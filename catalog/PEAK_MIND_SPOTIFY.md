# Peak Mind weekly Spotify upload kit

This runbook prepares a **local** kit for the captain's manual Spotify for Creators upload. It never uploads to Spotify, R2, or the public site/feed.

Peak Mind is the Wednesday show with JT and his brother Matt. It is not JT's Thursday BoomRoom, a casual Space, or a Space hosted by another account.

## The two judgment gates

Do not automate these decisions:

1. **Select the show.** Decide that the Space is a genuine Peak Mind episode, not merely the latest Space JT linked. If the evidence is ambiguous, stop and ask the captain.
2. **Choose the source cut window.** Listen and use the transcript/waveform to identify the first real program sentence and the end of the spoken close. Remove only demonstrated hold music, pre-show chatter, and dead-air tail. Never cut inside the show.

Everything after those approved inputs is deterministic and handled by `catalog/scripts/prepare_peak_mind_kit.py`.

## 1. Discover and verify candidates (judgment gate)

X's logged-out timeline is not useful. Start signed-in Grok research with no memory or subagents from a disposable directory:

```bash
scratch="$(mktemp -d)"
grok --cwd "$scratch" --no-memory --no-subagents -p \
  'From scratch, find every recorded X Space hosted by @McCarthy_JT after <LAST_DATE> through today. Identify Wednesday Peak Mind episodes with Matt; distinguish BoomRoom, casual/test Spaces, and Spaces hosted by others. Return direct Space/post URLs, ids, dates, titles, hosts, durations, and exact evidence. Be explicit about uncertainty.'
```

Grok is discovery evidence, not authority. Independently query **every candidate**:

```bash
for url in https://x.com/i/spaces/ID1 https://x.com/i/spaces/ID2; do
  yt-dlp --skip-download --no-warnings \
    --print 'id=%(id)s|upload_date=%(upload_date)s|timestamp=%(timestamp)s|title=%(title)s|uploader=%(uploader)s|uploader_id=%(uploader_id)s|duration=%(duration)s|webpage_url=%(webpage_url)s' \
    "$url"
done
```

`yt-dlp` currently reports X Space identity, upload date, title, and host, but may report duration as `NA`. Verify downloaded duration with `ffprobe`; record that limitation instead of inventing a value. Keep the direct evidence that rules out newer candidates.

Proceed only when the selected URL resolves to `uploader_id=McCarthy_JT` and the Wednesday/Matt/show evidence is clear.

## 2. Download, transcribe, and inspect (automatic, then judgment gate)

Keep working files outside the repository or in ignored scratch space:

```bash
url=https://x.com/i/spaces/SPACE_ID
work=/path/to/private/scratch
mkdir -p "$work"
yt-dlp --no-warnings -o "$work/source.m4a" "$url"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,sample_rate,channels \
  -of json "$work/source.m4a"

# whisper-cli on this machine requires WAV input.
ffmpeg -y -hide_banner -loglevel error -i "$work/source.m4a" \
  -ar 16000 -ac 1 -c:a pcm_s16le "$work/source.wav"
whisper-cli -m ~/.whisper-models/ggml-large-v3-turbo.bin \
  -f "$work/source.wav" -otxt -ovtt -of "$work/source" --print-progress
rm "$work/source.wav"
```

Listen around the first and last speech and inspect pauses. For example:

```bash
ffplay -ss 120 -t 90 "$work/source.m4a"
ffmpeg -hide_banner -nostats -i "$work/source.m4a" \
  -af silencedetect=noise=-45dB:d=0.5 -f null - 2>&1 | grep silence
```

Choose start/end timestamps at pauses or VTT cue boundaries. A repeated phrase over hold music or dead air (for example, Whisper's repeated "We'll be right back") is a demonstrated hallucination only when the audio and cut window establish that; do not apply broad text heuristics.

## 3. Write the transcript-grounded manifest

Create a private JSON file in scratch. Titles, descriptions, speakers, and selection notes must come from the recording/transcript.

```json
{
  "schema_version": 1,
  "date": "YYYY-MM-DD",
  "slug": "deterministic-lowercase-slug",
  "title": "Transcript-grounded episode title",
  "speakers": ["JT", "Matt McCarthy"],
  "concise_description": "One concise transcript-grounded sentence.",
  "spotify_description": "The full transcript-grounded Spotify description.",
  "cut_start_seconds": 123.456,
  "cut_end_seconds": 4567.890,
  "edit_rationale": "Removed X hold music/pre-show greetings before the real introduction and dead air after the spoken close; no program content removed.",
  "selection_evidence": [
    "Direct evidence that this is Wednesday Peak Mind with JT and Matt."
  ],
  "ruled_out_candidates": [
    {
      "space_url": "https://x.com/i/spaces/OTHER_ID",
      "reason": "Newer, but hosted by another account / BoomRoom / not Peak Mind."
    }
  ]
}
```

The final directory is always `<output-root>/<date>-<slug>/`. The script refuses to overwrite it. To revise a kit, review and deliberately move the old directory first; there is no force flag.

## 4. Build and validate the kit (automatic)

Reuse the inspected source and its raw VTT transcript so the script does not download or transcribe twice:

```bash
python3 catalog/scripts/prepare_peak_mind_kit.py prepare "$url" \
  --manifest "$work/manifest.json" \
  --source-file "$work/source.m4a" \
  --transcript-prefix "$work/source"
```

If the source-level Whisper pass lost words at the hold-music/program transition, reuse only the source. The script trims first, converts the edited audio to mono 16 kHz WAV, and creates fresh TXT/VTT output on the final timeline:

```bash
python3 catalog/scripts/prepare_peak_mind_kit.py prepare "$url" \
  --manifest "$work/manifest.json" \
  --source-file "$work/source.m4a"
```

Or omit both reuse options and let the script download the verified replay before doing the same final-audio transcription:

```bash
python3 catalog/scripts/prepare_peak_mind_kit.py prepare "$url" \
  --manifest "$work/manifest.json"
```

The script:

- re-verifies Space id, date, and `@McCarthy_JT` host with `yt-dlp`;
- checks dependencies and the required Whisper model;
- checks the cut window against source duration;
- trims AAC with ffmpeg stream copy (`-c:a copy`) and fast-start metadata;
- when given `--transcript-prefix`, removes cues outside the approved cut window and shifts retained VTT timestamps;
- refuses a cut through a reused transcript cue rather than guessing which words to keep;
- otherwise transcribes the edited audio so TXT/VTT timestamps directly match the final file;
- verifies AAC/M4A codec, duration, byte count, full decode, transcripts, and SHA-256;
- atomically creates the kit only after validation.

Validate again at any time:

```bash
python3 catalog/scripts/prepare_peak_mind_kit.py validate \
  ~/Downloads/peak-mind-spotify/YYYY-MM-DD-slug
```

The kit contains final M4A audio, TXT/VTT transcripts, `UPLOAD.txt`, `SOURCE-EVIDENCE.json`, the approved `MANIFEST.json`, and `SHA256SUMS`.

## Tests

Tests use local fixtures and mocked media/network command boundaries:

```bash
python3 -m unittest discover -s catalog/scripts/tests -v
```
