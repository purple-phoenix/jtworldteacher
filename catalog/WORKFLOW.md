# Catalog workflow

How to add new material to the catalog. Skim this when you (or future Claude) sit down to add a batch of posts or Spaces.

## TL;DR

| Material | Where it goes | How to add |
|----------|---------------|------------|
| Tweet screenshot | `posts/YYYY-MM-DD-slug.md` + image in `media/` | Paste screenshot in chat → Claude writes the entry |
| X Space (recorded) | `spaces/audio/` + `spaces/transcripts/` + a `posts/` stub | `yt-dlp` → `whisper-cpp` (see below) |
| X Space (live, capture yourself) | same as above | BlackHole + QuickTime/Audio Hijack → whisper-cpp |

---

## 1. Adding a tweet from a screenshot

You: paste the screenshot in the chat.

Claude:
1. Reads the image.
2. Copies it into `catalog/media/YYYY-MM-DD-slug.png`.
3. Creates `catalog/posts/YYYY-MM-DD-slug.md` with frontmatter (date, type, engagement, topics) + tweet text + media transcription + notes.
4. Cross-links related posts via `[[slug]]`.

Date convention: use the date shown in the X UI ("May 8" with no year = current year, since X omits the year only for posts in the same calendar year as today).

---

## 2. Downloading an X Space with yt-dlp

**Prerequisite (one-time):**

```bash
brew install yt-dlp ffmpeg
```

**Run:**

```bash
cd catalog/spaces/audio
yt-dlp -o "%(id)s-%(title)s.%(ext)s" "https://x.com/i/spaces/<SPACE_ID>"
```

The Space ID is the bit after `/spaces/` in the URL (strip `?s=20` and any other params). Example: `https://x.com/i/spaces/1nKOLEXAlPkGR?s=20` → ID is `1nKOLEXAlPkGR`.

**Then rename** to the catalog convention so it sorts with everything else:

```bash
mv "<SPACE_ID>-<title>.m4a" "YYYY-MM-DD-slug.m4a"
```

(Use the upload date `yt-dlp` reports: `yt-dlp --print "%(upload_date)s" --skip-download "<URL>"`.)

### When it works

- The host enabled "record" before going live (so X archived the audio).
- The Space's audio chunks are still on `prod-fastly-us-east-1.video.pscp.tv` (X's CDN). They generally persist for at least weeks, sometimes longer.

### When it doesn't

- **HTTP 401/403** — Space requires auth. Get your X cookies (Chrome/Firefox extension "Get cookies.txt LOCALLY"), save as `cookies.txt`, re-run with `--cookies cookies.txt`.
- **"Space is no longer available"** — host didn't record, or audio was purged. Nothing recovers this.
- **`yt-dlp` extractor errors** — X changes their APIs occasionally. Update with `brew upgrade yt-dlp` first.

### Batch-downloading multiple Spaces

```bash
cd catalog/spaces/audio
cat > urls.txt <<'EOF'
https://x.com/i/spaces/1nKOLEXAlPkGR
https://x.com/i/spaces/1XXXXXXXXXX
https://x.com/i/spaces/1YYYYYYYYYY
EOF
yt-dlp -o "%(upload_date)s-%(id)s-%(title)s.%(ext)s" -a urls.txt
```

### Finding Space IDs you don't already have

You can usually pull them from JT's profile — every Space post links to the Space URL. The quote-tweets we have in the catalog (e.g. [[posts/2026-05-07-ufox-crusade]] linking to `x.com/i/spaces/1Oxwb…`) all contain Space IDs we could try to recover.

---

## 3. Capturing a live Space (host didn't record)

```bash
brew install blackhole-2ch
```

1. System Settings → Sound → set output to **BlackHole 2ch** (or use a Multi-Output Device so you can also still hear it).
2. QuickTime → File → New Audio Recording → set input to **BlackHole 2ch**.
3. Join the Space, record, save as `.m4a` in `catalog/spaces/audio/`.
4. Rename to `YYYY-MM-DD-slug.m4a`.

For a more polished workflow, **Audio Hijack** (paid) handles routing + recording in one app.

---

## 4. Transcribing with whisper-cpp

**Prerequisite (one-time):**

```bash
brew install whisper-cpp
```

You also need a model file. The recommended balance of quality + speed for an M-series Mac is **large-v3-turbo** (~1.5 GB):

```bash
mkdir -p ~/.whisper-models
cd ~/.whisper-models
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

Alternatives:
- `ggml-large-v3.bin` (~3 GB) — best quality, ~3-5x slower than turbo.
- `ggml-medium.en.bin` (~1.5 GB) — English-only, slightly worse than large.
- `ggml-base.en.bin` (~150 MB) — fast but noticeably more errors on jargon (RV, archons, etc.).

**Run:**

```bash
cd catalog/spaces
whisper-cli \
  -m ~/.whisper-models/ggml-large-v3-turbo.bin \
  -f audio/YYYY-MM-DD-slug.m4a \
  -otxt -ovtt \
  -of transcripts/YYYY-MM-DD-slug \
  --print-progress
```

- `-otxt` → plain `.txt`
- `-ovtt` → `.vtt` with timestamps (useful for jumping around the audio)
- `-of <prefix>` → output filename without extension

Then wrap the `.txt` content in the [transcript frontmatter template](spaces/README.md#transcript-frontmatter) and save as `transcripts/YYYY-MM-DD-slug.md`.

### Speeding it up

Whisper-cpp uses Metal automatically on Apple Silicon. For a 90-min Space on an M1/M2/M3, expect:
- turbo: ~10-20 min
- large-v3: ~40-90 min
- base.en: ~2-5 min

### Speaker labels

Whisper-cpp doesn't do diarization (who said what). If you need that, run the audio through **pyannote-audio** separately and merge, or use a hosted service (AssemblyAI, Deepgram). For a single-host Space, label JT manually for any spots where someone else speaks.

---

## 5. Updating the index

After adding any new post or transcript, add a row to the table in `catalog/README.md`. Keep it sorted newest-first.

---

## File layout (full)

```
catalog/
├── README.md             # index of posts + topic overview
├── WORKFLOW.md           # this file
├── posts/
│   └── YYYY-MM-DD-slug.md
├── media/
│   └── YYYY-MM-DD-slug.png
└── spaces/
    ├── README.md         # space-specific tooling notes
    ├── audio/            # git-ignored
    │   └── YYYY-MM-DD-slug.m4a
    └── transcripts/      # tracked in git
        └── YYYY-MM-DD-slug.md
```
