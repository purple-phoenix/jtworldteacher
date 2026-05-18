#!/usr/bin/env bash
# Batch-process X Spaces: download, transcribe, and stage catalog entries.
#
# Usage:
#   ./process-spaces.sh <url> [<url> ...]
#   ./process-spaces.sh -f urls.txt   # one URL per line, # for comments
#
# For each URL:
#   1. Resolve via yt-dlp → get Space ID, title, upload date
#   2. Skip if audio already present in catalog/spaces/audio/
#   3. Download m4a as YYYY-MM-DD-slug.m4a
#   4. Convert to 16kHz mono WAV
#   5. Transcribe with whisper-cpp large-v3-turbo → .txt + .vtt
#   6. Delete the intermediate WAV
#   7. Write/refresh a stub post file in catalog/posts/
#
# Requires: yt-dlp, ffmpeg, whisper-cli, and the model file at
#   ~/.whisper-models/ggml-large-v3-turbo.bin

set -euo pipefail

CATALOG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUDIO_DIR="$CATALOG_ROOT/spaces/audio"
TRANSCRIPT_DIR="$CATALOG_ROOT/spaces/transcripts"
POSTS_DIR="$CATALOG_ROOT/posts"
MODEL="$HOME/.whisper-models/ggml-large-v3-turbo.bin"

mkdir -p "$AUDIO_DIR" "$TRANSCRIPT_DIR" "$POSTS_DIR"

[[ -f "$MODEL" ]] || { echo "Missing whisper model at $MODEL"; exit 1; }
for cmd in yt-dlp ffmpeg whisper-cli; do
  command -v "$cmd" >/dev/null || { echo "Missing: $cmd (install with brew)"; exit 1; }
done

# --- args ---
urls=()
if [[ "${1:-}" == "-f" ]]; then
  [[ -n "${2:-}" ]] || { echo "Usage: $0 -f urls.txt"; exit 1; }
  while IFS= read -r line; do
    line="${line%%#*}"; line="${line## }"; line="${line%% }"
    [[ -n "$line" ]] && urls+=("$line")
  done < "$2"
else
  urls=("$@")
fi
[[ ${#urls[@]} -gt 0 ]] || { echo "No URLs given"; exit 1; }

# --- slugify ---
slugify() {
  echo "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' \
    | cut -c1-60
}

# --- main loop ---
for url in "${urls[@]}"; do
  echo "=== $url"

  meta=$(yt-dlp --print "%(id)s|%(title)s|%(upload_date)s" --skip-download "$url" 2>/dev/null | tail -1)
  IFS='|' read -r space_id title upload_date <<< "$meta"
  [[ -n "$space_id" ]] || { echo "  ! could not resolve, skipping"; continue; }

  date_iso="${upload_date:0:4}-${upload_date:4:2}-${upload_date:6:2}"
  slug=$(slugify "$title")
  base="${date_iso}-${slug}"
  m4a="$AUDIO_DIR/${base}.m4a"
  wav="$AUDIO_DIR/${base}.wav"
  txt="$TRANSCRIPT_DIR/${base}.txt"
  post="$POSTS_DIR/${base}-space.md"

  echo "  ID:    $space_id"
  echo "  Date:  $date_iso"
  echo "  Title: $title"
  echo "  Slug:  $base"

  # 1. download
  if [[ -f "$m4a" ]]; then
    echo "  audio: already downloaded, skipping"
  else
    echo "  audio: downloading..."
    yt-dlp -q -o "$m4a" "$url"
  fi

  # 2. transcribe
  if [[ -f "$txt" ]]; then
    echo "  transcript: already exists, skipping"
  else
    echo "  transcript: converting + transcribing..."
    ffmpeg -y -loglevel error -i "$m4a" -ar 16000 -ac 1 -c:a pcm_s16le "$wav"
    whisper-cli -m "$MODEL" -f "$wav" -otxt -ovtt -of "$TRANSCRIPT_DIR/${base}" >/dev/null 2>&1
    rm -f "$wav"
  fi

  # 3. stub catalog post (only if missing — never overwrite human edits)
  if [[ ! -f "$post" ]]; then
    bytes=$(stat -f "%z" "$m4a")
    cat > "$post" <<EOF
---
date: ${date_iso}
author: "@McCarthy_JT"
type: space
space_id: ${space_id}
space_url: https://x.com/i/spaces/${space_id}
space_title: "$(echo "$title" | sed 's/"/\\"/g')"
audio: ../spaces/audio/${base}.m4a
audio_bytes: ${bytes}
transcript: ../spaces/transcripts/${base}.txt
source_tweet: ${url}
topics: [spaces]
source: yt-dlp
---

# ${title}

**X Space**, ${date_iso}.

[Listen on X](https://x.com/i/spaces/${space_id}) · audio archived locally at \`catalog/spaces/audio/${base}.m4a\` · transcript at \`catalog/spaces/transcripts/${base}.txt\`.

## Notes

(Add after listening / skimming transcript.)
EOF
    echo "  post:  created $post"
  else
    echo "  post:  already exists, leaving alone"
  fi
done

echo
echo "Done. ${#urls[@]} URL(s) processed."
echo "Add new posts to catalog/README.md by hand, or just open the new files and start annotating."
