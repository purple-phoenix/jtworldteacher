"""Render a week of Peak Mind shorts and write its posting kit.

usage (from the repo root):
  python3 -I catalog/social/shorts/week.py render catalog/social/shorts/week-01.json
  python3 -I catalog/social/shorts/week.py kit catalog/social/shorts/week-01.json
  python3 -I catalog/social/shorts/week.py stage catalog/social/shorts/week-01.json   # after approval

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
OUT = os.path.expanduser(os.environ.get("PEAK_MIND_SHORTS_DIR", "~/Downloads/JT social clips/Shorts"))
WORK = os.path.join(OUT, ".words")
SITE = "https://jtworldteacher.com/podcast"
SPOTIFY = "https://open.spotify.com/show/033LHLE9BxNUNTLSzmDqfC"
POST_TIME = "12:00 PM ET"

sys.path.insert(0, HERE)
from render_short import is_profane, read_words  # noqa: E402


def output_base(c):
    return os.path.join(OUT, c.get("output_subdir", ""), f"{c['n']:02d} - {c['title']}")


def files_for(c):
    base = output_base(c)
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
        base = output_base(c)
        os.makedirs(os.path.dirname(base), exist_ok=True)
        cmd = [sys.executable, "-I", os.path.join(HERE, "render_short.py"), "--audio", audio, "--words", vtt,
               "--headline", c["headline"], "--speaker", c.get("speaker", "JT McCarthy"),
               "--tag", f"Recorded live on X · {c['recorded']}", "--art", "none"]
        if swears:
            subprocess.run(cmd + ["--out", base + " (X).mp4"], check=True)
            subprocess.run(cmd + ["--bleep", "--out", base + " (YouTube, bleeped).mp4"], check=True)
        else:
            subprocess.run(cmd + ["--out", base + ".mp4"], check=True)


def moment(c):
    if "caption" in c:
        return c["episode_title"], c["caption"], c["hashtags"]
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
             f"Post time for every slot: {POST_TIME}, on X, YouTube Shorts, TikTok and Instagram the same day. Nothing in this kit "
             "has been posted. Each post goes out only after Matt approves it.\n",
             f"Files are in `{OUT}/`. X gets the uncensored file and YouTube, TikTok and Instagram get "
             "the bleeped one when a clip has both.\n"]
    for c in week:
        title, caption, tags = moment(c)
        x_file, yt_file = files_for(c)
        spare = c.get("spare", False)
        day = None if spare else dt.date.fromisoformat(c["post_on"])
        wed = day is not None and day.weekday() == 2 and c.get("promote_live", True)
        live = ["\n\nPeak Mind is live tonight at 7 PM ET.", "\n\nLive tonight, 7 PM ET."] if wed else [""]
        variants = [caption + lv + lead + SPOTIFY + ("\n\n" + " ".join(tags[:n]) if n else "")
                    for lead in ("\n\nPeak Mind on Spotify: ", "\n\nSpotify: ", "\n\n") for lv in live for n in (2, 1, 0)]
        x_text = next((v for v in variants if x_len(v) <= 280), None)
        assert x_text, f"#{c['n']}: caption too long for X even without extras"
        show_line = "JT and Matt McCarthy."
        if c.get("promote_live", True):
            show_line = "JT and Matt McCarthy, live on X every Wednesday at 7 PM ET."
        yt_desc = (f"{caption}\n\nListen to Peak Mind on Spotify: {SPOTIFY}\n{show_line}\n\n" + " ".join(tags[:5]))
        slot = "SPARE (no posting date)" if spare else day.strftime('%a %b %-d')
        lines += [
            f"## {slot}: #{c['n']} {c['headline']}\n",
            f"- **From:** {title} (recorded {c['recorded']})",
            *([f"- **Length:** {c['duration_seconds']:.2f} seconds",
               f"- **Why:** {c['why']}"] if "duration_seconds" in c else []),
            f"- **X file:** `{os.path.relpath(x_file, OUT)}`",
            f"- **YouTube file:** `{os.path.relpath(yt_file, OUT)}`\n",
            *([f"- **Review:** [Play this short]({c['review_url']})\n"] if c.get("review_url") else []),
            *([f"- **YouTube review:** [Play the bleeped version]({c['youtube_review_url']})\n"] if c.get("youtube_review_url") else []),
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


def stage(week, week_path):
    """Copy the week's files into .upload-tmp/ (chrome-devtools-axi only uploads from inside the repo) and write posts.json."""
    if any(c.get("spare") for c in week):
        raise ValueError("Choose the approved dated clips and remove spares before staging")
    kit_text = open(os.path.splitext(week_path)[0] + "-kit.md", encoding="utf-8").read()
    os.makedirs(os.path.join(REPO, ".upload-tmp"), exist_ok=True)
    posts = []
    # only the dated slot sections ("Wed Nov 18: #21 ..."); hand-written notes after them are skipped
    for section in [s for s in re.split(r"\n## ", kit_text)[1:] if re.match(r"\w{3} \w{3} \d{1,2}: #\d+ ", s)]:
        n = int(re.search(r"#(\d+)", section).group(1))
        x_text, title, desc = re.findall(r"```text\n(.*?)\n```", section, re.S)
        c = next(c for c in week if c["n"] == n)
        x_file, yt_file = files_for(c)
        shutil.copy(x_file, os.path.join(REPO, ".upload-tmp", f"x-{n:02d}.mp4"))
        shutil.copy(yt_file, os.path.join(REPO, ".upload-tmp", f"yt-{n:02d}.mp4"))
        posts.append({"n": n, "post_on": c["post_on"], "x": x_text, "title": title, "desc": desc})
    assert sorted(p["n"] for p in posts) == sorted(c["n"] for c in week), "kit and week file list different clips"
    json.dump(posts, open(os.path.join(REPO, ".upload-tmp", "posts.json"), "w"), indent=1, ensure_ascii=False)
    print(f"staged {len(posts)} posts in .upload-tmp/ (delete it when done)")


if __name__ == "__main__":
    cmd, path = sys.argv[1], sys.argv[2]
    week = json.load(open(path, encoding="utf-8"))
    {"render": lambda: render(week), "kit": lambda: kit(week, path), "stage": lambda: stage(week, path)}[cmd]()
