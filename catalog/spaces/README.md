# X Spaces

Audio recordings and transcripts of JT's X Spaces.

## Structure

- `audio/` — raw recordings: `YYYY-MM-DD-slug.m4a` (or `.mp3` / `.wav`). Large files — git-ignored by default.
- `transcripts/` — plain-text and timed transcripts: `YYYY-MM-DD-slug.txt` and `YYYY-MM-DD-slug.vtt`. These ARE tracked in git — they're the searchable record.
- One markdown entry per Space lives in `../posts/` alongside the regular posts and links to the audio and transcript.

## Naming

Match the slug to the corresponding Space entry in `catalog/posts/`. For example, `posts/2026-09-16-the-world-tree-and-the-eclipse-in-leo-space.md` links to `spaces/transcripts/2026-09-16-the-world-tree-and-the-eclipse-in-leo.txt` and its matching `.vtt` file.

## Getting audio

### Already-aired Space with a saved recording

```bash
brew install yt-dlp ffmpeg   # one-time
yt-dlp -o "audio/%(upload_date)s-%(title)s.%(ext)s" "https://x.com/i/spaces/<SPACE_ID>"
```

If you hit auth errors, export your X cookies (browser extension "Get cookies.txt LOCALLY") and add `--cookies ~/path/to/cookies.txt`.

Spaces only persist if the **host toggled "record" before going live**. If not, the audio is gone — no tool recovers it.

### Capturing a Space live

1. macOS: route Space audio to a virtual input — install **BlackHole** (`brew install blackhole-2ch`) or use **Audio Hijack** (paid, easiest).
2. Record in QuickTime / Audio Hijack while listening live.
3. Save as `.m4a` or `.mp3` in `audio/`.

## Transcribing

**MacWhisper** (free, runs locally on Apple Silicon): drag the audio file in and export plain text plus a timed transcript. Save them under `transcripts/` using the naming convention above.

Or via CLI with `whisper.cpp` (convert first; this `whisper-cli` build requires WAV input):

```bash
brew install whisper-cpp ffmpeg
ffmpeg -y -i audio/<slug>.m4a -ar 16000 -ac 1 -c:a pcm_s16le audio/<slug>.wav
whisper-cli -m ~/.whisper-models/ggml-large-v3-turbo.bin \
  -f audio/<slug>.wav -otxt -ovtt -of transcripts/<slug>
rm audio/<slug>.wav
```
