#!/usr/bin/env bash
# Download ONE X Space (no transcription).
# Idempotent: skips if the audio file already exists.
#
# Usage:
#   bash download-space.sh <url>

set -euo pipefail

[[ -n "${1:-}" ]] || { echo "Usage: $0 <url>"; exit 1; }
url="$1"

CATALOG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUDIO_DIR="$CATALOG_ROOT/spaces/audio"
POSTS_DIR="$CATALOG_ROOT/posts"
mkdir -p "$AUDIO_DIR" "$POSTS_DIR"

slugify() {
  echo "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' \
    | cut -c1-60
}

meta=$(yt-dlp --print "%(id)s|%(title)s|%(upload_date)s" --skip-download "$url" 2>/dev/null | tail -1)
IFS='|' read -r space_id title upload_date <<< "$meta"
[[ -n "$space_id" ]] || { echo "[$url] could not resolve, skipping"; exit 0; }

date_iso="${upload_date:0:4}-${upload_date:4:2}-${upload_date:6:2}"
slug=$(slugify "$title")
base="${date_iso}-${slug}"
m4a="$AUDIO_DIR/${base}.m4a"
post="$POSTS_DIR/${base}-space.md"

if [[ -f "$m4a" ]]; then
  echo "[$base] audio already present, skipping download"
else
  echo "[$base] downloading..."
  yt-dlp -q -o "$m4a" "$url"
  echo "[$base] downloaded $(du -h "$m4a" | cut -f1)"
fi

# Stub catalog post — only created on first run, never overwrites human edits.
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

[Listen on X](https://x.com/i/spaces/${space_id}) · audio at \`catalog/spaces/audio/${base}.m4a\` · transcript at \`catalog/spaces/transcripts/${base}.txt\`.

## Notes

(Add after listening / skimming transcript.)
EOF
  echo "[$base] stub post created"
fi
