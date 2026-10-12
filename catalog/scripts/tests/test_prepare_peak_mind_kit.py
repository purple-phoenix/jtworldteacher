#!/usr/bin/env python3

import argparse
import importlib.util
import json
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


class TranscriptTests(unittest.TestCase):
    def test_clean_transcript_drops_cut_material_and_shifts_cues(self):
        raw = """WEBVTT

00:00:00.000 --> 00:00:05.000
hold music hallucination

00:00:10.000 --> 00:00:12.000
Program starts.

00:00:14.500 --> 00:00:16.000
Second line.

00:00:20.000 --> 00:00:25.000
closing hallucination
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.vtt"
            output_vtt = root / "final.vtt"
            output_txt = root / "final.txt"
            source.write_text(raw, encoding="utf-8")
            count = kit.clean_transcript(source, output_vtt, output_txt, 10.0, 16.0)
            self.assertEqual(count, 2)
            self.assertEqual(
                output_vtt.read_text(encoding="utf-8"),
                "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nProgram starts.\n\n"
                "00:00:04.500 --> 00:00:06.000\nSecond line.\n",
            )
            self.assertEqual(output_txt.read_text(encoding="utf-8"), "Program starts.\nSecond line.\n")

    def test_clean_transcript_refuses_cue_that_straddles_editorial_cut(self):
        raw = """WEBVTT

00:00:09.000 --> 00:00:12.000
Pre-show and show in one cue.
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.vtt"
            source.write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(kit.KitError, "straddles a cut boundary"):
                kit.clean_transcript(source, root / "final.vtt", root / "final.txt", 10.0, 12.0)

    def test_clean_transcript_refuses_cue_just_before_start_boundary(self):
        raw = """WEBVTT

00:00:09.800 --> 00:00:12.000
Cut speech and retained speech in one cue.
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.vtt"
            source.write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(kit.KitError, "straddles a cut boundary"):
                kit.clean_transcript(source, root / "final.vtt", root / "final.txt", 10.0, 16.0)

    def test_clean_transcript_refuses_cue_just_after_end_boundary(self):
        raw = """WEBVTT

00:00:14.000 --> 00:00:16.200
Retained speech and cut speech in one cue.
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.vtt"
            source.write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(kit.KitError, "straddles a cut boundary"):
                kit.clean_transcript(source, root / "final.vtt", root / "final.txt", 10.0, 16.0)


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


class PrepareBehaviorTests(unittest.TestCase):
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

    def args(self, root: Path, manifest: Path, source: Path, prefix: Path) -> argparse.Namespace:
        return argparse.Namespace(
            space_url="https://x.com/i/spaces/1Example",
            manifest=manifest,
            output_root=root / "output",
            source_file=source,
            transcript_prefix=prefix,
        )

    def test_prepare_refuses_existing_kit_before_command_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root)
            existing = root / "output" / "2026-10-07-proof-of-work"
            existing.mkdir(parents=True)
            args = self.args(root, manifest, root / "source.m4a", root / "raw")
            with mock.patch.object(kit, "require_dependencies") as dependencies:
                with self.assertRaisesRegex(kit.KitError, "Refusing to overwrite"):
                    kit.prepare(args)
                dependencies.assert_not_called()

    def test_prepare_builds_and_validates_kit_with_mocked_media_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root)
            source = root / "source.m4a"
            source.write_bytes(b"source-audio")
            prefix = root / "raw"
            prefix.with_suffix(".vtt").write_text(
                "WEBVTT\n\n"
                "00:00:00.000 --> 00:00:05.000\nhold hallucination\n\n"
                "00:00:10.000 --> 00:00:12.000\nProgram starts.\n\n"
                "00:00:14.500 --> 00:00:16.000\nProgram ends.\n",
                encoding="utf-8",
            )
            args = self.args(root, manifest, source, prefix)

            source_probe = {
                "streams": [{"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2}],
                "format": {"format_name": "mov,mp4,m4a", "duration": "25.0", "size": "12"},
            }
            final_probe = {
                "streams": [{"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2}],
                "format": {"format_name": "mov,mp4,m4a", "duration": "6.0", "size": "11"},
            }

            def fake_trim(_source, destination, _start, _end):
                destination.write_bytes(b"final-audio")

            def fake_probe(path):
                return final_probe if path.name.endswith("proof-of-work.m4a") else source_probe

            metadata = {
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
            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "resolve_space", return_value=metadata),
                mock.patch.object(kit, "probe_media", side_effect=fake_probe),
                mock.patch.object(kit, "trim_audio", side_effect=fake_trim),
                mock.patch.object(kit, "run_command"),
                mock.patch.object(kit, "tool_version", return_value="fixture-version"),
            ):
                result = kit.prepare(args)
                self.assertTrue(result.is_dir())
                self.assertEqual(
                    (result / "2026-10-07-proof-of-work.txt").read_text(encoding="utf-8"),
                    "Program starts.\nProgram ends.\n",
                )
                self.assertIn("TITLE: Proof of Work", (result / "UPLOAD.txt").read_text(encoding="utf-8"))
                self.assertIn("2026-10-07-proof-of-work.m4a", (result / "SHA256SUMS").read_text())

    def test_prepare_transcribes_edited_audio_when_raw_transcript_is_not_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root)
            source = root / "source.m4a"
            source.write_bytes(b"source-audio")
            args = self.args(root, manifest, source, root / "unused")
            args.transcript_prefix = None

            source_probe = {
                "streams": [{"codec_type": "audio", "codec_name": "aac"}],
                "format": {"format_name": "mov,mp4,m4a", "duration": "25.0", "size": "12"},
            }
            final_probe = {
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

            def fake_trim(_source, destination, _start, _end):
                destination.write_bytes(b"final-audio")

            def fake_transcribe(_source, prefix):
                prefix.with_suffix(".txt").write_text("Fresh final transcript.\n", encoding="utf-8")
                prefix.with_suffix(".vtt").write_text(
                    "WEBVTT\n\n00:00:00.000 --> 00:00:06.000\nFresh final transcript.\n",
                    encoding="utf-8",
                )

            def fake_probe(path):
                return final_probe if path.name.endswith("proof-of-work.m4a") else source_probe

            metadata = {
                "id": "1Example",
                "upload_date": "20261007",
                "uploader_id": "McCarthy_JT",
            }
            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "resolve_space", return_value=metadata),
                mock.patch.object(kit, "probe_media", side_effect=fake_probe),
                mock.patch.object(kit, "trim_audio", side_effect=fake_trim),
                mock.patch.object(kit, "transcribe_source", side_effect=fake_transcribe),
                mock.patch.object(kit, "run_command"),
                mock.patch.object(kit, "tool_version", return_value="fixture-version"),
            ):
                result = kit.prepare(args)

            transcript = result / "2026-10-07-proof-of-work.txt"
            self.assertEqual(transcript.read_text(encoding="utf-8"), "Fresh final transcript.\n")
            evidence = json.loads((result / "SOURCE-EVIDENCE.json").read_text(encoding="utf-8"))
            self.assertIn("edited M4A", evidence["final"]["transcript_method"])

    def test_prepare_rejects_non_jt_host(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root)
            source = root / "source.m4a"
            source.write_bytes(b"source")
            prefix = root / "raw"
            prefix.with_suffix(".vtt").write_text(
                "WEBVTT\n\n00:00:10.000 --> 00:00:16.000\nProgram.\n"
            )
            metadata = {
                "id": "1Example",
                "upload_date": "20261007",
                "uploader_id": "SomeoneElse",
            }
            with (
                mock.patch.object(kit, "require_dependencies"),
                mock.patch.object(kit, "resolve_space", return_value=metadata),
            ):
                with self.assertRaisesRegex(kit.KitError, "not @McCarthy_JT"):
                    kit.prepare(self.args(root, manifest, source, prefix))


if __name__ == "__main__":
    unittest.main()
