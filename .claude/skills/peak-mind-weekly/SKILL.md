---
name: peak-mind-weekly
description: Weekly Peak Mind run on the Mac mini: find the newest Wednesday Peak Mind X Space, cut it, write copy, make the cover, build the Spotify kit, send Matt a one-tap review, and after "approved" upload it to Spotify for Creators in the mini's Peak Mind Chrome profile. Use when the scheduled Thursday run fires, or when the user says "do this week's Peak Mind" / invokes /peak-mind-weekly.
---

# Peak Mind weekly run (one-tap approval)

Peak Mind is the Wednesday X Space podcast co-hosted by JT (`@McCarthy_JT`, the host account) and his brother Matt (the user). Spotify show: https://open.spotify.com/show/033LHLE9BxNUNTLSzmDqfC. It is not JT's Thursday BoomRoom, casual Spaces, or Spaces hosted by others.

Authoritative references (read before acting): `catalog/PEAK_MIND_SPOTIFY.md` (kit runbook and judgment gates), `catalog/PEAK_MIND_VOICE.md`, and memory `peak_mind_podcast.md` + `jt_voice_and_themes.md` in `~/.claude/projects/-Users-mtmccarthy-github-jtworldteacher/memory/`.

**Where this runs (Matt, 2026-11-16):** on the Mac mini (home `/Users/mtmccarthy`), never the MacBook, which sleeps and missed the Nov 12 run. Use `python3.13` for every script here: the mini's `/usr/bin/python3` is Apple's 3.9, which cannot load `prepare_peak_mind_kit.py`. Studio's code lives in `purple-phoenix/peakmindshow` (`studio/`, cloned at `~/github/peakmindshow`) and runs from `~/peak-mind-studio/app`.

Matt approves once per episode, after hearing the clips and seeing the cover and copy, in **Peak Mind Studio** (the local app from `peakmindshow/studio/`, see §7). The Studio's Approve button posts `approved <cover>` into this run's T3 thread; a typed "approved" reply in the thread also counts. That approval is the attestation for `resume --attest-cleanup` and the go-ahead to publish that one episode. Nothing is published without it. Never approve on Matt's behalf: not with the Studio API, not with `t3 thread send`.

## 0. What's already done

- Spotify's latest: `curl -sL https://open.spotify.com/embed/show/033LHLE9BxNUNTLSzmDqfC` → parse `<script id="__NEXT_DATA__">` → `props.pageProps.state.data.entity` (`title`, `releaseDate.isoString`).
- Local kits: `ls ~/Downloads/peak-mind-spotify/` (finished: `<date>-<slug>/`; in progress: `.checkpoints/`).
- LAST = the newest recording date that is on Spotify or has a kit. Work only on Wednesdays after LAST, oldest first, one episode per review message.
- Studio: `S="python3.13 ~/peak-mind-studio/app/studioctl.py"` (config `~/.config/peak-mind-studio/config.json`); `$S list` shows every episode and its status. If an episode is already `review` or `approved` there, finish that one first. The Studio runs on the Mac mini as LaunchAgent `com.peakmind.studio` (log `~/Library/Logs/peak-mind-studio.log`), tailnet URL https://matts-mac-mini.tailebcf61.ts.net:5480 (details: `~/github/peakmindshow/studio/README.md`). The old MacBook copy is stopped and kept only as a backup; never write to it.

## 1. Discover (judgment gate 1)

```bash
scratch="$(mktemp -d)"; cd "$scratch" && grok --cwd "$scratch" --no-memory --no-subagents -p \
  'From scratch, find every recorded X Space hosted by @McCarthy_JT after <LAST> through today. JT records a Wednesday podcast called Peak Mind with his brother Matt (~7 PM Eastern, sometimes 8:30). Distinguish BoomRoom (Thursday), casual/test Spaces, and Spaces hosted by others. Return Space/post URLs, ids, dates/times (UTC), titles, hosts, and exact post text. Be explicit about uncertainty.'
```

Verify every candidate yourself (Grok is a lead, not evidence):

```bash
yt-dlp --skip-download --no-warnings --print 'id=%(id)s|upload_date=%(upload_date)s|release_ts=%(release_timestamp)s|title=%(title)s|uploader_id=%(uploader_id)s' "https://x.com/i/spaces/<ID>"
```

**14-character Space IDs:** since Nov 2026 X issues 14-character IDs (e.g. `1gqvzmLkLrWvnV`), and yt-dlp 2026.08.19 only matches 13, failing with "Twitter Space not found" on a truncated ID. Put the wrapper first on PATH for every yt-dlp call, including `prepare_peak_mind_kit.py`: `PATH=~/peak-mind-scratch/bin:$PATH` (`~/peak-mind-scratch/bin/yt-dlp` widens the pattern for its own process only). Retire it once Homebrew's yt-dlp accepts the ID.

Accept only `uploader_id=McCarthy_JT` and a `release_timestamp` that lands on a Wednesday evening in America/New_York (`upload_date` is when a scheduled Space was created and can be days early). Show identity is confirmed later from the transcript ("This is Peak Mind", Matt speaking). If no new Wednesday Space exists, post one line ("No new Peak Mind since <LAST>") and stop, with no notification. If identity is ambiguous, notify Matt and stop.

## 2. Download and transcribe (scratch)

```bash
d=~/peak-mind-scratch/<YYYY-MM-DD>; mkdir -p "$d"
yt-dlp --no-warnings -o "$d/source.m4a" "https://x.com/i/spaces/<ID>"
ffmpeg -y -hide_banner -loglevel error -i "$d/source.m4a" -ar 16000 -ac 1 -c:a pcm_s16le "$d/source.wav"
whisper-cli -m ~/.whisper-models/ggml-large-v3-turbo.bin -f "$d/source.wav" -ovtt -otxt -of "$d/source" --print-progress
rm "$d/source.wav"
```

Run the transcription in the background; it takes ~5–10 min per 2–3 h Space on this Mac.

## 3. Choose cuts (judgment gate 2)

`R="python3.13 catalog/scripts/peak_mind_review.py"`: `$R markers`, `$R cues`, `$R scan`, `$R check`.

- **Start**: the on-air open if there is one ("Let's try to do this right. I'm JT. This is Matt. This is Peak Mind."). Otherwise start at a natural opener (a question between the brothers or the first line of the topic), never mid-answer or mid-thought (2026-10-28: starting on JT's mid-answer "I look forward to making the podcast" sounded wrong; Matt picked the start at Matt's "How's your week been?"). Hold music, sound-effect banter, and catching up before the open are cut.
- **End**: one of them says the show is ending ("end of the podcast", "end of the show", "thank you all for attending this podcast") right before opening to speakers/Q&A. Keep the spoken sign-off; cut before the handoff line that invites a speaker up ("All right, Diogenes, go ahead", "John, if you want to come up"). Listener Q&A is never in the episode.
- Put each cut in a measured pause *between* cues, never on Whisper's own cue boundary without checking (they are often ±0.5 s off and clip words). `$R check <audio> <vtt> <start> <end>` must PASS both cuts.
- `$R scan` the kept window. Only remove whole cues that are demonstrated hallucinations; JT's stammers ("the, the, the") are real speech.
- **Confidence**: HIGH only when there is an explicit on-air open and an explicit end-of-show line. Otherwise LOW: still prepare, but say exactly what is uncertain in the review.

## 4. Title and descriptions

Dispatch a `general-purpose` subagent (synchronous) on the kept window. Give it: the transcript path and cut window; the style precedents (`~/Downloads/peak-mind-spotify/DESCRIPTIONS.txt` and earlier kits' `MANIFEST.json` title/concise_description/spotify_description); the voice memory; Matt's writing rules in `catalog/PEAK_MIND_VOICE.md` (check the draft against every rule before using it); and the rules: everything from the transcript, third person, plain text, garbled names flagged, forward-looking claims framed as JT's interpretations, politics neutral. Ask for: title (primary + 2 alternates, "X and the Y" pattern), concise description ≤300 chars, Spotify description 90–150 words, speakers with any non-host voice inside the window, 6–10 timestamped beats, uncertain terms. Spot-check at least three claims with `grep` on `source.txt` before using them.

## 5. Cover

Delegate to Codex (`delegate_task`, provider `codex`, model `gpt-6.1-sol`, `reasoningEffort: high`, `mode: async`): two text-free variants in the Oracular Broadside series, saved to `~/Downloads/peak-mind-spotify/episode-thumbnails/source/<date>-<slug>-v{1,2}-source.png` with prompts beside them. Reuse the prompt structure in the existing `source/*-prompt.txt` files and the layout constraint (bottom ~37% plain parchment, top-left label area clear). Then letter both:

```bash
catalog/scripts/compose_peak_mind_cover.sh <src.png> ~/Downloads/peak-mind-spotify/episode-thumbnails/drafts/<date>-<short>-v1.jpg 'MAIN TITLE' 'AND THE SUBTITLE'
```

Look at both at full size and at 64 px before showing them.

## 6. Manifest and checkpoint

Write `~/peak-mind-scratch/manifests/<date>.json` (schema in `catalog/PEAK_MIND_SPOTIFY.md` §3; `ruled_out_candidates` entries contain only `space_url` and `reason`; `date` is the Eastern recording date). Then, in the background:

```bash
python3.13 catalog/scripts/prepare_peak_mind_kit.py prepare "https://x.com/i/spaces/<ID>" --manifest ~/peak-mind-scratch/manifests/<date>.json
```

Confirm the checkpoint `draft.vtt` matches the scratch VTT and rerun `$R check` against the checkpoint files. Make the review clips: `$R clips <audio> <start> <end> ~/Downloads/peak-mind-spotify/review-clips <date>-<short>`.

## 7. Review in Peak Mind Studio (stop here)

Write the review into the Studio, not as a long chat message. Matt reads and approves it there.

1. Make sure the episode exists: `$S get <date>`. If it 404s (Matt didn't add it during prep), create it; `studioctl` only edits existing docs, so use the API: `curl -sf -X PUT http://127.0.0.1:5480/api/episodes/<date> -H 'X-Peak-Mind-Studio: 1' -H 'Content-Type: application/json' -d '{"date":"<date>","title":"<title>","status":"editing","time":"<h:mm PM ET>","summary":"<concise description>","spaceUrl":"https://x.com/i/spaces/<ID>","spotifyUrl":"https://open.spotify.com/show/033LHLE9BxNUNTLSzmDqfC","sections":[],"beats":[],"clips":[],"checklist":[]}'`. If it exists, `$S patch <date>` the summary and space link instead; never overwrite Matt's prep, script or clips.
2. Write `review.json` in scratch (schema in `studio/README.md`) and run `$S put-review <date> review.json`. Include: `t3ThreadId` and `t3ThreadLink` of THIS thread (from `t3 thread list --project ~/github/jtworldteacher --json`; on the mini `t3` is `~/.local/bin/t3`), title + 2 alternates, both descriptions, length, confidence (+ note), `start`/`end` with the exact quoted lines on either side of each cut, every flag as one plain sentence, covers `[{id:"v1",label,media:"kits/episode-thumbnails/drafts/<date>-<short>-v1.jpg"}, ...v2]` with `defaultCover`, and clips `kits/review-clips/<date>-<short>-{opening,ending}.m4a`. `put-review` sets status "Awaiting approval".
3. Open https://matts-mac-mini.tailebcf61.ts.net:5480/#ep-<date> in a fresh headless browser session (Chrome for Testing or a headless-shell binary, never the installed Google Chrome app) and check the Review tab renders, both covers load and both clips play. Look only: never click Approve or Request changes.
4. Post a short message in the thread (title, confidence, any flag that needs a decision, and the Studio link), then `PushNotification`: `Peak Mind "<title>" ready to approve in Studio`. End the turn. Do not resume, upload, or publish until the approval arrives.

## 8. After "approved"

0. The approval arrives as a T3 message: `approved <cover>` followed by `Sent from Peak Mind Studio by Matt McCarthy (...)`, or Matt types "approved" himself. Before acting, run `$S get <date>` and confirm `approval.decision` is `approved`, `approval.by` is Matt's login, the cover matches, and status is `approved` (for a typed reply there is no Studio record; that's fine). A `changes requested` message carries Matt's note: apply it (step 1), then `$S put-review` again, which reopens the review.
1. Apply any requested changes first (title/copy/cut changes mean: delete the checkpoint, update the manifest, rerun §6, re-send the review).
2. `python3.13 catalog/scripts/prepare_peak_mind_kit.py resume ~/Downloads/peak-mind-spotify/.checkpoints/<date>-<slug> --attest-cleanup`
3. Copy the chosen cover draft to `~/Downloads/peak-mind-spotify/episode-thumbnails/<date>-<slug>.jpg` and append its entry to that folder's `manifest.json` (title, slug, outputFilename, dimensions, byteSize, sha256, sitePath `episodes/<file>`, siteStatus `not-wired-spotify-only`).
4. Upload (§9). After publishing, confirm the Spotify embed's latest entity title matches.
5. Mark it published in the Studio: `$S patch <date> '{"status":"published","title":"<final title>"}'`. Update the status section of memory `peak_mind_podcast.md`, and `PushNotification` that it's live.

## 9. Upload to Spotify for Creators (dedicated browser profile)

Uploads run on the Mac mini in its Peak Mind Chrome profile (`~/.peak-mind-social-chrome`, session `peak-mind-social`, headed), the same profile the shorts scheduling uses (`catalog/social/shorts/README.md`). It is signed in to Spotify for Creators with Matt's Google account, which is a team member on PEAK MIND; the login address is in `~/.config/peak-mind-studio/spotify-login` (private, never committed). It does not use Matt's own Chrome. Mapped 2026-10-31 on the MacBook; moved to the mini 2026-11-16. If another thread is driving the same session (check `chrome-devtools-axi pages` and the running Peak Mind threads), wait for it to finish: opening a tab steals its selected page.

```bash
export CHROME_DEVTOOLS_AXI_SESSION=peak-mind-social CHROME_DEVTOOLS_AXI_USER_DATA_DIR=$HOME/.peak-mind-social-chrome \
  CHROME_DEVTOOLS_AXI_HEADED=1 CHROME_DEVTOOLS_AXI_CHROME_ARGS="--disable-blink-features=AutomationControlled"
```

- **Signed out?** Spotify's reCAPTCHA rejects the headless/automation-flagged browser, so keep it HEADED with that flag. Click the Email box and enter the address from `~/.config/peak-mind-studio/spotify-login` with `type` (keystrokes), then Continue. Spotify emails a 6-digit code. On 2026-10-31 the Gmail connector never saw it, so ask Matt for it with `request_secret` (`delivery: "file"`), type it into "Digit 1 of 6", then Next. Never ask for or type a password.
- **Upload paths must be inside the repo** (the browser tool's workspace root). Stage copies in `catalog/spaces/audio/spotify-staging/` (gitignored) and delete them after publishing.
- **Refs go stale constantly on these pages.** Prefer `eval` with the selectors below over `fill`/`click @ref`. Only use `type` after confirming `document.activeElement`: a stray keystroke landed on the wizard's Close button and opened "Cancel upload?".

Steps (one episode at a time, oldest first):

1. `chrome-devtools-axi open https://creators.spotify.com/pod/show/033LHLE9BxNUNTLSzmDqfC/episode/wizard` (Upload → Details → Review).
2. `upload @<ref of button "Select a file">` with the staged `.m4a`. Wait until `#title-input` exists (~30–60 s for ~75 MB). The URL becomes `/episode/<draftId>/wizard`. Reopen that URL to recover from a bad state, though the title and description aren't saved until Next.
3. **Title:** set `#title-input` with the native `HTMLInputElement` value setter, then dispatch `input` and `change`. The counter should read `N / 200`.
4. **Description:** click the checkbox labelled `HTML`. That replaces the Slate editor with a `<textarea>`. Set it to `<p>…escaped description…</p>` with the native `HTMLTextAreaElement` setter, then dispatch `input`/`change`; the counter should read `N / 4000`. Never `execCommand`/type into the Slate editor: it desyncs, and the only fix is reloading the draft URL.
5. **Episode art:** first wait until the page shows "Preview ready!" with no "Uploading (N%)". While the audio upload is still running, refs go stale on every attempt. Then `upload @<ref of button "Change">` with the staged `.jpg`. In the crop dialog, click the only `Save` button and wait for "Saving..." to clear.
6. Leave the defaults as they are: `podcastEpisodeIsExplicit` unchecked (No), `podcastEpisodeContainsSponsoredContent` unchecked (No), type Full, Spotify settings (auto transcript/chapters) Off. Review shows Comments On, which comes from the show setting.
7. Click the only `Next` button. On Review, screenshot it and check the title, description, the **Episode art row** (it disappears if the art upload silently failed; go Back and redo step 5), and Explicit No.
8. Choose `#publish-date-now` (or `#publish-date-schedule`), then click `Publish`. **Only after Matt's "approved" for this episode.**
9. Confirm the Spotify embed's latest entity title matches, then delete the staged copies.

## Stop and ask Matt when

- A candidate's show identity is unclear, or two Wednesdays' worth of episodes are pending (review them one at a time).
- There is no end-of-show line before the Q&A, or `$R check` can't PASS at a sensible line.
- Codex image generation fails, or both variants contain text or broken composition.
- Chrome isn't reachable, Spotify isn't signed in, or the upload form doesn't match §9.

## Never

Publish without "approved" for that specific episode; overwrite or rename an existing kit, cover, or audio file; commit audio, transcripts, or kits to git; include listener Q&A; type passwords or approve logins; or pass `--attest-cleanup` before Matt has approved the clips.
