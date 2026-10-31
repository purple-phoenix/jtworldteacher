# Peak Mind weekly Spotify upload kit

This runbook prepares a **local** kit for the captain's manual Spotify for Creators upload. It never uploads to Spotify, R2, or the public site/feed.

Peak Mind is the Wednesday show with JT and his brother Matt. It is not JT's Thursday BoomRoom, a casual Space, or a Space hosted by another account.

## The two judgment gates

Do not automate these decisions:

1. **Select the show.** Decide that the Space is a genuine Peak Mind episode, not merely the latest Space JT linked. If the evidence is ambiguous, stop and ask the captain.
2. **Approve the edit and transcript.** Listen and use the transcript/waveform to identify the first real program sentence and the end of the spoken close. Remove only demonstrated hold music, pre-show chatter, dead-air tail, and whole Whisper cues demonstrated to be hallucinations. Never cut inside the show or silently rewrite speech.

`catalog/scripts/prepare_peak_mind_kit.py` automates the deterministic work around those gates and pauses before finalization for explicit transcript-cleanup attestation.

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
    --print 'id=%(id)s|upload_date=%(upload_date)s|release_date=%(release_date)s|timestamp=%(timestamp)s|title=%(title)s|uploader=%(uploader)s|uploader_id=%(uploader_id)s|duration=%(duration)s|webpage_url=%(webpage_url)s' \
    "$url"
done
```

`yt-dlp` currently reports X Space identity, upload date, title, and host, but may report duration as `NA`. For a scheduled Space, `upload_date` is the day it was *created*, often days before the show. `release_timestamp` is when it went live. The manifest `date` is the Eastern-time date the Space went live, which can be a day before the UTC `release_date` for 8:30 PM starts. The script checks this. Verify downloaded duration with `ffprobe`; record that limitation instead of inventing a value. Keep the direct evidence that rules out newer candidates.

Proceed only when the selected URL resolves to `uploader_id=McCarthy_JT` and the Wednesday/Matt/show evidence is clear.

## 2. Download, transcribe, and inspect (automatic, then judgment gate)

Keep working files outside the repository or in ignored scratch space:

```bash
url=https://x.com/i/spaces/SPACE_ID
work=/path/to/private/scratch
install -d -m 700 "$work"
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

`catalog/scripts/peak_mind_review.py` collects the evidence for this step without choosing anything:

```bash
python3 catalog/scripts/peak_mind_review.py markers "$work/source.vtt"            # on-air open/close and Q&A handoff lines
python3 catalog/scripts/peak_mind_review.py scan "$work/source.vtt" START END     # likely hallucinations in the kept window
python3 catalog/scripts/peak_mind_review.py check "$work/source.m4a" "$work/source.vtt" START END
python3 catalog/scripts/peak_mind_review.py clips "$work/source.m4a" START END "$work/clips" SLUG
```

The episode starts at the on-air open ("I'm JT. This is Matt. This is Peak Mind.") or another natural opener, never partway through an answer. It ends after one of the hosts says the show is ending, before a listener is invited up for Q&A. Whisper cue boundaries are often half a second off, so `check` fails a cut unless it lands between cues in a 50 ms window at or below -40 dB.

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

The final directory is always `~/Downloads/peak-mind-spotify/<date>-<slug>/`. The script refuses to overwrite it. To revise a kit, review and deliberately move the old directory first; there is no force flag.

## 4. Create the source-bound review checkpoint (automatic)

Pass the approved canonical Space URL. The script independently downloads that Space again so the final kit cannot accidentally combine a URL with another candidate's scratch audio or transcript. It transcribes the uncut source, writes a hash-bound checkpoint under `~/Downloads/peak-mind-spotify/.checkpoints/`, prints the exact next command, and stops without creating a kit:

```bash
python3 catalog/scripts/prepare_peak_mind_kit.py prepare "$url" \
  --manifest "$work/manifest.json"
```

Phase 1:

- re-verifies Space id, date, and `@McCarthy_JT` host with `yt-dlp`;
- freshly downloads the verified replay into a private checkpoint;
- checks dependencies and the required Whisper model;
- checks the cut window against source duration;
- converts the source to mono 16 kHz WAV for Whisper, writes editable `draft.vtt`, and preserves a hashed `draft.original.vtt`;
- records the canonical Space URL/id, verified metadata, manifest hash, source hash/byte count/probe, draft provenance, and tool versions in `CHECKPOINT.json`.

## 5. Review transcript cleanup, then resume

Open the checkpoint's `source.m4a` and `draft.vtt`. Remove only whole cues demonstrated by listening to be Whisper hallucinations; do not edit `draft.original.vtt`, rewrite speech, reorder cues, or alter timestamps. Resume verifies the reviewed VTT is an exact subsequence of the hashed original. Confirm the approved start/end do not cross a retained cue. If either cut crosses a cue, delete the checkpoint and restart phase 1 with corrected manifest timestamps rather than guessing which words belong inside the cut.

After that review, run the exact command printed by phase 1 and stored in `NEXT-STEPS.txt`:

```bash
python3 catalog/scripts/prepare_peak_mind_kit.py resume \
  ~/Downloads/peak-mind-spotify/.checkpoints/YYYY-MM-DD-slug \
  --attest-cleanup
```

`--attest-cleanup` is an explicit operator attestation that the draft was checked against the audio. Phase 2 revalidates the managed checkpoint path, Space identity, manifest hash, source hash and byte count, source duration, draft provenance, and cut boundaries before it:

- drops reviewed cues wholly outside the approved cut and refuses any cue crossing either boundary;
- shifts retained VTT cues to the edited-audio timeline and derives TXT from that cleaned VTT;
- trims AAC with ffmpeg stream copy (`-c:a copy`) and fast-start metadata;
- verifies AAC/M4A codec, duration, byte count, full decode, transcripts, and SHA-256;
- atomically creates the fixed Downloads kit only after validation, then removes the private checkpoint.

Repeating the same resume command is safe: it validates and returns the completed kit without overwriting it.

Validate again at any time:

```bash
python3 catalog/scripts/prepare_peak_mind_kit.py validate \
  ~/Downloads/peak-mind-spotify/YYYY-MM-DD-slug
```

The kit contains final M4A audio, TXT/VTT transcripts, `UPLOAD.txt`, `SOURCE-EVIDENCE.json`, the approved `MANIFEST.json`, and `SHA256SUMS`.

## Episode cover

Episode covers follow the "Oracular Broadside" series in `~/Downloads/peak-mind-spotify/episode-thumbnails/`. Generate text-free square art; the prompts are saved beside each `source/*-source.png`, and the lower ~37% must stay plain parchment. Then set the type programmatically, never with the image model:

```bash
catalog/scripts/compose_peak_mind_cover.sh source.png out.jpg 'MAIN TITLE' $'AND THE\nSUBTITLE'
```

The script refuses to overwrite and sizes the titles to fit. Big Caslon only has old-style figures, so digits are set in Baskerville lining figures.

## Tests

Tests use local fixtures and mocked media/network command boundaries:

```bash
python3 -m unittest discover -s catalog/scripts/tests -v
```
