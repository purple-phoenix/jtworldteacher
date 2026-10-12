#!/usr/bin/env python3
"""Prepare and validate a local Peak Mind Spotify upload kit.

Discovery and cut selection are intentionally outside this script. The input Space URL
must already have been verified as a Peak Mind episode hosted by @McCarthy_JT.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SPACE_RE = re.compile(r"^https://(?:x|twitter)\.com/i/spaces/([A-Za-z0-9]+)(?:[/?#].*)?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TIMING_RE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3})(?P<settings>.*)$"
)
REQUIRED_TOOLS = ("yt-dlp", "ffmpeg", "ffprobe", "whisper-cli")
MODEL = Path.home() / ".whisper-models" / "ggml-large-v3-turbo.bin"


class KitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str
    settings: str = ""


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


def require_dependencies(needs_whisper: bool) -> None:
    tools = REQUIRED_TOOLS if needs_whisper else REQUIRED_TOOLS[:3]
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        raise KitError(f"Missing dependencies: {', '.join(missing)}")
    if needs_whisper and not MODEL.is_file():
        raise KitError(f"Missing Whisper model: {MODEL}")


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KitError(f"Cannot read manifest {path}: {exc}") from exc

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
    try:
        start = float(data["cut_start_seconds"])
        end = float(data["cut_end_seconds"])
    except (TypeError, ValueError) as exc:
        raise KitError("Manifest cut timestamps must be numbers") from exc
    if start < 0 or end <= start:
        raise KitError("Manifest cut window must satisfy 0 <= start < end")
    data["cut_start_seconds"] = start
    data["cut_end_seconds"] = end
    return data


def canonical_space_url(url: str) -> tuple[str, str]:
    match = SPACE_RE.fullmatch(url)
    if not match:
        raise KitError("Space URL must look like https://x.com/i/spaces/<id>")
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


def transcribe_source(source: Path, prefix: Path) -> None:
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
                "-otxt",
                "-ovtt",
                "-of",
                str(prefix),
                "--print-progress",
            ]
        )
    finally:
        wav.unlink(missing_ok=True)
    if not prefix.with_suffix(".txt").is_file() or not prefix.with_suffix(".vtt").is_file():
        raise KitError("Whisper did not create both TXT and VTT outputs")


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
                    match.group("settings"),
                )
            )
    if not cues:
        raise KitError("VTT transcript contains no cues")
    return cues


def clean_transcript(raw_vtt: Path, output_vtt: Path, output_txt: Path, start: float, end: float) -> int:
    cues = parse_vtt(raw_vtt.read_text(encoding="utf-8"))
    kept: list[Cue] = []
    for cue in cues:
        if cue.end <= start or cue.start >= end:
            continue
        overlap_start = max(cue.start, start)
        overlap_end = min(cue.end, end)
        if cue.start < start - 0.25 or cue.end > end + 0.25:
            raise KitError(
                "A transcript cue straddles a cut boundary; choose a pause/cue boundary "
                "or manually produce aligned transcripts rather than silently retaining cut speech"
            )
        kept.append(Cue(overlap_start - start, overlap_end - start, cue.text, cue.settings))
    if not kept:
        raise KitError("No transcript cues remain inside the selected cut window")

    vtt_parts = ["WEBVTT\n"]
    txt_lines: list[str] = []
    for cue in kept:
        vtt_parts.append(
            f"{format_time(cue.start)} --> {format_time(cue.end)}{cue.settings}\n{cue.text}\n"
        )
        txt_lines.append(" ".join(cue.text.split()))
    output_vtt.write_text("\n".join(vtt_parts), encoding="utf-8")
    output_txt.write_text("\n".join(txt_lines) + "\n", encoding="utf-8")
    return len(kept)


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


def validate_final_probe(probe: dict[str, Any], expected_duration: float) -> None:
    stream = audio_stream(probe)
    if stream.get("codec_name") != "aac":
        raise KitError(f"Final audio codec is {stream.get('codec_name')!r}, expected AAC")
    formats = set(str(probe.get("format", {}).get("format_name", "")).split(","))
    if not formats.intersection({"mov", "mp4", "m4a"}):
        raise KitError("Final audio is not an MP4/M4A container")
    actual = media_duration(probe)
    if abs(actual - expected_duration) > 1.0:
        raise KitError(
            f"Final duration {actual:.3f}s differs from requested {expected_duration:.3f}s by more than 1s"
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


def prepare(args: argparse.Namespace) -> Path:
    manifest = read_manifest(args.manifest.resolve())
    url, url_id = canonical_space_url(args.space_url)
    output_root = args.output_root.expanduser().resolve()
    base = f"{manifest['date']}-{manifest['slug']}"
    final_dir = output_root / base

    # Refuse before running tools or creating a staging directory.
    if final_dir.exists():
        raise KitError(
            f"Refusing to overwrite existing kit: {final_dir}. "
            "Choose a new slug or explicitly move the existing kit after reviewing it."
        )

    needs_whisper = args.transcript_prefix is None
    require_dependencies(needs_whisper)
    output_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{base}.work-", dir=output_root))
    try:
        metadata = resolve_space(url)
        if metadata.get("id") != url_id:
            raise KitError(f"yt-dlp resolved Space id {metadata.get('id')!r}, expected {url_id}")
        if metadata.get("uploader_id") != "McCarthy_JT":
            raise KitError(
                f"Verified URL is hosted by @{metadata.get('uploader_id')}, not @McCarthy_JT; refusing"
            )
        expected_upload_date = manifest["date"].replace("-", "")
        if metadata.get("upload_date") != expected_upload_date:
            raise KitError(
                f"yt-dlp upload date {metadata.get('upload_date')!r} does not match manifest date "
                f"{expected_upload_date}; resolve this evidence mismatch before preparing"
            )

        source = stage / "source.m4a"
        if args.source_file:
            source_input = args.source_file.expanduser().resolve()
            if not source_input.is_file():
                raise KitError(f"Source file does not exist: {source_input}")
            shutil.copy2(source_input, source)
        else:
            download_source(url, source)

        source_probe = probe_media(source)
        source_duration = media_duration(source_probe)
        cut_start = manifest["cut_start_seconds"]
        cut_end = manifest["cut_end_seconds"]
        if cut_end > source_duration + 0.25:
            raise KitError(
                f"Cut end {cut_end:.3f}s exceeds source duration {source_duration:.3f}s"
            )

        raw_vtt = None
        if args.transcript_prefix:
            prefix = args.transcript_prefix.expanduser().resolve()
            raw_txt = prefix.with_suffix(".txt")
            raw_vtt = prefix.with_suffix(".vtt")
            if not raw_txt.is_file() or not raw_vtt.is_file():
                raise KitError(f"Transcript prefix must have both {raw_txt.name} and {raw_vtt.name}")

        audio_name = f"{base}.m4a"
        txt_name = f"{base}.txt"
        vtt_name = f"{base}.vtt"
        final_audio = stage / audio_name
        final_txt = stage / txt_name
        final_vtt = stage / vtt_name
        trim_audio(source, final_audio, cut_start, cut_end)
        if raw_vtt is None:
            transcribe_source(final_audio, final_audio.with_suffix(""))
            cue_count = len(parse_vtt(final_vtt.read_text(encoding="utf-8")))
            transcript_method = (
                "converted the edited M4A to mono 16 kHz PCM WAV, transcribed it with "
                "whisper.cpp large-v3-turbo, and retained the resulting edited-audio timestamps"
            )
        else:
            cue_count = clean_transcript(raw_vtt, final_vtt, final_txt, cut_start, cut_end)
            transcript_method = (
                "removed raw-source cues outside the approved cut window and shifted retained "
                "VTT cues to the edited-audio timeline"
            )

        final_probe = probe_media(final_audio)
        validate_final_probe(final_probe, cut_end - cut_start)
        # Decode every packet; malformed/truncated output must fail before the kit is published locally.
        run_command(
            ["ffmpeg", "-v", "error", "-i", str(final_audio), "-f", "null", os.devnull],
            capture=True,
        )

        audio_hash = sha256(final_audio)
        evidence = {
            "schema_version": 1,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": {
                "space_url": url,
                "space_id": url_id,
                "yt_dlp": metadata,
                "duration_seconds": source_duration,
                "probe": source_probe,
            },
            "selection_evidence": manifest.get("selection_evidence", []),
            "ruled_out_candidates": manifest.get("ruled_out_candidates", []),
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
                tool: tool_version(tool)
                for tool in (REQUIRED_TOOLS if needs_whisper else REQUIRED_TOOLS[:3])
            },
            "whisper_model": str(MODEL) if needs_whisper else None,
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

        # Source and raw Whisper files are working data, not upload-kit deliverables.
        for path in (source, stage / "source.txt", stage / "source.vtt"):
            path.unlink(missing_ok=True)

        checksum_files = sorted(
            path for path in stage.iterdir() if path.is_file() and path.name != "SHA256SUMS"
        )
        (stage / "SHA256SUMS").write_text(
            "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_files),
            encoding="utf-8",
        )
        validate_kit(stage, check_dependencies=False)
        stage.rename(final_dir)
        return final_dir
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def validate_kit(kit_dir: Path, *, check_dependencies: bool = True) -> None:
    kit_dir = kit_dir.expanduser().resolve()
    if not kit_dir.is_dir():
        raise KitError(f"Kit directory does not exist: {kit_dir}")
    if check_dependencies and shutil.which("ffprobe") is None:
        raise KitError("Missing dependency: ffprobe")
    required_names = {"MANIFEST.json", "SOURCE-EVIDENCE.json", "UPLOAD.txt", "SHA256SUMS"}
    names = {path.name for path in kit_dir.iterdir() if path.is_file()}
    missing = sorted(required_names - names)
    if missing:
        raise KitError(f"Kit is missing: {', '.join(missing)}")

    try:
        evidence = json.loads((kit_dir / "SOURCE-EVIDENCE.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KitError(f"Invalid SOURCE-EVIDENCE.json: {exc}") from exc
    filename = evidence.get("final", {}).get("filename")
    if not filename:
        raise KitError("SOURCE-EVIDENCE.json lacks final.filename")
    if Path(filename).name != filename or not filename.endswith(".m4a"):
        raise KitError("SOURCE-EVIDENCE.json final.filename must be a plain .m4a filename")
    base = Path(filename).stem
    audio = kit_dir / filename
    txt = kit_dir / f"{base}.txt"
    vtt = kit_dir / f"{base}.vtt"
    for path in (audio, txt, vtt):
        if not path.is_file() or path.stat().st_size == 0:
            raise KitError(f"Missing or empty kit output: {path.name}")

    probe = probe_media(audio)
    validate_final_probe(probe, float(evidence["final"]["duration_seconds"]))
    if int(probe["format"]["size"]) != int(evidence["final"]["byte_count"]):
        raise KitError("Audio byte count does not match SOURCE-EVIDENCE.json")
    if sha256(audio) != evidence["final"]["sha256"]:
        raise KitError("Audio SHA-256 does not match SOURCE-EVIDENCE.json")

    cues = parse_vtt(vtt.read_text(encoding="utf-8"))
    duration = media_duration(probe)
    if cues[-1].end > duration + 0.5:
        raise KitError("Final VTT extends beyond final audio")
    if not txt.read_text(encoding="utf-8").strip():
        raise KitError("Final TXT transcript is empty")

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


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="prepare a new upload kit")
    prepare_parser.add_argument("space_url", help="verified canonical X Space URL")
    prepare_parser.add_argument("--manifest", required=True, type=Path, help="editor-approved JSON manifest")
    prepare_parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.home() / "Downloads" / "peak-mind-spotify",
        help="parent directory for the date-slug kit",
    )
    prepare_parser.add_argument(
        "--source-file", type=Path, help="reuse an already downloaded source while still verifying its URL"
    )
    prepare_parser.add_argument(
        "--transcript-prefix",
        type=Path,
        help="reuse raw Whisper PREFIX.txt and PREFIX.vtt made from the uncut source",
    )

    validate_parser = subparsers.add_parser("validate", help="validate an existing upload kit")
    validate_parser.add_argument("kit_dir", type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args)
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
