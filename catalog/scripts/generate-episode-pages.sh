#!/usr/bin/env bash
# Generate site/src/content/episodes/<slug>.md for every audio file that
# doesn't already have a site episode page. Pulls metadata from:
#   - the audio file (size, duration via ffprobe)
#   - the catalog/posts/<slug>-space.md stub (title, space_id, space_url)
#
# Existing episode files are NEVER overwritten — hand-written show notes are safe.

set -euo pipefail

CATALOG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_ROOT="$(cd "$CATALOG_ROOT/../site" && pwd)"
AUDIO_DIR="$CATALOG_ROOT/spaces/audio"
POSTS_DIR="$CATALOG_ROOT/posts"
EPISODES_DIR="$SITE_ROOT/src/content/episodes"
R2_DOMAIN="https://media.jtworldteacher.com"

mkdir -p "$EPISODES_DIR"

frontmatter_get() {
  # $1 = file, $2 = key. Returns value (stripped of quotes).
  grep -E "^${2}:" "$1" 2>/dev/null | head -1 | sed -E "s/^${2}:[[:space:]]*//; s/^\"//; s/\"$//"
}

PATH=/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin
created=0
skipped_existing=0
skipped_missing_stub=0

for m4a in "$AUDIO_DIR"/*.m4a; do
  base="$(basename "$m4a" .m4a)"
  date_iso="${base:0:10}"
  episode_md="$EPISODES_DIR/${base}.md"
  stub="$POSTS_DIR/${base}-space.md"

  if [[ -f "$episode_md" ]]; then
    skipped_existing=$((skipped_existing+1))
    continue
  fi

  # Also skip if an episode file with the same date prefix already exists under
  # a *different* slug — happens for the 3 hand-written episodes that used
  # cleaner slugs (e.g. saturn-neptune vs saturnneptune).
  if compgen -G "$EPISODES_DIR/${date_iso}-*.md" > /dev/null; then
    skipped_existing=$((skipped_existing+1))
    continue
  fi

  if [[ ! -f "$stub" ]]; then
    echo "  ! [${base}] stub catalog post missing — skipping"
    skipped_missing_stub=$((skipped_missing_stub+1))
    continue
  fi

  title="$(frontmatter_get "$stub" 'space_title')"
  space_id="$(frontmatter_get "$stub" 'space_id')"
  space_url="$(frontmatter_get "$stub" 'space_url')"
  bytes="$(stat -f "%z" "$m4a")"
  secs="$(ffprobe -i "$m4a" -show_entries format=duration -v quiet -of csv="p=0" 2>/dev/null | cut -d. -f1)"
  hh=$((secs/3600)); mm=$(((secs%3600)/60)); ss=$((secs%60))
  duration=$(printf "%d:%02d:%02d" "$hh" "$mm" "$ss")

  pretty_date=$(date -j -f "%Y-%m-%d" "$date_iso" "+%B %-d, %Y" 2>/dev/null || echo "$date_iso")

  cat > "$episode_md" <<EOF
---
title: "$(echo "$title" | sed 's/"/\\"/g')"
pubDate: ${date_iso}
description: "Originally aired as an X Space on ${pretty_date}. Detailed show notes coming."
audioUrl: "${R2_DOMAIN}/episodes/${base}.m4a"
audioLength: ${bytes}
audioType: "audio/mp4"
duration: "${duration}"
durationSeconds: ${secs}
episodeType: "full"
explicit: false
draft: false
spaceUrl: "${space_url}"
spaceId: "${space_id}"
---

## About this episode

Originally aired as an X Space on ${pretty_date}. Listen to the live version on [X](${space_url}).

Detailed show notes are forthcoming.
EOF
  created=$((created+1))
  echo "  + [${base}]"
done

echo
echo "created: $created  skipped (already exists): $skipped_existing  skipped (no stub): $skipped_missing_stub"
