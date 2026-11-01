#!/usr/bin/env python3
"""Evidence helpers for choosing and reviewing Peak Mind cut points.

These commands support the judgment gates in catalog/PEAK_MIND_SPOTIFY.md; they never
choose cuts or edit files on their own. Timestamps are seconds on the source timeline.

  markers <vtt>                        on-air open/close and Q&A handoff candidates
  cues <vtt> <from> <to>               transcript cues in a window
  scan <vtt> <start> <end>             likely Whisper hallucinations inside the kept window
  check <audio> <vtt> <start> <end>    straddle + loudness checks at both cuts (exit 1 on FAIL)
  clips <audio> <start> <end> <dir> <prefix>   20 s opening/ending review clips
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

_KIT_PATH = Path(__file__).resolve().with_name("prepare_peak_mind_kit.py")
_SPEC = importlib.util.spec_from_file_location("prepare_peak_mind_kit", _KIT_PATH)
assert _SPEC and _SPEC.loader
kit = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault(_SPEC.name, kit)
_SPEC.loader.exec_module(kit)
Cue = kit.Cue

# Phrases JT and Matt actually used on air (Oct 2026 episodes) to open and close the show.
OPEN_RE = re.compile(r"this is peak mind|i'm jt\b|let's start|let's try to do this right|welcome to", re.I)
CLOSE_RE = re.compile(
    r"end of the (show|podcast)|end the (show|podcast)|attending this podcast"
    r"|thank you all for (listening|attending)|that's (the|our) show",
    re.I,
)
HANDOFF_RE = re.compile(
    r"q and a|q&a|open (it )?up|switch over|(letting|let) .{0,20}\bup\b|go ahead, (dude|man)"
    r"|take it away|speakers",
    re.I,
)
STOCK_RE = re.compile(r"^(thank you\.?|thanks for watching.*|we'll be right back\.?|you|bye\.?|\.+)$", re.I)

QUIET_DB = -40.0  # a cut must land in a 50 ms window quieter than this
WINDOW = 0.05


def load_cues(vtt: Path) -> list[Cue]:
    return kit.parse_vtt(vtt.read_text(encoding="utf-8"))


def clock(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 3600}:{whole % 3600 // 60:02d}:{whole % 60:02d}"


def classify(text: str) -> list[str]:
    tags = []
    if OPEN_RE.search(text):
        tags.append("OPEN")
    if CLOSE_RE.search(text):
        tags.append("CLOSE")
    if HANDOFF_RE.search(text):
        tags.append("HANDOFF")
    return tags


def hallucination_reason(cue: Cue) -> str | None:
    text = cue.text.strip()
    if STOCK_RE.match(text):
        return "stock"
    words = re.findall(r"[a-z']+", text.lower())
    grams = Counter(tuple(words[i : i + 4]) for i in range(len(words) - 3))
    if grams and grams.most_common(1)[0][1] >= 3:
        return "loop"
    span = cue.end - cue.start
    if span >= 12 and len(words) / span < 0.6:
        return "sparse"
    return None


def straddling(cues: list[Cue], cut: float) -> list[Cue]:
    return [cue for cue in cues if cue.start < cut < cue.end]


def rms_profile(audio: Path, center: float, half_span: float = 0.5) -> list[tuple[float, float]]:
    """50 ms RMS levels (dB) around center, as (window_start_seconds, level)."""
    start = max(0.0, center - half_span)
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start:.3f}", "-t", f"{2 * half_span:.3f}",
            "-i", str(audio), "-af",
            "aresample=48000,asetnsamples=2400,astats=metadata=1:reset=1,"
            "ametadata=print:key=lavfi.astats.Overall.RMS_level",
            "-f", "null", "-",
        ],
        capture_output=True, text=True, check=True,
    )
    return parse_rms(result.stderr, start)


def parse_rms(ffmpeg_log: str, offset: float) -> list[tuple[float, float]]:
    times = [float(t) for t in re.findall(r"pts_time:([0-9.]+)", ffmpeg_log)]
    levels = [float(v) if v not in ("-inf", "inf") else -120.0
              for v in re.findall(r"RMS_level=(-?inf|-?[0-9.]+)", ffmpeg_log)]
    return [(round(offset + t, 3), level) for t, level in zip(times, levels)]


def level_at(profile: list[tuple[float, float]], cut: float) -> float | None:
    for start, level in profile:
        if start <= cut < start + WINDOW:
            return level
    return None


def cmd_markers(args: argparse.Namespace) -> int:
    for cue in load_cues(args.vtt):
        tags = classify(cue.text)
        if tags:
            print(f"{cue.start:9.2f} ({clock(cue.start)}) {'/'.join(tags):13} {cue.text[:150]}")
    return 0


def cmd_cues(args: argparse.Namespace) -> int:
    for cue in load_cues(args.vtt):
        if args.start <= cue.start <= args.end:
            print(f"{cue.start:9.2f}-{cue.end:9.2f} {cue.text}")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    for cue in load_cues(args.vtt):
        if args.start <= cue.start and cue.end <= args.end:
            reason = hallucination_reason(cue)
            if reason:
                print(f"{cue.start:9.2f}-{cue.end:9.2f} [{reason}] {cue.text[:160]}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    cues = load_cues(args.vtt)
    ok = True
    for name, cut in (("start", args.start), ("end", args.end)):
        crossing = straddling(cues, cut)
        level = level_at(rms_profile(args.audio, cut), cut)
        quiet = level is not None and level <= QUIET_DB
        status = "PASS" if quiet and not crossing else "FAIL"
        ok &= status == "PASS"
        shown = "n/a" if level is None else f"{level:.1f} dB"
        print(f"{name} {cut:.3f} ({clock(cut)}): {status} level={shown}"
              + (f" crosses cue {crossing[0].start:.2f}-{crossing[0].end:.2f}" if crossing else ""))
    return 0 if ok else 1


def cmd_clips(args: argparse.Namespace) -> int:
    args.outdir.mkdir(parents=True, exist_ok=True)
    for label, at in (("opening", args.start), ("ending", max(0.0, args.end - 20))):
        out = args.outdir / f"{args.prefix}-{label}.m4a"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{at:.3f}", "-t", "20",
             "-i", str(args.audio), "-c:a", "aac", "-b:a", "128k", str(out)],
            check=True,
        )
        print(out)
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = root.add_subparsers(dest="command", required=True)
    specs = (
        ("markers", cmd_markers, (("vtt", Path),)),
        ("cues", cmd_cues, (("vtt", Path), ("start", float), ("end", float))),
        ("scan", cmd_scan, (("vtt", Path), ("start", float), ("end", float))),
        ("check", cmd_check, (("audio", Path), ("vtt", Path), ("start", float), ("end", float))),
        ("clips", cmd_clips, (("audio", Path), ("start", float), ("end", float), ("outdir", Path), ("prefix", str))),
    )
    for name, func, arguments in specs:
        command = sub.add_parser(name)
        for argument, kind in arguments:
            command.add_argument(argument, type=kind)
        command.set_defaults(func=func)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
