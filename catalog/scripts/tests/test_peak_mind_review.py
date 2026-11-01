#!/usr/bin/env python3

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "peak_mind_review.py"
SPEC = importlib.util.spec_from_file_location("peak_mind_review", SCRIPT)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)
Cue = review.Cue


class MarkerTests(unittest.TestCase):
    def test_classifies_on_air_open_close_and_handoff(self):
        self.assertEqual(review.classify("This is Peak Mind."), ["OPEN"])
        self.assertEqual(review.classify("And we'll look at this as the end of the podcast."), ["CLOSE"])
        self.assertEqual(
            review.classify("So we're going to switch over now and, uh, thank you all for attending this podcast."),
            ["CLOSE", "HANDOFF"],
        )
        self.assertEqual(review.classify("All right, buddy, I'm letting you up."), ["HANDOFF"])
        self.assertEqual(review.classify("The Monroe doctrine is old."), [])


class HallucinationTests(unittest.TestCase):
    def test_flags_stock_phrases_loops_and_sparse_cues_only(self):
        self.assertEqual(review.hallucination_reason(Cue(0.0, 29.98, "We'll be right back.")), "stock")
        looped = "I'm going to go up and I'm going to go up and I'm going to go up and visit"
        self.assertEqual(review.hallucination_reason(Cue(350.0, 370.0, looped)), "loop")
        self.assertEqual(review.hallucination_reason(Cue(10.0, 40.0, "Okay so")), "sparse")
        self.assertIsNone(review.hallucination_reason(Cue(1.0, 4.0, "Actually, I'm a little wound up.")))


class CutGeometryTests(unittest.TestCase):
    def test_straddling_excludes_cues_that_touch_the_cut(self):
        cues = [Cue(10.0, 12.0, "a"), Cue(12.0, 14.0, "b"), Cue(15.0, 20.0, "c")]
        self.assertEqual(review.straddling(cues, 12.0), [])
        self.assertEqual(review.straddling(cues, 16.0), [cues[2]])

    def test_parses_ffmpeg_rms_log_and_finds_the_cut_window(self):
        log = (
            "frame:0 pts:0 pts_time:0\nlavfi.astats.Overall.RMS_level=-24.5\n"
            "frame:1 pts:2400 pts_time:0.05\nlavfi.astats.Overall.RMS_level=-inf\n"
            "frame:2 pts:4800 pts_time:0.1\nlavfi.astats.Overall.RMS_level=-12.0\n"
        )
        profile = review.parse_rms(log, 100.0)
        self.assertEqual(profile, [(100.0, -24.5), (100.05, -120.0), (100.1, -12.0)])
        self.assertEqual(review.level_at(profile, 100.07), -120.0)
        self.assertIsNone(review.level_at(profile, 101.0))


if __name__ == "__main__":
    unittest.main()
