#!/usr/bin/env bash
# Transcribe every audio file in catalog/spaces/audio/ that lacks a matching transcript.
# Runs sequentially (whisper is GPU-bound — parallelizing on a single GPU hurts).
#
# Usage:
#   bash transcribe-pending.sh         # process whatever's there now and exit
#   bash transcribe-pending.sh --watch # loop forever until killed; processes new files as they appear

set -euo pipefail

CATALOG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUDIO_DIR="$CATALOG_ROOT/spaces/audio"
TRANSCRIPT_DIR="$CATALOG_ROOT/spaces/transcripts"
MODEL="$HOME/.whisper-models/ggml-large-v3-turbo.bin"
mkdir -p "$TRANSCRIPT_DIR"

[[ -f "$MODEL" ]] || { echo "Missing whisper model at $MODEL"; exit 1; }
for cmd in ffmpeg whisper-cli; do
  command -v "$cmd" >/dev/null || { echo "Missing: $cmd"; exit 1; }
done

watch_mode=false
[[ "${1:-}" == "--watch" ]] && watch_mode=true

process_one() {
  local m4a="$1"
  local base
  base="$(basename "$m4a" .m4a)"
  local wav="$AUDIO_DIR/${base}.wav"
  local txt="$TRANSCRIPT_DIR/${base}.txt"

  if [[ -f "$txt" ]]; then return; fi
  if [[ "$m4a" == *.part || "$m4a" == *.partial ]]; then return; fi
  # skip files that are likely still being written (mtime within last 5s)
  if [[ -n "$(find "$m4a" -newermt '-5 seconds' 2>/dev/null)" ]]; then
    echo "[$base] still being written, skipping this pass"
    return
  fi

  echo "[$base] converting → 16kHz mono WAV"
  ffmpeg -y -loglevel error -i "$m4a" -ar 16000 -ac 1 -c:a pcm_s16le "$wav"

  echo "[$base] transcribing..."
  whisper-cli -m "$MODEL" -f "$wav" -otxt -ovtt -of "$TRANSCRIPT_DIR/${base}" >/dev/null 2>&1

  rm -f "$wav"
  echo "[$base] done → $(basename "$txt") $(du -h "$txt" | cut -f1)"
}

run_pass() {
  local did_work=false
  for m4a in "$AUDIO_DIR"/*.m4a; do
    [[ -f "$m4a" ]] || continue
    local base
    base="$(basename "$m4a" .m4a)"
    [[ -f "$TRANSCRIPT_DIR/${base}.txt" ]] && continue
    did_work=true
    process_one "$m4a"
  done
  $did_work
}

if $watch_mode; then
  echo "watcher: starting (Ctrl-C or kill PID to stop)"
  while true; do
    run_pass || true
    # Exit cleanly if a stop signal file is present
    if [[ -f "$AUDIO_DIR/.stop-transcriber" ]]; then
      echo "watcher: stop flag found, doing final pass and exiting"
      run_pass || true
      rm -f "$AUDIO_DIR/.stop-transcriber"
      break
    fi
    sleep 10
  done
else
  run_pass || true
fi
