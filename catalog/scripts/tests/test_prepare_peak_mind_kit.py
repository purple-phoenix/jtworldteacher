#!/usr/bin/env python3

import argparse
import contextlib
import importlib.util
import io
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "prepare_peak_mind_kit.py"
SPEC = importlib.util.spec_from_file_location("prepare_peak_mind_kit", SCRIPT)
assert SPEC and SPEC.loader
kit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = kit
SPEC.loader.exec_module(kit)


class InputValidationTests(unittest.TestCase):
    def manifest_data(self) -> dict:
        return {
            "schema_version": 1,
            "date": "2026-10-07",
            "slug": "proof-of-work",
            "title": "Proof of Work",
            "speakers": ["JT", "Matt McCarthy"],
            "concise_description": "A transcript-grounded description.",
            "spotify_description": "A longer transcript-grounded description.",
            "cut_start_seconds": 10.0,
            "cut_end_seconds": 16.0,
            "edit_rationale": "Removed demonstrated hold music and dead air only.",
            "selection_evidence": ["The recording identifies the Wednesday Peak Mind show."],
            "ruled_out_candidates": [],
        }

    def read_manifest(self, root: Path, data: dict):
        path = root / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return kit.read_manifest(path)

    def test_manifest_requires_nonempty_selection_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for evidence in (None, [], [" "]):
                data = self.manifest_data()
                if evidence is None:
                    del data["selection_evidence"]
                else:
                    data["selection_evidence"] = evidence
                with self.subTest(evidence=evidence):
                    with self.assertRaisesRegex(kit.KitError, "selection_evidence"):
                        self.read_manifest(root, data)

    def test_manifest_requires_explicit_valid_ruled_out_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = (
                None,
                "not-an-array",
                [{"space_url": 123, "reason": "BoomRoom"}],
                [{"space_url": "https://twitter.com/i/spaces/Other", "reason": "BoomRoom"}],
                [{"space_url": "https://x.com/i/spaces/Other", "reason": ""}],
            )
            for candidates in cases:
                data = self.manifest_data()
                if candidates is None:
                    del data["ruled_out_candidates"]
                else:
                    data["ruled_out_candidates"] = candidates
                with self.subTest(candidates=candidates):
                    with self.assertRaises(kit.KitError):
                        self.read_manifest(root, data)

    def test_prepare_rejects_nonfinite_cut_timestamps_before_work(self):
        cases = (
            ("cut_start_seconds", float("nan")),
            ("cut_start_seconds", float("inf")),
            ("cut_start_seconds", float("-inf")),
            ("cut_end_seconds", float("nan")),
            ("cut_end_seconds", float("inf")),
            ("cut_end_seconds", float("-inf")),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for field, value in cases:
                data = self.manifest_data()
                data[field] = value
                path = root / f"{field}-{repr(value)}.json"
                path.write_text(json.dumps(data), encoding="utf-8")
                with (
                    self.subTest(field=field, value=value),
                    mock.patch.object(kit, "require_dependencies") as dependencies,
                    mock.patch.object(kit, "resolve_space") as resolve_space,
                ):
                    with self.assertRaisesRegex(kit.KitError, "finite"):
                        kit.prepare(
                            argparse.Namespace(
                                space_url="https://x.com/i/spaces/1Example",
                                manifest=path,
                            ),
                            output_root=root / "output",
                            checkpoint_root=root / "checkpoints",
                        )
                    dependencies.assert_not_called()
                    resolve_space.assert_not_called()
            self.assertFalse((root / "output").exists())
            self.assertFalse((root / "checkpoints").exists())

    def test_prepare_rejects_boolean_and_string_cut_timestamps_before_work(self):
        cases = (
            ("cut_start_seconds", True),
            ("cut_start_seconds", "10.0"),
            ("cut_end_seconds", False),
            ("cut_end_seconds", "16.0"),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (field, value) in enumerate(cases):
                data = self.manifest_data()
                data[field] = value
                path = root / f"invalid-cut-{index}.json"
                path.write_text(json.dumps(data), encoding="utf-8")
                with (
                    self.subTest(field=field, value=value),
                    mock.patch.object(kit, "require_dependencies") as dependencies,
                    mock.patch.object(kit, "resolve_space") as resolve_space,
                ):
                    with self.assertRaisesRegex(kit.KitError, f"{field} must be a JSON number"):
                        kit.prepare(
                            argparse.Namespace(
                                space_url="https://x.com/i/spaces/1Example",
                                manifest=path,
                            ),
                            output_root=root / "output",
                            checkpoint_root=root / "checkpoints",
                        )
                    dependencies.assert_not_called()
                    resolve_space.assert_not_called()
            self.assertFalse((root / "output").exists())
            self.assertFalse((root / "checkpoints").exists())

    def test_space_url_accepts_only_exact_canonical_form(self):
        self.assertEqual(
            kit.canonical_space_url("https://x.com/i/spaces/1Example"),
            ("https://x.com/i/spaces/1Example", "1Example"),
        )
        for url in (
            "https://twitter.com/i/spaces/1Example",
            "https://x.com/i/spaces/1Example/",
            "https://x.com/i/spaces/1Example?ref=share",
            "https://x.com/i/spaces/1Example#fragment",
        ):
            with self.subTest(url=url):
                with self.assertRaisesRegex(kit.KitError, "Space URL"):
                    kit.canonical_space_url(url)


class TranscriptTests(unittest.TestCase):
    def test_cleanup_removes_attested_hallucination_and_derives_txt(self):
        draft = """WEBVTT

00:00:00.000 --> 00:00:05.000
hold music

00:00:10.000 --> 00:00:12.000
Program starts.

00:00:14.000 --> 00:00:16.000
Program ends.

00:00:20.000 --> 00:00:25.000
dead air hallucination
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "draft.vtt"
            source.write_text(draft, encoding="utf-8")
            count = kit.clean_transcript(
                source, root / "final.vtt", root / "final.txt", 10.0, 16.0
            )
            self.assertEqual(count, 2)
            self.assertEqual(
                (root / "final.txt").read_text(encoding="utf-8"),
                "Program starts.\nProgram ends.\n",
            )
            self.assertNotIn("hallucination", (root / "final.vtt").read_text(encoding="utf-8"))

    def test_cleanup_rejects_cues_straddling_either_cut_boundary(self):
        cases = (
            "00:00:09.800 --> 00:00:12.000",
            "00:00:14.000 --> 00:00:16.200",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, timing in enumerate(cases):
                draft = root / f"draft-{index}.vtt"
                draft.write_text(f"WEBVTT\n\n{timing}\nMixed cut speech.\n", encoding="utf-8")
                with self.subTest(timing=timing):
                    with self.assertRaisesRegex(kit.KitError, "straddles a cut boundary"):
                        kit.clean_transcript(
                            draft, root / "final.vtt", root / "final.txt", 10.0, 16.0
                        )


class WorkflowTests(unittest.TestCase):
    SOURCE_PROBE = {
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2,
            }
        ],
        "format": {"format_name": "mov,mp4,m4a", "duration": "25.0", "size": "12"},
    }
    FINAL_PROBE = {
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2,
            }
        ],
        "format": {"format_name": "mov,mp4,m4a", "duration": "6.0", "size": "11"},
    }
    METADATA = {
        "id": "1Example",
        "title": "twitter-spaces video #1Example",
        "upload_date": "20261007",
        "timestamp": 1791413864,
        "uploader": "JT",
        "uploader_id": "McCarthy_JT",
        "webpage_url": "https://x.com/i/spaces/1Example",
        "ext": "m4a",
        "acodec": "aac",
    }
    DRAFT = """WEBVTT

00:00:00.000 --> 00:00:05.000
hold music

00:00:10.000 --> 00:00:12.000
Program starts.

00:00:12.000 --> 00:00:14.000
Thank you.

00:00:14.000 --> 00:00:16.000
Program ends.

00:00:20.000 --> 00:00:25.000
dead air
"""

    def manifest(self, root: Path) -> Path:
        path = root / "manifest.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "date": "2026-10-07",
                    "slug": "proof-of-work",
                    "title": "Proof of Work",
                    "speakers": ["JT", "Matt McCarthy"],
                    "concise_description": "A transcript-grounded description.",
                    "spotify_description": "A longer transcript-grounded description.",
                    "cut_start_seconds": 10.0,
                    "cut_end_seconds": 16.0,
                    "edit_rationale": "Removed demonstrated hold music and dead air only.",
                    "selection_evidence": [
                        "The recording identifies the Wednesday Peak Mind show."
                    ],
                    "ruled_out_candidates": [],
                }
            ),
            encoding="utf-8",
        )
        return path

    def prepare_args(self, manifest: Path) -> argparse.Namespace:
        return argparse.Namespace(
            space_url="https://x.com/i/spaces/1Example",
            manifest=manifest,
        )

    def resume_args(self, checkpoint: Path, attested: bool = True) -> argparse.Namespace:
        return argparse.Namespace(checkpoint=checkpoint, attest_cleanup=attested)

    def create_checkpoint(self, root: Path, draft: str | None = None) -> Path:
        manifest = self.manifest(root)

        def fake_download(_url, destination):
            destination.write_bytes(b"source-audio")

        def fake_transcribe(_source, prefix):
            content = self.DRAFT if draft is None else draft
            prefix.with_suffix(".vtt").write_text(content, encoding="utf-8")
            return len(kit.parse_vtt(content))

        with (
            mock.patch.object(kit, "require_dependencies"),
            mock.patch.object(kit, "resolve_space", return_value=self.METADATA),
            mock.patch.object(kit, "download_source", side_effect=fake_download),
            mock.patch.object(kit, "probe_media", return_value=self.SOURCE_PROBE),
            mock.patch.object(kit, "transcribe_source", side_effect=fake_transcribe),
            mock.patch.object(kit, "tool_version", return_value="fixture-version"),
        ):
            return kit.prepare(
                self.prepare_args(manifest),
                output_root=root / "output",
                checkpoint_root=root / "checkpoints",
            )

    def resume_checkpoint(self, root: Path, checkpoint: Path) -> Path:
        def fake_trim(_source, destination, _start, _end):
            destination.write_bytes(b"final-audio")

        def fake_probe(path):
            return self.SOURCE_PROBE if path.name == "source.m4a" else self.FINAL_PROBE

        with (
            mock.patch.object(kit, "require_dependencies"),
            mock.patch.object(kit, "probe_media", side_effect=fake_probe),
            mock.patch.object(kit, "trim_audio", side_effect=fake_trim) as trim,
            mock.patch.object(kit, "run_command"),
            mock.patch.object(kit, "tool_version", return_value="fixture-version"),
            mock.patch.object(kit.shutil, "which", return_value="/fixture/ffprobe"),
        ):
            result = kit.resume(
                self.resume_args(checkpoint),
                output_root=root / "output",
                checkpoint_root=root / "checkpoints",
            )
            trim.reset_mock()
            repeated = kit.resume(
                self.resume_args(checkpoint),
                output_root=root / "output",
                checkpoint_root=root / "checkpoints",
            )
            trim.assert_not_called()
        self.assertEqual(repeated, result)
        return result

    def rewrite_evidence(self, final_dir: Path, mutate) -> None:
        evidence_path = final_dir / "SOURCE-EVIDENCE.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        mutate(evidence)
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        checksum_files = sorted(
            path
            for path in final_dir.iterdir()
            if path.is_file() and path.name != "SHA256SUMS"
        )
        (final_dir / "SHA256SUMS").write_text(
            "".join(f"{kit.sha256(path)}  {path.name}\n" for path in checksum_files),
            encoding="utf-8",
        )

    def test_prepare_creates_provenance_checkpoint_and_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = self.create_checkpoint(root)
            record = json.loads((checkpoint / "CHECKPOINT.json").read_text(encoding="utf-8"))
            self.assertEqual(record["source"]["space_id"], "1Example")
            self.assertEqual(record["source"]["space_url"], "https://x.com/i/spaces/1Example")
            self.assertEqual(record["source"]["sha256"], kit.sha256(checkpoint / "source.m4a"))
            self.assertEqual(
                record["draft"]["generated_from_source_sha256"], record["source"]["sha256"]
            )
            instructions = (checkpoint / "NEXT-STEPS.txt").read_text(encoding="utf-8")
            self.assertIn("Remove only demonstrated Whisper hallucination cues", instructions)
            self.assertIn("--attest-cleanup", instructions)
            self.assertFalse((root / "output" / "2026-10-07-proof-of-work").exists())

    def test_prepare_enforces_owner_only_scratch_without_executable_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint_root = root / "checkpoints"
            previous_umask = os.umask(0o022)
            try:
                checkpoint_root.mkdir(mode=0o777)
                sentinel = checkpoint_root / "preserve-me"
                sentinel.write_text("existing scratch content", encoding="utf-8")
                self.assertEqual(stat.S_IMODE(checkpoint_root.stat().st_mode), 0o755)
                checkpoint = self.create_checkpoint(root)
            finally:
                os.umask(previous_umask)

            self.assertEqual(stat.S_IMODE(checkpoint_root.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(checkpoint.stat().st_mode), 0o700)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "existing scratch content")
            for name in ("source.m4a", "draft.vtt", "draft.original.vtt"):
                self.assertEqual(stat.S_IMODE((checkpoint / name).stat().st_mode) & 0o111, 0)

    def test_prepare_rejects_symlinked_checkpoint_root_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "unrelated"
            target.mkdir(mode=0o755)
            target.chmod(0o755)
            sentinel = target / "preserve-me"
            sentinel.write_text("unrelated content", encoding="utf-8")
            checkpoint_root = root / "checkpoints"
            checkpoint_root.symlink_to(target, target_is_directory=True)

            with mock.patch.object(kit, "require_dependencies") as dependencies:
                with self.assertRaisesRegex(kit.KitError, "must not be a symlink"):
                    kit.prepare(
                        self.prepare_args(self.manifest(root)),
                        output_root=root / "output",
                        checkpoint_root=checkpoint_root,
                    )
                dependencies.assert_not_called()

            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o755)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "unrelated content")
            self.assertEqual([sentinel], list(target.iterdir()))

    def test_prepare_refuses_existing_checkpoint_before_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.create_checkpoint(root)
            with mock.patch.object(kit, "require_dependencies") as dependencies:
                with self.assertRaisesRegex(kit.KitError, "overwrite existing checkpoint"):
                    kit.prepare(
                        self.prepare_args(root / "manifest.json"),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )
                dependencies.assert_not_called()

    def test_prepare_rejects_non_jt_host(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = {**self.METADATA, "uploader_id": "SomeoneElse"}
            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "resolve_space", return_value=metadata),
            ):
                with self.assertRaisesRegex(kit.KitError, "not @McCarthy_JT"):
                    kit.prepare(
                        self.prepare_args(self.manifest(root)),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )

    def test_resume_requires_attestation_and_managed_checkpoint_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = self.create_checkpoint(root)
            with self.assertRaisesRegex(kit.KitError, "requires --attest-cleanup"):
                kit.resume(
                    self.resume_args(checkpoint, attested=False),
                    output_root=root / "output",
                    checkpoint_root=root / "checkpoints",
                )
            outside = root / "outside" / checkpoint.name
            with self.assertRaisesRegex(kit.KitError, "directly inside"):
                kit.resume(
                    self.resume_args(outside),
                    output_root=root / "output",
                    checkpoint_root=root / "checkpoints",
                )

    def test_resume_refuses_tampered_source_and_mismatched_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = self.create_checkpoint(root)
            (checkpoint / "source.m4a").write_bytes(b"different-audio")
            with mock.patch.object(kit, "require_dependencies"):
                with self.assertRaisesRegex(kit.KitError, "source audio hash"):
                    kit.resume(
                        self.resume_args(checkpoint),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = self.create_checkpoint(root)
            (checkpoint / "draft.vtt").write_text(
                self.DRAFT.replace("Program starts.", "Rewritten speech."), encoding="utf-8"
            )
            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "probe_media", return_value=self.SOURCE_PROBE),
            ):
                with self.assertRaisesRegex(kit.KitError, "may only delete whole Whisper cues"):
                    kit.resume(
                        self.resume_args(checkpoint),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = self.create_checkpoint(root)
            record_path = checkpoint / "CHECKPOINT.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["source"]["space_id"] = "AnotherSpace"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with mock.patch.object(kit, "require_dependencies"):
                with self.assertRaisesRegex(kit.KitError, "URL and id"):
                    kit.resume(
                        self.resume_args(checkpoint),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )

    def test_resume_uses_reviewed_vtt_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = self.create_checkpoint(root)
            reviewed = """WEBVTT

00:00:00.000 --> 00:00:05.000
hold music

00:00:10.000 --> 00:00:12.000
Program starts.

00:00:14.000 --> 00:00:16.000
Program ends.

00:00:20.000 --> 00:00:25.000
dead air
"""
            (checkpoint / "draft.vtt").write_text(reviewed, encoding="utf-8")
            result = self.resume_checkpoint(root, checkpoint)
            transcript = result / "2026-10-07-proof-of-work.txt"
            self.assertEqual(transcript.read_text(encoding="utf-8"), "Program starts.\nProgram ends.\n")
            evidence = json.loads((result / "SOURCE-EVIDENCE.json").read_text(encoding="utf-8"))
            self.assertTrue(evidence["transcript_cleanup"]["attested"])
            self.assertNotEqual(
                evidence["transcript_cleanup"]["cleaned_vtt_sha256"],
                evidence["transcript_cleanup"]["original_draft_vtt_sha256"],
            )
            self.assertFalse(checkpoint.exists())

    def test_shared_validation_requires_error_fatal_full_decode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.resume_checkpoint(root, self.create_checkpoint(root))
            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "probe_media", return_value=self.FINAL_PROBE),
                mock.patch.object(
                    kit, "run_command", side_effect=kit.KitError("decode failed")
                ) as decode,
            ):
                with self.assertRaisesRegex(kit.KitError, "decode failed"):
                    kit.validate_kit(result)
            command = decode.call_args.args[0]
            self.assertEqual(command[0], "ffmpeg")
            self.assertIn("-xerror", command)
            self.assertEqual(command[-3:], ["-f", "null", kit.os.devnull])

    def test_public_validate_reports_malformed_final_evidence(self):
        cases = (
            (
                "missing duration",
                lambda final: final.pop("duration_seconds"),
                "lacks final.duration_seconds",
            ),
            (
                "nonfinite duration",
                lambda final: final.update(duration_seconds=float("nan")),
                "final.duration_seconds must be a positive finite JSON number",
            ),
            (
                "string duration",
                lambda final: final.update(duration_seconds="6.0"),
                "final.duration_seconds must be a positive finite JSON number",
            ),
            (
                "negative duration",
                lambda final: final.update(duration_seconds=-1),
                "final.duration_seconds must be a positive finite JSON number",
            ),
            (
                "missing byte count",
                lambda final: final.pop("byte_count"),
                "lacks final.byte_count",
            ),
            (
                "nonfinite byte count",
                lambda final: final.update(byte_count=float("inf")),
                "final.byte_count must be a positive JSON integer",
            ),
            (
                "string byte count",
                lambda final: final.update(byte_count="11"),
                "final.byte_count must be a positive JSON integer",
            ),
            (
                "negative byte count",
                lambda final: final.update(byte_count=-1),
                "final.byte_count must be a positive JSON integer",
            ),
            (
                "missing digest",
                lambda final: final.pop("sha256"),
                "lacks final.sha256",
            ),
            (
                "numeric digest",
                lambda final: final.update(sha256=123),
                "final.sha256 must be a lowercase SHA-256 digest",
            ),
            (
                "malformed digest",
                lambda final: final.update(sha256="not-a-digest"),
                "final.sha256 must be a lowercase SHA-256 digest",
            ),
        )
        for name, mutate, message in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                final_dir = self.resume_checkpoint(root, self.create_checkpoint(root))
                self.rewrite_evidence(final_dir, lambda evidence: mutate(evidence["final"]))
                stderr = io.StringIO()
                with (
                    mock.patch.object(kit, "require_dependencies"),
                    mock.patch.object(kit, "probe_media") as probe,
                    contextlib.redirect_stderr(stderr),
                ):
                    result = kit.main(["validate", str(final_dir)])
                self.assertEqual(result, 2)
                self.assertIn(message, stderr.getvalue())
                probe.assert_not_called()

    def test_resume_preserves_checkpoint_when_existing_kit_provenance_differs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = self.create_checkpoint(root)
            saved_checkpoint = root / "saved-checkpoint"
            shutil.copytree(checkpoint, saved_checkpoint)
            final_dir = self.resume_checkpoint(root, checkpoint)
            shutil.copytree(saved_checkpoint, checkpoint)

            self.rewrite_evidence(
                final_dir,
                lambda evidence: evidence["source"].update(
                    {"sha256": "0" * 64}
                ),
            )

            def fake_probe(path):
                return self.SOURCE_PROBE if path.name == "source.m4a" else self.FINAL_PROBE

            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "probe_media", side_effect=fake_probe),
                mock.patch.object(kit, "run_command"),
            ):
                with self.assertRaisesRegex(kit.KitError, "checkpoint provenance"):
                    kit.resume(
                        self.resume_args(checkpoint),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )
            self.assertTrue(checkpoint.is_dir())

    def test_invalid_final_metadata_is_rejected_by_validation_and_resume(self):
        cases = (
            ("uploader_id", "SomeoneElse", "not @McCarthy_JT"),
            ("upload_date", "20261008", "does not match manifest date"),
        )
        for field, value, message in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                checkpoint = self.create_checkpoint(root)
                saved_checkpoint = root / "saved-checkpoint"
                shutil.copytree(checkpoint, saved_checkpoint)
                final_dir = self.resume_checkpoint(root, checkpoint)
                self.rewrite_evidence(
                    final_dir,
                    lambda evidence, field=field, value=value: evidence["source"]["yt_dlp"].update(
                        {field: value}
                    ),
                )

                def fake_probe(path):
                    return self.SOURCE_PROBE if path.name == "source.m4a" else self.FINAL_PROBE

                with (
                    mock.patch.object(kit, "require_dependencies"),
                    mock.patch.object(kit, "probe_media", side_effect=fake_probe),
                    mock.patch.object(kit, "run_command"),
                ):
                    with self.assertRaisesRegex(kit.KitError, message):
                        kit.validate_kit(final_dir)
                    with self.assertRaisesRegex(kit.KitError, message):
                        kit.resume(
                            self.resume_args(checkpoint),
                            output_root=root / "output",
                            checkpoint_root=root / "checkpoints",
                        )
                    shutil.copytree(saved_checkpoint, checkpoint)
                    with self.assertRaisesRegex(kit.KitError, message):
                        kit.resume(
                            self.resume_args(checkpoint),
                            output_root=root / "output",
                            checkpoint_root=root / "checkpoints",
                        )
                self.assertTrue(checkpoint.is_dir())

    def test_missing_checkpoint_cannot_accept_renamed_kit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.resume_checkpoint(root, self.create_checkpoint(root))
            renamed = result.with_name("2026-10-08-other-show")
            result.rename(renamed)
            missing_checkpoint = root / "checkpoints" / renamed.name
            with mock.patch.object(kit, "require_dependencies"):
                with self.assertRaisesRegex(kit.KitError, "directory name"):
                    kit.resume(
                        self.resume_args(missing_checkpoint),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )

    def test_resume_rejects_straddling_reviewed_cue_before_trim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint = self.create_checkpoint(
                root,
                "WEBVTT\n\n00:00:09.800 --> 00:00:12.000\nMixed cut speech.\n",
            )
            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "probe_media", return_value=self.SOURCE_PROBE),
                mock.patch.object(kit, "trim_audio") as trim,
            ):
                with self.assertRaisesRegex(kit.KitError, "straddles a cut boundary"):
                    kit.resume(
                        self.resume_args(checkpoint),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )
                trim.assert_not_called()

    def test_prepare_rejects_cut_end_beyond_one_source_aac_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root)
            short_probe = {
                **self.SOURCE_PROBE,
                "format": {**self.SOURCE_PROBE["format"], "duration": "15.8"},
            }

            def fake_download(_url, destination):
                destination.write_bytes(b"source-audio")

            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "resolve_space", return_value=self.METADATA),
                mock.patch.object(kit, "download_source", side_effect=fake_download),
                mock.patch.object(kit, "probe_media", return_value=short_probe),
                mock.patch.object(kit, "transcribe_source") as transcribe,
            ):
                with self.assertRaisesRegex(kit.KitError, "more than one AAC frame"):
                    kit.prepare(
                        self.prepare_args(manifest),
                        output_root=root / "output",
                        checkpoint_root=root / "checkpoints",
                    )
                transcribe.assert_not_called()


class DurationValidationTests(unittest.TestCase):
    def probe(self, duration: float) -> dict:
        return {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                }
            ],
            "format": {
                "format_name": "mov,mp4,m4a",
                "duration": str(duration),
                "size": "11",
            },
        }

    def test_final_duration_allows_at_most_one_aac_frame(self):
        kit.validate_final_probe(self.probe(6.021), 6.0)
        with self.assertRaisesRegex(kit.KitError, "more than one AAC frame"):
            kit.validate_final_probe(self.probe(6.022), 6.0)


if __name__ == "__main__":
    unittest.main()
