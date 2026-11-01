"""Render a vertical (1080x1920) short from a clip's audio and word-level VTT.

Layout: show art with a slow push-in, headline at the top, word-by-word captions with the
spoken word highlighted, speaker name, live waveform and handle. Frames are drawn with PIL and
piped to ffmpeg (this ffmpeg build has no libass/drawtext).

usage: python3 -I render_short.py --audio clip.m4a --words words.vtt --headline "..." \
         --speaker "JT McCarthy" --art art.png --out short.mp4
"""
import argparse
import os
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
PARCHMENT = (232, 220, 193)
GOLD = (242, 193, 78)
WHITE = (255, 255, 255)
CASLON = "/System/Library/Fonts/Supplemental/BigCaslon.ttf"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"  # 8 = Heavy, 2 = Demi Bold


def ts(x):
    h, m, s = x.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def read_words(path):
    words, cur = [], None
    for line in open(path, encoding="utf-8"):
        m = re.match(r"(\S+) --> (\S+)", line)
        if m:
            cur = [ts(m.group(1)), ts(m.group(2))]
        elif cur and line.strip():
            words.append((cur[0], cur[1], line.strip()))
            cur = None
    return words


def chunk_words(words, font, max_words=3, max_width=940):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    chunks, cur = [], []
    for w in words:
        text = " ".join(display(x[2]) for x in cur + [w])
        if cur and (len(cur) >= max_words or d.textlength(text, font=font) > max_width):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[,.?!;:]$", w[2]):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


PROFANE = re.compile(r"^(shit|shitty|bullshit|fuck|fucking|fucked|fucker|motherfucker|goddamn|bitch|asshole)$", re.I)
BLEEP = False


def is_profane(word):
    return bool(PROFANE.match(re.sub(r"[^A-Za-z]", "", word)))


def display(word):
    word = re.sub(r"[,.;:]+$", "", word)
    if BLEEP and is_profane(word):
        core = re.sub(r"[^A-Za-z]", "", word)
        word = core[0] + "*" * (len(core) - 1) + word[len(core):] if word.startswith(core) else core[0] + "***"
    return word.upper()


def text_w(draw, s, font):
    return draw.textlength(s, font=font)


def wrap(draw, text, font, width):
    """Fewest lines that fit, with the break chosen so the lines are as even as possible."""
    words = text.split()
    for n in (1, 2, 3):
        best = None
        if n == 1:
            cands = [[words]]
        elif n == 2:
            cands = [[words[:i], words[i:]] for i in range(1, len(words))]
        else:
            cands = [[words[:i], words[i:j], words[j:]] for i in range(1, len(words)) for j in range(i + 1, len(words))]
        for c in cands:
            widths = [text_w(draw, " ".join(l), font) for l in c]
            if max(widths) <= width and (best is None or max(widths) < best[0]):
                best = (max(widths), [" ".join(l) for l in c])
        if best:
            return best[1]
    return [text]


def static_layer(headline, speaker, tag=""):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    brand = ImageFont.truetype(CASLON, 46)
    label = "P E A K   M I N D"
    d.text(((W - text_w(d, label, brand)) / 2, 150), label, font=brand, fill=PARCHMENT)
    d.line([(W / 2 - 170, 222), (W / 2 + 170, 222)], fill=PARCHMENT, width=3)
    head = ImageFont.truetype(CASLON, 84)
    y = 262
    for line in wrap(d, headline, head, 920)[:3]:
        x = (W - text_w(d, line, head)) / 2
        d.text((x + 3, y + 4), line, font=head, fill=(0, 0, 0, 200))
        d.text((x, y), line, font=head, fill=PARCHMENT)
        y += 100
    spk = ImageFont.truetype(AVENIR, 42, index=2)
    d.text(((W - text_w(d, speaker, spk)) / 2, 1318), speaker, font=spk, fill=PARCHMENT)
    if tag:
        small = ImageFont.truetype(AVENIR, 30, index=5)
        d.text(((W - text_w(d, tag, small)) / 2, 1376), tag, font=small, fill=PARCHMENT + (210,))
    handle = ImageFont.truetype(AVENIR, 36, index=2)
    d.text(((W - text_w(d, "@PeakMindShow", handle)) / 2, 1560), "@PeakMindShow", font=handle, fill=PARCHMENT)
    return layer


def caption_layer(chunk, active, font):
    layer = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    words = [display(w[2]) for w in chunk]
    space = text_w(d, " ", font)
    lines, cur = [], []
    for i, w in enumerate(words):
        trial = cur + [(i, w)]
        if cur and sum(text_w(d, x, font) for _, x in trial) + space * (len(trial) - 1) > 960:
            lines.append(cur)
            cur = [(i, w)]
        else:
            cur = trial
    lines.append(cur)
    y = 200 - len(lines) * 62
    for line in lines:
        total = sum(text_w(d, w, font) for _, w in line) + space * (len(line) - 1)
        x = (W - total) / 2
        for i, w in line:
            d.text((x, y), w, font=font, fill=GOLD if i == active else WHITE, stroke_width=9, stroke_fill=(0, 0, 0))
            x += text_w(d, w, font) + space
        y += 124
    return layer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--headline", required=True)
    ap.add_argument("--speaker", default="JT McCarthy")
    ap.add_argument("--art", required=True, help='image path, or "none" for the type-only background')
    ap.add_argument("--tag", default="", help='small line under the speaker, e.g. "Recorded live on X · May 8, 2026"')
    ap.add_argument("--out", required=True)
    ap.add_argument("--bleep", action="store_true", help="bleep profanity in the audio and mask it in the captions")
    a = ap.parse_args()
    global BLEEP
    BLEEP = a.bleep

    pcm = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", a.audio, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    samples = np.frombuffer(pcm, dtype=np.float32).copy()
    duration = len(samples) / 48000
    n_frames = int(duration * FPS)
    audio_in = a.audio
    if a.bleep:
        for start, end, word in read_words(a.words):
            if is_profane(word):
                i0, i1 = int(start * 48000), int(min(end, start + 0.6) * 48000)
                tt = np.arange(i1 - i0) / 48000
                samples[i0:i1] = 0.18 * np.sin(2 * np.pi * 1000 * tt)
        audio_in = a.out + ".bleeped.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", "-",
                        audio_in], input=samples.tobytes(), check=True)

    plain = a.art == "none"
    if plain:
        rng = np.random.default_rng(7)
        base = np.empty((H, W, 3), dtype=np.float32)
        base[...] = (24, 22, 30)
        base += rng.normal(0, 6, (H, W, 1))
        yy = np.linspace(-1, 1, H)[:, None]
        xx = np.linspace(-1, 1, W)[None, :]
        base *= (1 - 0.35 * (xx ** 2 + yy ** 2))[..., None]
        bg = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
        d0 = ImageDraw.Draw(bg)
        d0.rectangle([44, 44, W - 44, H - 44], outline=PARCHMENT + (150,), width=3)
        d0.rectangle([58, 58, W - 58, H - 58], outline=PARCHMENT + (90,), width=1)
    else:
        art = Image.open(a.art).convert("RGB")
        art = art.resize((2400, 2400), Image.LANCZOS)
    static = static_layer(a.headline, a.speaker, a.tag)
    cap_font = ImageFont.truetype(AVENIR, 104, index=8)

    # fillers stay in the audio but not in the captions
    words = [w for w in read_words(a.words) if w[2] and not re.match(r"^(um+|uh+|erm|hmm)[,.]?$", w[2], re.I)]
    chunks = chunk_words(words, cap_font)
    spans = []  # (start, end, chunk index): a chunk stays up until the next starts, unless there is a long pause
    for k, c in enumerate(chunks):
        start = c[0][0]
        end = chunks[k + 1][0][0] if k + 1 < len(chunks) else c[-1][1] + 0.6
        end = min(end, c[-1][1] + 1.0)
        spans.append((start, end, k))
    cache = {}

    # darkening gradient: heavier behind the caption band
    grad = np.full((H, 1), 0.58, dtype=np.float32)
    for y in range(H):
        if 860 <= y <= 1500:
            grad[y] = 0.42
    grad = np.repeat(grad, W, axis=1)[..., None]

    bands = np.geomspace(60, 6000, 41)
    smooth = np.zeros(40)
    enc = subprocess.Popen(
        ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", audio_in, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", a.out],
        stdin=subprocess.PIPE)
    for f in range(n_frames):
        t = f / FPS
        if plain:
            frame = bg.copy()
        else:
            frame = None
        z = 1.0 + 0.10 * (t / duration)
        hs = 1900 / z  # illustrated area is y 0..~1944 of the 2400px upscale
        ws = hs * W / H
        cx, cy = 1200, 990
        box = (cx - ws / 2, cy - hs / 2, cx + ws / 2, cy + hs / 2)
        if frame is None:
            frame = art.resize((W, H), Image.BILINEAR, box=box)
            arr = (np.asarray(frame, dtype=np.float32) * grad).astype(np.uint8)
            frame = Image.fromarray(arr).convert("RGBA")
        frame.alpha_composite(static)

        for start, end, k in spans:
            if start <= t < end:
                active = max(i for i, w in enumerate(chunks[k]) if w[0] <= t or i == 0)
                key = (k, active)
                if key not in cache:
                    cache[key] = caption_layer(chunks[k], active, cap_font)
                frame.alpha_composite(cache[key], (0, 900))
                break

        # waveform: 40 log-spaced bands from the last 2048 samples, mirrored around a centre line
        i = int(t * 48000)
        win = samples[max(0, i - 2048):i]
        if len(win) == 2048:
            spec = np.abs(np.fft.rfft(win * np.hanning(2048)))
            freqs = np.fft.rfftfreq(2048, 1 / 48000)
            mags = np.array([spec[(freqs >= lo) & (freqs < hi)].mean() if ((freqs >= lo) & (freqs < hi)).any() else 0
                             for lo, hi in zip(bands[:-1], bands[1:])])
            level = np.clip(np.log1p(mags) / 4.0, 0, 1)
        else:
            level = np.zeros(40)
        smooth = np.maximum(level, smooth * 0.82)
        d = ImageDraw.Draw(frame)
        bw, gap = 12, 7
        x0 = (W - (40 * bw + 39 * gap)) / 2
        for b in range(40):
            h = 6 + smooth[b] * 80
            x = x0 + b * (bw + gap)
            d.rounded_rectangle([x, 1480 - h / 2, x + bw, 1480 + h / 2], radius=5, fill=PARCHMENT + (230,))
        d.rectangle([0, H - 12, W * t / duration, H], fill=GOLD + (255,))
        enc.stdin.write(frame.convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()
    if a.bleep:
        os.remove(audio_in)
    print("wrote", a.out, f"{duration:.1f}s", n_frames, "frames")


if __name__ == "__main__":
    main()
