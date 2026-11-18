"""Shorts regressions exercised with in-memory word timings."""
import importlib
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

SHORTS = Path(__file__).resolve().parents[2] / "social" / "shorts"
PIL = ModuleType("PIL")
for name in ("Image", "ImageDraw", "ImageFilter", "ImageFont"):
    setattr(PIL, name, object())

with patch.object(sys, "path", [str(SHORTS), *sys.path]), patch.dict(
    sys.modules, {"numpy": ModuleType("numpy"), "PIL": PIL}
):
    render_short = importlib.import_module("render_short")
    week = importlib.import_module("week")


class ShortsTests(unittest.TestCase):
    def test_matches_listed_words_and_variations_as_whole_tokens(self):
        profane = (
            "shit", "shitty", "bullshit", "fuck", "fucking", "fucked",
            "fucker", "motherfucker", "goddamn", "bitch", "asshole",
            "shits", "bullshittin’", "bitches", "assholes", "“FUCKIN'!”",
            "motherfuckers", "goddamned", "shithead", "cluster-fucks",
        )
        clean = ("assess", "classic", "shiitake", "shitake", "embassy", "scunthorpe")
        for word in profane:
            with self.subTest(word=word):
                self.assertTrue(render_short.is_profane(word))
        for word in clean:
            with self.subTest(word=word):
                self.assertFalse(render_short.is_profane(word))

    def test_caption_masking_uses_same_word_check(self):
        with patch.object(render_short, "BLEEP", True):
            self.assertEqual(render_short.display("Motherfuckers!"), "M************!")
            self.assertEqual(render_short.display("“Fuckin’!”"), "“F*****’!”")
            self.assertEqual(render_short.display("shitake,"), "SHITAKE")
        with patch.object(render_short, "BLEEP", False):
            self.assertEqual(render_short.display("Motherfuckers!"), "MOTHERFUCKERS!")

    def test_week_renders_bleeped_copy_only_for_clip_with_swear(self):
        clips = [
            {"n": 1, "audio": "unused.m4a", "title": "Marked",
             "headline": "First", "recorded": "November 1"},
            {"n": 2, "audio": "unused.m4a", "title": "Clean",
             "headline": "Second", "recorded": "November 1"},
        ]
        word_lists = [
            [(0.0, 0.4, "assholes")],
            [(0.0, 0.4, "classic"), (0.4, 0.8, "shitake")],
        ]
        with patch.object(week, "read_words", side_effect=word_lists), patch.object(
            week.os.path, "exists", return_value=True
        ), patch.object(week.os, "makedirs"), patch.object(week.subprocess, "run") as run:
            week.render(clips)

        outputs = [
            (Path(call.args[0][-1]).name, "--bleep" in call.args[0])
            for call in run.call_args_list
        ]
        self.assertEqual(outputs, [
            ("01 - Marked (X).mp4", False),
            ("01 - Marked (YouTube, bleeped).mp4", True),
            ("02 - Clean.mp4", False),
        ])
