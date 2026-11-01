"""Word-level caption timings for a clip, written as a VTT with one word per cue.

whisper.cpp's default word timestamps drift (on clip #1, 18 of 119 words started inside a pause).
DTW token timestamps (needs --no-flash-attn) shifted 0.05 s earlier put none in a pause. Any word
that still lands in a detected pause is moved to the end of that pause.

usage: python3 -I align_words.py clip.m4a out.vtt
"""
import json
import os
import re
import subprocess
import sys
import tempfile

MODEL = os.path.expanduser("~/.whisper-models/ggml-large-v3-turbo.bin")
SHIFT = -0.05


def fmt(t):
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def main(audio, out):
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", audio, "-ar", "16000", "-ac", "1",
                        "-c:a", "pcm_s16le", wav], check=True)
        subprocess.run(["whisper-cli", "-m", MODEL, "-f", wav, "-dtw", "large.v3.turbo", "-nfa", "-ojf",
                        "-of", os.path.join(tmp, "w"), "-np"], check=True, capture_output=True)
        data = json.load(open(os.path.join(tmp, "w.json"), encoding="utf-8"))
        log = subprocess.run(["ffmpeg", "-nostdin", "-i", wav, "-af", "silencedetect=noise=-35dB:d=0.15", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
    pauses = list(zip(map(float, re.findall(r"silence_start: ([0-9.]+)", log)),
                      map(float, re.findall(r"silence_end: ([0-9.]+)", log))))

    words = []
    for seg in data["transcription"]:
        for tok in seg["tokens"]:
            text = tok["text"]
            if text.startswith("[_") or not text.strip():
                continue
            if text.startswith(" ") or not words:
                words.append([tok["t_dtw"] / 100 + SHIFT, text.strip()])
            else:
                words[-1][1] += text
    last = 0.0
    for w in words:
        for a, b in pauses:
            if a + 0.03 < w[0] < b:
                w[0] = b
        w[0] = max(w[0], last)
        last = w[0]

    with open(out, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, (start, text) in enumerate(words):
            end = words[i + 1][0] if i + 1 < len(words) else start + 0.6
            f.write(f"{fmt(start)} --> {fmt(max(end, start + 0.05))}\n{text}\n\n")
    print(f"wrote {out}: {len(words)} words")


if __name__ == "__main__":
    main(*sys.argv[1:3])
