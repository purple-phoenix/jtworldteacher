#!/usr/bin/env bash
# Transcribe every audio file in catalog/spaces/audio/ that lacks a matching transcript.
# Runs sequentially (whisper is GPU-bound, parallelizing on a single GPU hurts).
#
# Usage:
#   bash transcribe-pending.sh         # process whatever's there now and exit
#   bash transcribe-pending.sh --watch # loop forever until killed; processes new files as they appear

set -euo pipefail

CATALOG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUDIO_DIR="$CATALOG_ROOT/spaces/audio"
TRANSCRIPT_DIR="$CATALOG_ROOT/spaces/transcripts"
MODEL="${WHISPER_MODEL:-$HOME/.whisper-models/ggml-large-v3-turbo.bin}"
mkdir -p "$TRANSCRIPT_DIR"

[[ -f "$MODEL" ]] || { echo "Missing whisper model at $MODEL"; exit 1; }
for cmd in ffmpeg whisper-cli; do
  command -v "$cmd" >/dev/null || { echo "Missing: $cmd"; exit 1; }
done

watch_mode=false
[[ "${1:-}" == "--watch" ]] && watch_mode=true

# Indexed arrays keep this compatible with macOS Bash 3.2.
failed_files=()
failed_steps=()

record_failure() {
  failed_files+=("$1")
  failed_steps+=("$2")
  echo "[$1] FAILED: $2" >&2
}

process_one() {
  local m4a="$1" final_pass="${2:-false}" base wav txt vtt failed
  base="$(basename "$m4a" .m4a)"
  wav="$AUDIO_DIR/${base}.wav"
  txt="$TRANSCRIPT_DIR/${base}.txt"
  vtt="$TRANSCRIPT_DIR/${base}.vtt"

  for failed in "${failed_files[@]+"${failed_files[@]}"}"; do
    [[ "$failed" == "$base" ]] && return 0
  done
  [[ -s "$txt" && -s "$vtt" ]] && return 0
  # Skip files that are likely still being written (mtime within last 5s).
  if ! $final_pass && [[ -n "$(find "$m4a" -newermt '-5 seconds' 2>/dev/null)" ]]; then
    if $watch_mode; then
      echo "[$base] still being written, skipping this pass"
    else
      record_failure "$base" "file readiness (modified within last 5 seconds; retry when complete)"
    fi
    return 0
  fi

  echo "[$base] converting to 16kHz mono WAV"
  if ! ffmpeg -y -loglevel error -i "$m4a" -ar 16000 -ac 1 -c:a pcm_s16le "$wav"; then
    record_failure "$base" "ffmpeg conversion"
  elif [[ ! -s "$wav" ]]; then
    record_failure "$base" "ffmpeg output (missing or empty WAV)"
  else
    # Discard incomplete output from an earlier run before checking new output.
    rm -f "$txt" "$vtt"
    echo "[$base] transcribing..."
    if ! whisper-cli -m "$MODEL" -f "$wav" -otxt -ovtt -of "$TRANSCRIPT_DIR/${base}"; then
      record_failure "$base" "whisper-cli transcription"
      rm -f "$txt" "$vtt"
    elif [[ ! -s "$txt" || ! -s "$vtt" ]]; then
      record_failure "$base" "whisper-cli output (missing or empty TXT/VTT)"
      rm -f "$txt" "$vtt"
    else
      echo "[$base] done: $(basename "$txt") and $(basename "$vtt")"
    fi
  fi
  rm -f "$wav"
}

run_pass() {
  local m4a
  for m4a in "$AUDIO_DIR"/*.m4a; do
    [[ -f "$m4a" ]] || continue
    process_one "$m4a" "${1:-false}"
  done
}

if $watch_mode; then
  echo "watcher: starting (use .stop-transcriber to finish)"
  while true; do
    run_pass
    if [[ -f "$AUDIO_DIR/.stop-transcriber" ]]; then
      echo "watcher: stop flag found, doing final pass and exiting"
      # Downloads have finished before the pipeline sets the flag. Completed
      # .m4a files may be fresh; do not silently skip them on the last pass.
      run_pass true
      rm -f "$AUDIO_DIR/.stop-transcriber"
      break
    fi
    sleep 10
  done
else
  run_pass
fi

if (( ${#failed_files[@]} )); then
  echo "Transcription failures (${#failed_files[@]}):" >&2
  for ((i=0; i<${#failed_files[@]}; i++)); do
    echo "  ${failed_files[$i]}: ${failed_steps[$i]}" >&2
  done
  exit 1
fi
