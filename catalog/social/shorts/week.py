"""Render a week of Peak Mind shorts and write its posting kit.

usage (from the repo root):
  python3 -I catalog/social/shorts/week.py render catalog/social/shorts/week-01.json
  python3 -I catalog/social/shorts/week.py kit catalog/social/shorts/week-01.json

The week file lists clips (episode slug, moment number in catalog/social/clips/<slug>.md, post date,
headline, recording date, source audio name). Audio comes from ~/Downloads/JT social clips/Ready to post/
and videos go to ~/Downloads/JT social clips/Shorts/. Clips that swear get an uncensored X file and a
bleeped YouTube file. The kit is written next to the week file and copied to the Shorts folder.
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.expanduser("~/Downloads/JT social clips/Ready to post")
OUT = os.path.expanduser("~/Downloads/JT social clips/Shorts")
WORK = os.path.expanduser("~/Downloads/JT social clips/Shorts/.words")
SITE = "https://jtworldteacher.com/podcast"
SPOTIFY = "https://open.spotify.com/show/033LHLE9BxNUNTLSzmDqfC"
POST_TIME = "12:00 PM ET"

sys.path.insert(0, HERE)
from render_short import is_profane, read_words  # noqa: E402


def files_for(c):
    base = os.path.join(OUT, f"{c['n']:02d} - {c['title']}")
    if os.path.exists(base + ".mp4"):
        return base + ".mp4", base + ".mp4"
    return base + " (X).mp4", base + " (YouTube, bleeped).mp4"


def render(week):
    os.makedirs(WORK, exist_ok=True)
    for c in week:
        audio = os.path.join(SRC, c["audio"])
        vtt = os.path.join(WORK, f"{c['n']:02d}.vtt")
        if not os.path.exists(vtt):
            subprocess.run([sys.executable, "-I", os.path.join(HERE, "align_words.py"), audio, vtt], check=True)
        swears = [w for _, _, w in read_words(vtt) if is_profane(w)]
        base = os.path.join(OUT, f"{c['n']:02d} - {c['title']}")
        cmd = [sys.executable, "-I", os.path.join(HERE, "render_short.py"), "--audio", audio, "--words", vtt,
               "--headline", c["headline"], "--speaker", c.get("speaker", "JT McCarthy"),
               "--tag", f"Recorded live on X · {c['recorded']}", "--art", "none"]
        if swears:
            subprocess.run(cmd + ["--out", base + " (X).mp4"], check=True)
            subprocess.run(cmd + ["--bleep", "--out", base + " (YouTube, bleeped).mp4"], check=True)
        else:
            subprocess.run(cmd + ["--out", base + ".mp4"], check=True)


def moment(c):
    text = open(os.path.join(REPO, "catalog/social/clips", c["episode"] + ".md"), encoding="utf-8").read()
    title = re.match(r"# (.+): social clips", text).group(1)
    block = re.split(r"\n(?=### \d+\. )", text)[c["moment"]]
    get = lambda k: re.search(rf"\*\*{k}:\*\* (.+)", block).group(1).strip()
    return title, get("Caption"), get("Hashtags").split()


def x_len(text):
    # X counts every URL as 23 characters
    return len(re.sub(r"https?://\S+", "x" * 23, text))


def kit(week, week_path):
    lines = ["# Peak Mind shorts: posting kit\n",
             f"Post time for every slot: {POST_TIME}, on X and YouTube Shorts the same day. Nothing in this kit "
             "has been posted. Each post goes out only after Matt approves it.\n",
             "Files are in `~/Downloads/JT social clips/Shorts/`. X gets the uncensored file and YouTube gets "
             "the bleeped one when a clip has both.\n"]
    for c in week:
        title, caption, tags = moment(c)
        x_file, yt_file = files_for(c)
        link = f"{SITE}/{c['episode']}/"
        day = dt.date.fromisoformat(c["post_on"])
        wed = day.weekday() == 2
        live = ["\n\nPeak Mind is live tonight at 7 PM ET.", "\n\nLive tonight, 7 PM ET."] if wed else [""]
        variants = [caption + lv + lead + link + ("\n\n" + " ".join(tags[:n]) if n else "")
                    for lead in ("\n\nFull episode: ", "\n\n") for lv in live for n in (2, 1, 0)]
        x_text = next((v for v in variants if x_len(v) <= 280), None)
        assert x_text, f"#{c['n']}: caption too long for X even without extras"
        yt_desc = (f"{caption}\n\nFull episode: {link}\nPeak Mind: JT and Matt McCarthy, live on X every Wednesday "
                   f"at 7 PM ET. Listen on Spotify: {SPOTIFY}\n\n" + " ".join(tags[:5]))
        lines += [
            f"## {day.strftime('%a %b %-d')}: #{c['n']} {c['headline']}\n",
            f"- **From:** {title} (recorded {c['recorded']})",
            f"- **X file:** `{os.path.basename(x_file)}`",
            f"- **YouTube file:** `{os.path.basename(yt_file)}`\n",
            f"**X post** ({x_len(x_text)}/280):\n",
            "```text\n" + x_text + "\n```\n",
            f"**YouTube title** ({len(c['headline'])}/100):\n",
            "```text\n" + c["headline"] + "\n```\n",
            "**YouTube description:**\n",
            "```text\n" + yt_desc + "\n```\n",
        ]
    out = os.path.splitext(week_path)[0] + "-kit.md"
    text = "\n".join(lines)
    assert "\u2014" not in text, "kit must not contain em dashes"
    open(out, "w", encoding="utf-8").write(text)
    os.makedirs(OUT, exist_ok=True)
    shutil.copy(out, os.path.join(OUT, os.path.basename(out)))
    print("wrote", out)


if __name__ == "__main__":
    cmd, path = sys.argv[1], sys.argv[2]
    week = json.load(open(path, encoding="utf-8"))
    {"render": lambda: render(week), "kit": lambda: kit(week, path)}[cmd]()
