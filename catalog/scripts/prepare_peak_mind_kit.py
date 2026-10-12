#!/usr/bin/env python3
"""Prepare and validate a local Peak Mind Spotify upload kit in two phases.

Discovery and cut selection are intentionally outside this script. The input Space URL
must already have been verified as a Peak Mind episode hosted by @McCarthy_JT. Prepare
creates a source-bound transcript checkpoint; resume requires explicit cleanup attestation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SPACE_RE = re.compile(r"^https://x\.com/i/spaces/([A-Za-z0-9]+)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KIT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
TIMING_RE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3}).*$"
)
REQUIRED_TOOLS = ("yt-dlp", "ffmpeg", "ffprobe", "whisper-cli")
RESUME_TOOLS = ("ffmpeg", "ffprobe")
MODEL = Path.home() / ".whisper-models" / "ggml-large-v3-turbo.bin"


class KitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


def run_command(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
    except FileNotFoundError as exc:
        raise KitError(f"Missing dependency: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise KitError(f"Command failed ({' '.join(args)}): {detail}") from exc


def require_dependencies(tools: tuple[str, ...] = REQUIRED_TOOLS) -> None:
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        raise KitError(f"Missing dependencies: {', '.join(missing)}")
    if "whisper-cli" in tools and not MODEL.is_file():
        raise KitError(f"Missing Whisper model: {MODEL}")


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KitError(f"Cannot read manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise KitError("Manifest must be a JSON object")

    required = {
        "schema_version",
        "date",
        "slug",
        "title",
        "speakers",
        "concise_description",
        "spotify_description",
        "cut_start_seconds",
        "cut_end_seconds",
        "edit_rationale",
        "selection_evidence",
        "ruled_out_candidates",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise KitError(f"Manifest is missing: {', '.join(missing)}")
    if data["schema_version"] != 1:
        raise KitError("Manifest schema_version must be 1")
    if not DATE_RE.fullmatch(str(data["date"])):
        raise KitError("Manifest date must be YYYY-MM-DD")
    try:
        datetime.strptime(data["date"], "%Y-%m-%d")
    except ValueError as exc:
        raise KitError(f"Invalid manifest date: {data['date']}") from exc
    if not SLUG_RE.fullmatch(str(data["slug"])):
        raise KitError("Manifest slug must contain lowercase ASCII words separated by hyphens")
    for field in ("title", "concise_description", "spotify_description", "edit_rationale"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise KitError(f"Manifest {field} must be a non-empty string")
    if not isinstance(data["speakers"], list) or not data["speakers"] or not all(
        isinstance(item, str) and item.strip() for item in data["speakers"]
    ):
        raise KitError("Manifest speakers must be a non-empty array of names")
    if not isinstance(data["selection_evidence"], list) or not data["selection_evidence"] or not all(
        isinstance(item, str) and item.strip() for item in data["selection_evidence"]
    ):
        raise KitError("Manifest selection_evidence must be a non-empty array of evidence strings")
    if not isinstance(data["ruled_out_candidates"], list):
        raise KitError("Manifest ruled_out_candidates must be an array")
    for candidate in data["ruled_out_candidates"]:
        if not isinstance(candidate, dict) or set(candidate) != {"space_url", "reason"}:
            raise KitError(
                "Manifest ruled_out_candidates entries must contain only space_url and reason"
            )
        if not isinstance(candidate["space_url"], str):
            raise KitError("Manifest ruled_out_candidates space_url values must be strings")
        canonical_space_url(candidate["space_url"])
        if not isinstance(candidate["reason"], str) or not candidate["reason"].strip():
            raise KitError("Manifest ruled_out_candidates reasons must be non-empty strings")
    for field in ("cut_start_seconds", "cut_end_seconds"):
        value = data[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise KitError(f"Manifest {field} must be a JSON number")
    try:
        start = float(data["cut_start_seconds"])
        end = float(data["cut_end_seconds"])
    except (OverflowError, TypeError, ValueError) as exc:
        raise KitError("Manifest cut timestamps must be numbers") from exc
    if not math.isfinite(start) or not math.isfinite(end):
        raise KitError("Manifest cut timestamps must be finite numbers")
    if start < 0 or end <= start:
        raise KitError("Manifest cut window must satisfy 0 <= start < end")
    data["cut_start_seconds"] = start
    data["cut_end_seconds"] = end
    return data


def canonical_space_url(url: str) -> tuple[str, str]:
    match = SPACE_RE.fullmatch(url)
    if not match:
        raise KitError("Space URL must be exactly https://x.com/i/spaces/<id>")
    space_id = match.group(1)
    return f"https://x.com/i/spaces/{space_id}", space_id


def resolve_space(url: str) -> dict[str, Any]:
    template = "%(.{id,title,upload_date,timestamp,uploader,uploader_id,webpage_url,ext,acodec})#j"
    result = run_command(
        ["yt-dlp", "--skip-download", "--no-warnings", "--print", template, url],
        capture=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise KitError("yt-dlp returned invalid metadata JSON") from exc


def probe_media(path: Path) -> dict[str, Any]:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=format_name,duration,size,bit_rate:stream=index,codec_name,codec_type,sample_rate,channels,channel_layout",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise KitError(f"ffprobe returned invalid JSON for {path}") from exc


def audio_stream(probe: dict[str, Any]) -> dict[str, Any]:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "audio":
            return stream
    raise KitError("No audio stream found")


def media_duration(probe: dict[str, Any]) -> float:
    try:
        return float(probe["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise KitError("ffprobe did not report a media duration") from exc


def download_source(url: str, destination: Path) -> None:
    run_command(["yt-dlp", "--no-warnings", "-o", str(destination), url])
    if not destination.is_file() or destination.stat().st_size == 0:
        raise KitError("yt-dlp completed without creating source audio")


def transcribe_source(source: Path, prefix: Path) -> int:
    wav = prefix.with_suffix(".wav")
    try:
        run_command(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(wav),
            ]
        )
        run_command(
            [
                "whisper-cli",
                "-m",
                str(MODEL),
                "-f",
                str(wav),
                "-ovtt",
                "-of",
                str(prefix),
                "--print-progress",
            ]
        )
    finally:
        wav.unlink(missing_ok=True)
    vtt = prefix.with_suffix(".vtt")
    if not vtt.is_file():
        raise KitError("Whisper did not create a VTT output")
    return len(parse_vtt(vtt.read_text(encoding="utf-8")))


def trim_audio(source: Path, destination: Path, start: float, end: float) -> None:
    duration = end - start
    run_command(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    )
    if not destination.is_file() or destination.stat().st_size == 0:
        raise KitError("ffmpeg completed without creating final audio")


def parse_time(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def format_time(value: float) -> str:
    millis = max(0, round(value * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


def parse_vtt(text: str) -> list[Cue]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n{2,}", normalized.strip())
    if not blocks or blocks[0].strip() != "WEBVTT":
        raise KitError("Transcript is not a WEBVTT file")
    cues: list[Cue] = []
    for block in blocks[1:]:
        lines = block.splitlines()
        timing_index = next((i for i, line in enumerate(lines) if TIMING_RE.match(line)), None)
        if timing_index is None:
            continue
        match = TIMING_RE.match(lines[timing_index])
        assert match is not None
        cue_text = "\n".join(lines[timing_index + 1 :]).strip()
        if cue_text:
            cues.append(
                Cue(
                    parse_time(match.group("start")),
                    parse_time(match.group("end")),
                    cue_text,
                )
            )
    if not cues:
        raise KitError("VTT transcript contains no cues")
    return cues


def clean_transcript(
    draft_vtt: Path, output_vtt: Path, output_txt: Path, start: float, end: float
) -> int:
    cues = parse_vtt(draft_vtt.read_text(encoding="utf-8"))
    kept: list[Cue] = []
    for cue in cues:
        if cue.end <= cue.start:
            raise KitError("Transcript cues must have positive duration")
        if cue.end <= start or cue.start >= end:
            continue
        if cue.start < start or cue.end > end:
            raise KitError(
                "A transcript cue straddles a cut boundary; restart preparation with a cut "
                "at a cue boundary rather than retaining speech outside the approved audio"
            )
        kept.append(Cue(cue.start - start, cue.end - start, cue.text))
    if not kept:
        raise KitError("No reviewed transcript cues remain inside the selected cut window")

    output_vtt.write_text(
        "WEBVTT\n\n"
        + "\n\n".join(
            f"{format_time(cue.start)} --> {format_time(cue.end)}\n{cue.text}" for cue in kept
        )
        + "\n",
        encoding="utf-8",
    )
    output_txt.write_text(
        "\n".join(" ".join(cue.text.split()) for cue in kept) + "\n",
        encoding="utf-8",
    )
    return len(kept)


def validate_reviewed_vtt(original_vtt: Path, reviewed_vtt: Path) -> None:
    original = parse_vtt(original_vtt.read_text(encoding="utf-8"))
    reviewed = parse_vtt(reviewed_vtt.read_text(encoding="utf-8"))
    original_index = 0
    for reviewed_cue in reviewed:
        while original_index < len(original) and original[original_index] != reviewed_cue:
            original_index += 1
        if original_index == len(original):
            raise KitError(
                "Reviewed draft may only delete whole Whisper cues; text, timestamps, and order "
                "must remain unchanged"
            )
        original_index += 1


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_duration(seconds: float) -> str:
    rounded = int(round(seconds))
    hours, remainder = divmod(rounded, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def tool_version(command: str) -> str:
    flag = "--version" if command != "ffmpeg" and command != "ffprobe" else "-version"
    result = run_command([command, flag], capture=True)
    return (result.stdout or result.stderr).splitlines()[0]


def aac_frame_duration(probe: dict[str, Any]) -> float:
    stream = audio_stream(probe)
    if stream.get("codec_name") != "aac":
        raise KitError(f"Audio codec is {stream.get('codec_name')!r}, expected AAC")
    try:
        sample_rate = float(stream["sample_rate"])
    except (KeyError, TypeError, ValueError) as exc:
        raise KitError("ffprobe did not report an audio sample rate") from exc
    if sample_rate <= 0:
        raise KitError("ffprobe reported an invalid audio sample rate")
    return 1024 / sample_rate


def validate_final_probe(probe: dict[str, Any], expected_duration: float) -> None:
    stream = audio_stream(probe)
    if stream.get("codec_name") != "aac":
        raise KitError(f"Final audio codec is {stream.get('codec_name')!r}, expected AAC")
    formats = set(str(probe.get("format", {}).get("format_name", "")).split(","))
    if not formats.intersection({"mov", "mp4", "m4a"}):
        raise KitError("Final audio is not an MP4/M4A container")
    actual = media_duration(probe)
    tolerance = aac_frame_duration(probe)
    if abs(actual - expected_duration) > tolerance:
        raise KitError(
            f"Final duration {actual:.3f}s differs from requested {expected_duration:.3f}s "
            f"by more than one AAC frame ({tolerance:.6f}s)"
        )


def write_upload_sheet(
    path: Path,
    manifest: dict[str, Any],
    url: str,
    space_id: str,
    filename: str,
    probe: dict[str, Any],
    audio_hash: str,
    transcript_method: str,
) -> None:
    stream = audio_stream(probe)
    duration = media_duration(probe)
    size = int(probe["format"]["size"])
    path.write_text(
        "PEAK MIND - Spotify for Creators upload sheet\n\n"
        f"TITLE: {manifest['title'].strip()}\n"
        f"DATE: {manifest['date']}\n"
        f"DURATION: {display_duration(duration)} ({duration:.3f} seconds)\n"
        f"CONCISE DESCRIPTION: {manifest['concise_description'].strip()}\n\n"
        "FULL SPOTIFY DESCRIPTION:\n"
        f"{manifest['spotify_description'].strip()}\n\n"
        f"SPEAKERS: {', '.join(item.strip() for item in manifest['speakers'])}\n"
        f"SOURCE SPACE URL: {url}\n"
        f"SOURCE SPACE ID: {space_id}\n"
        f"FILENAME: {filename}\n"
        f"CODEC: AAC in M4A/MP4 ({stream.get('sample_rate')} Hz, {stream.get('channels')} channels)\n"
        f"BYTE COUNT: {size}\n"
        f"SHA-256: {audio_hash}\n\n"
        "EXACT EDITS:\n"
        f"Kept source audio from {manifest['cut_start_seconds']:.3f}s through "
        f"{manifest['cut_end_seconds']:.3f}s using ffmpeg stream copy (no re-encoding).\n"
        f"Rationale: {manifest['edit_rationale'].strip()}\n"
        f"Transcript method: {transcript_method}.\n",
        encoding="utf-8",
    )


def workflow_roots(
    output_root: Path | None, checkpoint_root: Path | None
) -> tuple[Path, Path]:
    if output_root is None:
        output_root = Path.home() / "Downloads" / "peak-mind-spotify"
    output_root = output_root.expanduser().resolve()
    if checkpoint_root is None:
        checkpoint_root = output_root / ".checkpoints"
    checkpoint_root = checkpoint_root.expanduser()
    checkpoint_root = checkpoint_root.parent.resolve() / checkpoint_root.name
    if checkpoint_root.is_symlink():
        raise KitError(f"Checkpoint root must not be a symlink: {checkpoint_root}")
    return output_root, checkpoint_root


def validate_space_metadata(
    metadata: dict[str, Any], url: str, url_id: str, manifest: dict[str, Any]
) -> None:
    if metadata.get("id") != url_id:
        raise KitError(f"yt-dlp resolved Space id {metadata.get('id')!r}, expected {url_id}")
    if metadata.get("uploader_id") != "McCarthy_JT":
        raise KitError(
            f"Verified URL is hosted by @{metadata.get('uploader_id')}, not @McCarthy_JT; refusing"
        )
    if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
        raise KitError("yt-dlp did not report a Space title")
    if metadata.get("webpage_url") != url:
        raise KitError(
            f"yt-dlp webpage URL {metadata.get('webpage_url')!r} does not match {url}"
        )
    expected_upload_date = manifest["date"].replace("-", "")
    if metadata.get("upload_date") != expected_upload_date:
        raise KitError(
            f"yt-dlp upload date {metadata.get('upload_date')!r} does not match manifest date "
            f"{expected_upload_date}; resolve this evidence mismatch before preparing"
        )


def prepare(
    args: argparse.Namespace,
    *,
    output_root: Path | None = None,
    checkpoint_root: Path | None = None,
) -> Path:
    manifest = read_manifest(args.manifest.resolve())
    url, url_id = canonical_space_url(args.space_url)
    output_root, checkpoint_root = workflow_roots(output_root, checkpoint_root)
    base = f"{manifest['date']}-{manifest['slug']}"
    final_dir = output_root / base
    checkpoint_dir = checkpoint_root / base

    if final_dir.exists():
        raise KitError(
            f"Refusing to overwrite existing kit: {final_dir}. "
            "Choose a new slug or explicitly move the existing kit after reviewing it."
        )
    if checkpoint_dir.exists():
        raise KitError(f"Refusing to overwrite existing checkpoint: {checkpoint_dir}")

    require_dependencies()
    checkpoint_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if checkpoint_root.is_symlink():
        raise KitError(f"Checkpoint root must not be a symlink: {checkpoint_root}")
    checkpoint_root.chmod(0o700)
    stage = Path(tempfile.mkdtemp(prefix=f".{base}.work-", dir=checkpoint_root))
    try:
        metadata = resolve_space(url)
        validate_space_metadata(metadata, url, url_id, manifest)

        source = stage / "source.m4a"
        download_source(url, source)

        source_probe = probe_media(source)
        source_duration = media_duration(source_probe)
        cut_start = manifest["cut_start_seconds"]
        cut_end = manifest["cut_end_seconds"]
        source_tolerance = aac_frame_duration(source_probe)
        if cut_end > source_duration + source_tolerance:
            raise KitError(
                f"Cut end {cut_end:.3f}s exceeds source duration {source_duration:.3f}s "
                f"by more than one AAC frame ({source_tolerance:.6f}s)"
            )

        draft_prefix = stage / "draft"
        cue_count = transcribe_source(source, draft_prefix)
        draft_vtt = draft_prefix.with_suffix(".vtt")
        original_vtt = stage / "draft.original.vtt"
        shutil.copy2(draft_vtt, original_vtt)
        manifest_path = stage / "MANIFEST.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        source_hash = sha256(source)
        checkpoint = {
            "schema_version": 1,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "base": base,
            "manifest_sha256": sha256(manifest_path),
            "source": {
                "filename": source.name,
                "space_url": url,
                "space_id": url_id,
                "sha256": source_hash,
                "byte_count": source.stat().st_size,
                "duration_seconds": source_duration,
                "probe": source_probe,
                "yt_dlp": metadata,
            },
            "draft": {
                "filename": draft_vtt.name,
                "original_filename": original_vtt.name,
                "generated_from_source_sha256": source_hash,
                "original_sha256": sha256(original_vtt),
                "cues": cue_count,
            },
            "tools": {tool: tool_version(tool) for tool in REQUIRED_TOOLS},
            "whisper_model": str(MODEL),
        }
        (stage / "CHECKPOINT.json").write_text(
            json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        resume_command = (
            "python3 catalog/scripts/prepare_peak_mind_kit.py resume "
            f"{shlex.quote(str(checkpoint_dir))} --attest-cleanup"
        )
        (stage / "NEXT-STEPS.txt").write_text(
            "1. Listen to source.m4a while reviewing draft.vtt. Remove only demonstrated "
            "Whisper hallucination cues as whole cues; do not edit draft.original.vtt, rewrite speech, "
            "reorder cues, or alter timestamps.\n"
            "2. Confirm neither approved cut boundary crosses a retained cue. If one does, "
            "delete this checkpoint and rerun prepare with corrected manifest timestamps.\n"
            "3. After completing that review, run exactly:\n"
            f"{resume_command}\n"
            "The --attest-cleanup flag records that the operator reviewed the audio and VTT.\n",
            encoding="utf-8",
        )
        stage.rename(checkpoint_dir)
        return checkpoint_dir
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def read_checkpoint(
    checkpoint_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path, dict[str, Any]]:
    required = {
        "CHECKPOINT.json",
        "MANIFEST.json",
        "source.m4a",
        "draft.vtt",
        "draft.original.vtt",
    }
    missing = sorted(name for name in required if not (checkpoint_dir / name).is_file())
    if missing:
        raise KitError(f"Checkpoint is missing: {', '.join(missing)}")
    try:
        checkpoint = json.loads((checkpoint_dir / "CHECKPOINT.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KitError(f"Invalid CHECKPOINT.json: {exc}") from exc
    if not isinstance(checkpoint, dict):
        raise KitError("CHECKPOINT.json must contain an object")
    if checkpoint.get("schema_version") != 1:
        raise KitError("Checkpoint schema_version must be 1")
    if not isinstance(checkpoint.get("tools"), dict):
        raise KitError("Checkpoint tools record is invalid")

    manifest_path = checkpoint_dir / "MANIFEST.json"
    if sha256(manifest_path) != checkpoint.get("manifest_sha256"):
        raise KitError("Checkpoint manifest hash does not match")
    manifest = read_manifest(manifest_path)
    base = f"{manifest['date']}-{manifest['slug']}"
    if checkpoint.get("base") != base or checkpoint_dir.name != base:
        raise KitError("Checkpoint identity does not match its manifest and directory")

    source_record = checkpoint.get("source")
    if not isinstance(source_record, dict) or source_record.get("filename") != "source.m4a":
        raise KitError("Checkpoint source record is invalid")
    url, url_id = canonical_space_url(str(source_record.get("space_url", "")))
    if source_record.get("space_id") != url_id:
        raise KitError("Checkpoint Space URL and id do not match")
    metadata = source_record.get("yt_dlp")
    if not isinstance(metadata, dict):
        raise KitError("Checkpoint yt-dlp metadata is invalid")
    validate_space_metadata(metadata, url, url_id, manifest)
    source = checkpoint_dir / "source.m4a"
    source_hash = sha256(source)
    if source_hash != source_record.get("sha256"):
        raise KitError("Checkpoint source audio hash does not match")
    if source.stat().st_size != source_record.get("byte_count"):
        raise KitError("Checkpoint source audio byte count does not match")

    draft_record = checkpoint.get("draft")
    if not isinstance(draft_record, dict) or draft_record.get("filename") != "draft.vtt":
        raise KitError("Checkpoint draft record is invalid")
    if draft_record.get("original_filename") != "draft.original.vtt":
        raise KitError("Checkpoint original draft filename is invalid")
    if draft_record.get("generated_from_source_sha256") != source_hash:
        raise KitError("Checkpoint draft provenance does not match its source audio")
    draft_vtt = checkpoint_dir / "draft.vtt"
    original_vtt = checkpoint_dir / "draft.original.vtt"
    if sha256(original_vtt) != draft_record.get("original_sha256"):
        raise KitError("Checkpoint original draft hash does not match")
    validate_reviewed_vtt(original_vtt, draft_vtt)

    source_probe = probe_media(source)
    source_duration = media_duration(source_probe)
    tolerance = aac_frame_duration(source_probe)
    try:
        recorded_duration = float(source_record["duration_seconds"])
    except (KeyError, TypeError, ValueError) as exc:
        raise KitError("Checkpoint source duration is invalid") from exc
    if abs(source_duration - recorded_duration) > tolerance:
        raise KitError("Checkpoint source duration does not match")
    if manifest["cut_end_seconds"] > source_duration + tolerance:
        raise KitError("Manifest cut end exceeds checkpoint source duration")
    return checkpoint, manifest, source, draft_vtt, source_probe


def resume(
    args: argparse.Namespace,
    *,
    output_root: Path | None = None,
    checkpoint_root: Path | None = None,
) -> Path:
    if not args.attest_cleanup:
        raise KitError("Resume requires --attest-cleanup after audio/VTT review")
    output_root, checkpoint_root = workflow_roots(output_root, checkpoint_root)
    checkpoint_dir = args.checkpoint.expanduser().resolve()
    if checkpoint_dir.parent != checkpoint_root:
        raise KitError(f"Checkpoint must be directly inside {checkpoint_root}")
    if not KIT_RE.fullmatch(checkpoint_dir.name):
        raise KitError("Checkpoint directory name must be <YYYY-MM-DD>-<slug>")
    final_dir = output_root / checkpoint_dir.name

    if not checkpoint_dir.is_dir():
        if final_dir.is_dir():
            validate_kit(final_dir)
            return final_dir
        raise KitError(f"Checkpoint directory does not exist: {checkpoint_dir}")

    require_dependencies(RESUME_TOOLS)
    checkpoint, manifest, source, draft_vtt, source_probe = read_checkpoint(checkpoint_dir)
    if final_dir.exists():
        final_manifest, final_source = validate_kit(final_dir, check_dependencies=False)
        checkpoint_source = checkpoint["source"]
        if final_manifest != manifest or any(
            final_source.get(field) != checkpoint_source.get(field)
            for field in ("space_url", "space_id", "sha256")
        ):
            raise KitError("Existing final kit does not match checkpoint provenance")
        shutil.rmtree(checkpoint_dir)
        return final_dir
    output_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{checkpoint_dir.name}.work-", dir=output_root))
    try:
        base = checkpoint_dir.name
        audio_name = f"{base}.m4a"
        final_audio = stage / audio_name
        final_vtt = stage / f"{base}.vtt"
        final_txt = stage / f"{base}.txt"
        cut_start = manifest["cut_start_seconds"]
        cut_end = manifest["cut_end_seconds"]
        cue_count = clean_transcript(draft_vtt, final_vtt, final_txt, cut_start, cut_end)
        trim_audio(source, final_audio, cut_start, cut_end)
        final_probe = probe_media(final_audio)
        validate_final_probe(final_probe, cut_end - cut_start)

        url = checkpoint["source"]["space_url"]
        url_id = checkpoint["source"]["space_id"]
        audio_hash = sha256(final_audio)
        transcript_method = (
            "operator-reviewed the source-bound Whisper VTT for demonstrated hallucinations, "
            "shifted wholly retained cues, and derived TXT from cleaned VTT"
        )
        evidence = {
            "schema_version": 1,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": {
                "space_url": url,
                "space_id": url_id,
                "yt_dlp": checkpoint["source"]["yt_dlp"],
                "duration_seconds": media_duration(source_probe),
                "byte_count": source.stat().st_size,
                "sha256": checkpoint["source"]["sha256"],
                "probe": source_probe,
            },
            "selection_evidence": manifest["selection_evidence"],
            "ruled_out_candidates": manifest["ruled_out_candidates"],
            "transcript_cleanup": {
                "attested": True,
                "cleaned_vtt_sha256": sha256(draft_vtt),
                "original_draft_vtt_sha256": checkpoint["draft"]["original_sha256"],
            },
            "edit": {
                "start_seconds": cut_start,
                "end_seconds": cut_end,
                "rationale": manifest["edit_rationale"].strip(),
                "method": "ffmpeg input seek and stream copy; no audio re-encoding",
            },
            "final": {
                "filename": audio_name,
                "duration_seconds": media_duration(final_probe),
                "byte_count": int(final_probe["format"]["size"]),
                "sha256": audio_hash,
                "probe": final_probe,
                "transcript_cues": cue_count,
                "transcript_method": transcript_method,
            },
            "tools": {
                **checkpoint.get("tools", {}),
                **{tool: tool_version(tool) for tool in RESUME_TOOLS},
            },
            "whisper_model": checkpoint.get("whisper_model"),
        }
        (stage / "SOURCE-EVIDENCE.json").write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (stage / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        write_upload_sheet(
            stage / "UPLOAD.txt",
            manifest,
            url,
            url_id,
            audio_name,
            final_probe,
            audio_hash,
            transcript_method,
        )
        checksum_files = sorted(
            path for path in stage.iterdir() if path.is_file() and path.name != "SHA256SUMS"
        )
        (stage / "SHA256SUMS").write_text(
            "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_files),
            encoding="utf-8",
        )
        validate_kit(stage, check_dependencies=False, expected_name=base)
        stage.rename(final_dir)
        shutil.rmtree(checkpoint_dir)
        return final_dir
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def validate_kit(
    kit_dir: Path,
    *,
    check_dependencies: bool = True,
    expected_name: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    kit_dir = kit_dir.expanduser().resolve()
    if not kit_dir.is_dir():
        raise KitError(f"Kit directory does not exist: {kit_dir}")
    if check_dependencies:
        require_dependencies(RESUME_TOOLS)
    required_names = {"MANIFEST.json", "SOURCE-EVIDENCE.json", "UPLOAD.txt", "SHA256SUMS"}
    names = {path.name for path in kit_dir.iterdir() if path.is_file()}
    missing = sorted(required_names - names)
    if missing:
        raise KitError(f"Kit is missing: {', '.join(missing)}")

    try:
        evidence = json.loads((kit_dir / "SOURCE-EVIDENCE.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KitError(f"Invalid SOURCE-EVIDENCE.json: {exc}") from exc
    if not isinstance(evidence, dict):
        raise KitError("SOURCE-EVIDENCE.json must contain an object")
    manifest = read_manifest(kit_dir / "MANIFEST.json")
    manifest_base = f"{manifest['date']}-{manifest['slug']}"
    if (expected_name or kit_dir.name) != manifest_base:
        raise KitError("Kit directory name does not match MANIFEST.json date and slug")
    if evidence.get("selection_evidence") != manifest["selection_evidence"]:
        raise KitError("Selection evidence does not match MANIFEST.json")
    if evidence.get("ruled_out_candidates") != manifest["ruled_out_candidates"]:
        raise KitError("Ruled-out candidates do not match MANIFEST.json")
    cleanup = evidence.get("transcript_cleanup")
    if not isinstance(cleanup, dict) or cleanup.get("attested") is not True:
        raise KitError("SOURCE-EVIDENCE.json lacks transcript cleanup attestation")
    source_record = evidence.get("source")
    if not isinstance(source_record, dict):
        raise KitError("SOURCE-EVIDENCE.json lacks source evidence")
    source_url, source_id = canonical_space_url(str(source_record.get("space_url", "")))
    if source_record.get("space_id") != source_id:
        raise KitError("SOURCE-EVIDENCE.json Space URL and id do not match")
    metadata = source_record.get("yt_dlp")
    if not isinstance(metadata, dict):
        raise KitError("SOURCE-EVIDENCE.json yt-dlp metadata is invalid")
    validate_space_metadata(metadata, source_url, source_id, manifest)
    edit = evidence.get("edit")
    if not isinstance(edit, dict) or edit.get("start_seconds") != manifest["cut_start_seconds"]:
        raise KitError("SOURCE-EVIDENCE.json edit start does not match MANIFEST.json")
    if edit.get("end_seconds") != manifest["cut_end_seconds"]:
        raise KitError("SOURCE-EVIDENCE.json edit end does not match MANIFEST.json")
    final_record = evidence.get("final")
    if not isinstance(final_record, dict):
        raise KitError("SOURCE-EVIDENCE.json lacks final evidence")
    filename = final_record.get("filename")
    if not filename:
        raise KitError("SOURCE-EVIDENCE.json lacks final.filename")
    if filename != f"{manifest_base}.m4a":
        raise KitError("SOURCE-EVIDENCE.json final.filename does not match kit identity")
    if "duration_seconds" not in final_record:
        raise KitError("SOURCE-EVIDENCE.json lacks final.duration_seconds")
    recorded_duration = final_record["duration_seconds"]
    if (
        isinstance(recorded_duration, bool)
        or not isinstance(recorded_duration, (int, float))
        or not math.isfinite(recorded_duration)
        or recorded_duration <= 0
    ):
        raise KitError(
            "SOURCE-EVIDENCE.json final.duration_seconds must be a positive finite JSON number"
        )
    if "byte_count" not in final_record:
        raise KitError("SOURCE-EVIDENCE.json lacks final.byte_count")
    recorded_byte_count = final_record["byte_count"]
    if (
        isinstance(recorded_byte_count, bool)
        or not isinstance(recorded_byte_count, int)
        or recorded_byte_count <= 0
    ):
        raise KitError("SOURCE-EVIDENCE.json final.byte_count must be a positive JSON integer")
    if "sha256" not in final_record:
        raise KitError("SOURCE-EVIDENCE.json lacks final.sha256")
    recorded_sha256 = final_record["sha256"]
    if not isinstance(recorded_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded_sha256):
        raise KitError("SOURCE-EVIDENCE.json final.sha256 must be a lowercase SHA-256 digest")
    base = manifest_base
    audio = kit_dir / filename
    txt = kit_dir / f"{base}.txt"
    vtt = kit_dir / f"{base}.vtt"
    for path in (audio, txt, vtt):
        if not path.is_file() or path.stat().st_size == 0:
            raise KitError(f"Missing or empty kit output: {path.name}")

    probe = probe_media(audio)
    requested_duration = manifest["cut_end_seconds"] - manifest["cut_start_seconds"]
    validate_final_probe(probe, requested_duration)
    if media_duration(probe) != float(recorded_duration):
        raise KitError("Audio duration does not match SOURCE-EVIDENCE.json")
    if int(probe["format"]["size"]) != recorded_byte_count:
        raise KitError("Audio byte count does not match SOURCE-EVIDENCE.json")
    if sha256(audio) != recorded_sha256:
        raise KitError("Audio SHA-256 does not match SOURCE-EVIDENCE.json")
    run_command(
        [
            "ffmpeg",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(audio),
            "-f",
            "null",
            os.devnull,
        ],
        capture=True,
    )

    cues = parse_vtt(vtt.read_text(encoding="utf-8"))
    duration = media_duration(probe)
    if max(cue.end for cue in cues) > duration + aac_frame_duration(probe):
        raise KitError("Final VTT extends beyond final audio")
    expected_txt = "\n".join(" ".join(cue.text.split()) for cue in cues) + "\n"
    if txt.read_text(encoding="utf-8") != expected_txt:
        raise KitError("Final TXT transcript is not derived from the final VTT")

    checksum_path = kit_dir / "SHA256SUMS"
    checked_names: set[str] = set()
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/]+)", line)
        if not match:
            raise KitError(f"Malformed checksum line: {line!r}")
        expected, name = match.groups()
        if name in checked_names:
            raise KitError(f"Duplicate checksum entry: {name}")
        target = kit_dir / name
        if not target.is_file() or sha256(target) != expected:
            raise KitError(f"Checksum failed: {name}")
        checked_names.add(name)
    expected_names = names - {"SHA256SUMS"}
    if checked_names != expected_names:
        raise KitError("SHA256SUMS must cover every kit file except itself exactly once")

    sheet = (kit_dir / "UPLOAD.txt").read_text(encoding="utf-8")
    for label in (
        "TITLE:",
        "DATE:",
        "DURATION:",
        "CONCISE DESCRIPTION:",
        "FULL SPOTIFY DESCRIPTION:",
        "SPEAKERS:",
        "SOURCE SPACE URL:",
        "SOURCE SPACE ID:",
        "FILENAME:",
        "EXACT EDITS:",
    ):
        if label not in sheet:
            raise KitError(f"UPLOAD.txt lacks {label}")
    return manifest, source_record


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="create a review checkpoint")
    prepare_parser.add_argument("space_url", help="verified canonical X Space URL")
    prepare_parser.add_argument("--manifest", required=True, type=Path, help="editor-approved JSON manifest")

    resume_parser = subparsers.add_parser("resume", help="build a kit from a reviewed checkpoint")
    resume_parser.add_argument("checkpoint", type=Path)
    resume_parser.add_argument(
        "--attest-cleanup",
        action="store_true",
        required=True,
        help="attest that draft.vtt was reviewed against source.m4a",
    )

    validate_parser = subparsers.add_parser("validate", help="validate an existing upload kit")
    validate_parser.add_argument("kit_dir", type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args)
            print(f"Draft checkpoint ready: {result}")
            print((result / "NEXT-STEPS.txt").read_text(encoding="utf-8"), end="")
        elif args.command == "resume":
            result = resume(args)
            print(f"Prepared and validated: {result}")
        else:
            validate_kit(args.kit_dir)
            print(f"Valid upload kit: {args.kit_dir.expanduser().resolve()}")
        return 0
    except KitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
