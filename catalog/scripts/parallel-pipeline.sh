#!/usr/bin/env bash
# Parallel pipeline for processing a queue of X Space URLs.
#   - Downloads N URLs concurrently (network-bound, parallelizable)
#   - Transcription runs in a watcher loop in parallel — picks up each
#     downloaded audio file as soon as it lands, processes sequentially
#     (whisper is GPU-bound on a single GPU)
#
# Usage:
#   bash parallel-pipeline.sh <queue.txt> [PARALLELISM]
#
# Default PARALLELISM = 4 concurrent downloads.

set -euo pipefail

queue="${1:-}"
[[ -n "$queue" && -f "$queue" ]] || { echo "Usage: $0 <queue.txt> [PARALLELISM]"; exit 1; }
parallel="${2:-4}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CATALOG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AUDIO_DIR="$CATALOG_ROOT/spaces/audio"
mkdir -p "$AUDIO_DIR"

# Clean up any stale stop flag
rm -f "$AUDIO_DIR/.stop-transcriber"

echo "=== parallel pipeline starting"
echo "  queue:       $queue"
echo "  parallelism: $parallel concurrent downloads"
echo

# Start the transcription watcher in the background
bash "$SCRIPT_DIR/transcribe-pending.sh" --watch &
WATCHER_PID=$!
echo "transcriber watcher started (pid $WATCHER_PID)"
echo

# Start downloads in parallel
echo "=== downloading $(grep -cvE '^[[:space:]]*(#|$)' "$queue") URL(s) at parallelism=$parallel"
grep -vE '^[[:space:]]*(#|$)' "$queue" \
  | xargs -n1 -P "$parallel" -I{} bash "$SCRIPT_DIR/download-space.sh" "{}"

echo
echo "=== all downloads complete, signaling watcher to finish"
touch "$AUDIO_DIR/.stop-transcriber"

# Wait for watcher
wait "$WATCHER_PID"
echo
echo "=== pipeline complete"
