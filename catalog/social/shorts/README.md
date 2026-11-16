# Peak Mind shorts

Vertical (1080x1920) videos for X and YouTube Shorts, made from the approved clips in `../clips/`.

The look is type only, with no generated imagery: the voice is JT's and real, and AI art next to it reads as "AI slop" (decided with Matt on 2026-11-01).
Each video has a headline, word-by-word captions with the spoken word highlighted, "Recorded live on X" with the date, a live waveform and @PeakMindShow.

- `align_words.py`: word timings from whisper.cpp DTW, shifted 0.05 s earlier and snapped out of pauses. The default timestamps drifted, putting 18 of 119 words inside pauses on clip #1.
- `render_short.py`: draws frames with Pillow and pipes them to ffmpeg, because the Homebrew ffmpeg has no libass or drawtext. `--bleep` puts a tone over swears and masks them in the captions. Filler words stay in the audio but are left out of the captions.
- `week.py render|kit <week-NN.json>`: renders a week's clips into `~/Downloads/JT social clips/Shorts/` and writes `week-NN-kit.md`, which holds the X post text, YouTube title and description, and post date for each clip. Every link points to the Peak Mind Spotify show (Matt, 2026-11-01).

Clips that swear get two files: an uncensored one for X and a bleeped one for YouTube.
Nothing posts automatically. Each week's kit is approved by Matt before anything is scheduled.

Set `output_subdir` on each clip (for example, `week-03`) to keep its videos below the Shorts folder; rendering, kit paths and staging all use that subfolder. `audio` may be an absolute path to a saved isolated cut.

Week files may include `caption`, `episode_title` and `hashtags` for transcript-grounded copy from Studio, plus `review_url`, `duration_seconds` and `why` for review. Set `promote_live: false` to omit live-show promotion. List optional `spare: true` clips after the dated slots with `post_on: null`; the kit labels them as undated spares. Staging refuses a file containing spares, so first make a manifest containing only the approved dated choices.

## Scheduling (after Matt approves the week's kit)

Run `week.py stage <week.json>`, then from the repo root `source catalog/social/shorts/browser/x.sh` (it also loads `youtube.sh`). The Peak Mind Chrome profile is already signed in to both sites. Delete `.upload-tmp/` when finished. Week 1 was scheduled this way on 2026-11-01: 7 YouTube Shorts and 7 X posts, Mon/Wed/Fri at 12:00 PM ET. Week 2 was scheduled the same way on 2026-11-16: 8 YouTube Shorts and 8 X posts from Nov 18 to Dec 4 (Letting go of resentment held while Matt checks with JT).

- **YouTube Studio:** upload, then fill in title, description and "not made for kids". Click Next three times, open **Schedule**, then set the date and time.
  - The time options use a narrow no-break space ("12:00 PM"), so typing a time doesn't work.
  - On some screens the time list saves one slot off from the option clicked. `set_noon` keeps trying until the field reads 12:00 PM.
  - Confirm success with the "will be set to public on …" message (it also has a narrow no-break space before PM, and may end "after the standard definition (SD) finishes processing"), not by reading the page summary, which gets cut off when the Shorts list is behind the dialog.
  - If a run leaves drafts, finish them from the video's own page (`studio.youtube.com/video/<id>/edit` → **Edit draft**).
- **X:** the composer's **Schedule post** panel (`data-testid=scheduleOption`) has six selects (Month, Day, Year, Hour, Minute, AM/PM). Set them with the native value setter and a `change` event. `xpost <n> <day> '<expected date text>' [month]` uploads, types and schedules one post; month defaults to 11, so pass 12 for December slots.
  - Only click the button when it reads **Schedule** and the panel says "Will send on <date> at 12:00 PM". Never click it while it says **Post**.
  - Check the result at `x.com/compose/post/unsent/scheduled`.
  - Editing a scheduled post doesn't save, so to change one, make a new scheduled post and delete the old one (Edit, tick it, Delete). X drops a typed opening quotation mark; `xtype` puts it back.

## Mac mini review batches

Set `PEAK_MIND_SHORTS_DIR=/Users/mtmccarthy/peak-mind-shorts` for both `week.py render` and `week.py kit`. Output subfolders and word caches then stay on the mini. The mini's existing renderer environment is `/Users/mtmccarthy/astroai-social-studio/venv/bin/python` (Pillow and NumPy); use that Python for `week.py`.

Week 4 lives in `/Users/mtmccarthy/peak-mind-shorts/week-04/`. The read-only `review_server.py` supports byte ranges for seeking and listens only on `127.0.0.1:5490`. Its installed copy is `/Users/mtmccarthy/peak-mind-shorts/.server/review_server.py`, started by `~/Library/LaunchAgents/com.peakmind.shorts-review.plist` at login and restarted on failure. Restart it with `launchctl kickstart -k gui/$(id -u)/com.peakmind.shorts-review`. After a cold reboot, the user's GUI login is required for LaunchAgents.

Tailscale Serve exposes only port 5490 to the tailnet at <https://matts-mac-mini.tailebcf61.ts.net:5490/>. Existing Serve and Funnel routes are left alone. Nothing in this workflow posts or schedules clips.
