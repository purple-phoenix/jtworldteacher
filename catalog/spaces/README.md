# X Spaces

Audio recordings and transcripts of JT's X Spaces.

## Structure

- `audio/` — raw recordings: `YYYY-MM-DD-slug.m4a` (or `.mp3` / `.wav`). Large files — git-ignored by default.
- `transcripts/` — text transcripts: `YYYY-MM-DD-slug.md`. These ARE tracked in git — they're the searchable record.
- One markdown entry per Space lives in `../posts/` alongside the regular posts (the poster announcement post links to the Space; the transcript file is the content).

## Naming

Match the slug to the corresponding post entry in `catalog/posts/`. Example: poster `posts/2026-05-08-trvxn-defining-remote-viewing.md` ↔ transcript `spaces/transcripts/2026-05-09-trvxn-defining-remote-viewing.md` (note: poster *announces*, transcript date = when Space actually happened).

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

**MacWhisper** (free, runs locally on Apple Silicon): drag the audio file in, export to `.txt` or `.srt`. Copy into `transcripts/<slug>.md` and wrap with the [frontmatter template](#transcript-frontmatter).

Or via CLI with `whisper.cpp`:

```bash
brew install whisper-cpp
whisper-cli -m ~/path/to/ggml-large-v3.bin -f audio/<slug>.m4a -otxt
```

## Transcript frontmatter

```markdown
---
date: YYYY-MM-DD            # date the Space aired
space_id: 1XXXXXXXXXX        # X Space ID
space_url: https://x.com/i/spaces/...
title: ""
host: "@McCarthy_JT"
co_hosts: []
speakers: []
duration_minutes:
source: yt-dlp | live-capture | host-upload
transcribed_with: macwhisper | whisper-cpp | manual
related_post: ../posts/YYYY-MM-DD-slug.md   # the announcement post, if cataloged
topics: []
---

# Title

## Summary

(1-2 paragraph human summary — the part you'll actually re-read)

## Notable quotes

> "…"
> — JT, 12:34

## Full transcript

…
```
