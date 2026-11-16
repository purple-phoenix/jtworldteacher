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

Run `week.py stage <week.json>`, then from the repo root `source catalog/social/shorts/browser/x.sh` (it also loads `youtube.sh`). The Peak Mind Chrome profile is already signed in to both sites. Delete `.upload-tmp/` when finished. Week 1 was scheduled this way on 2026-11-01: 7 YouTube Shorts and 7 X posts, Mon/Wed/Fri at 12:00 PM ET. Week 2 was scheduled the same way on 2026-11-16: 8 YouTube Shorts and 8 X posts from Nov 18 to Dec 4 (Letting go of resentment held while Matt checks with JT). Week 3 (eleven daily slots from Nov 17 to Dec 6, Dec 5 left empty) was scheduled on 2026-11-15: all 11 on X, but only 2 on YouTube before the daily upload limit stopped it.

- **YouTube Studio:** upload, then fill in title, description and "not made for kids". Click Next three times, open **Schedule**, then set the date and time.
  - The time options use a narrow no-break space ("12:00 PM"), so typing a time doesn't work.
  - On some screens the time list saves one slot off from the option clicked. `set_noon` keeps trying until the field reads 12:00 PM.
  - Confirm success with the "will be set to public on …" message (it also has a narrow no-break space before PM, and may end "after the standard definition (SD) finishes processing"), not by reading the page summary, which gets cut off when the Shorts list is behind the dialog.
  - If a run leaves drafts, finish them from the video's own page (`studio.youtube.com/video/<id>/edit` → **Edit draft**).
  - **Daily upload limit:** the channel is unverified, and about 10 uploads in 24 hours trips "Daily upload limit reached. Upload more videos daily after a one-time verification or wait 24 hours." It shows only in the upload dialog's file row, after the title is already filled in, and the upload is discarded silently, so `finish` reports UNCONFIRMED and no draft appears. Check the dialog text for it before scheduling, never click **Verify** (it is Matt's call), and split a big week across two days.
  - `set_noon` can loop on "12:00 AM" when the time reads back with an escaped narrow no-break space. Clicking the input, then the visible `tp-yt-paper-item` whose text is "12:00 PM", and checking the value in the page works. Don't press Escape to recover: it closes the dialog and leaves a draft.
- **X:** the composer's **Schedule post** panel (`data-testid=scheduleOption`) has six selects (Month, Day, Year, Hour, Minute, AM/PM). Set them with the native value setter and a `change` event. `xpost <n> <day> '<expected date text>' [month]` uploads, types and schedules one post; month defaults to 11, so pass 12 for December slots.
  - Only click the button when it reads **Schedule** and the panel says "Will send on <date> at 12:00 PM". Never click it while it says **Post**.
  - Check the result at `x.com/compose/post/unsent/scheduled`.
  - Editing a scheduled post doesn't save, so to change one, make a new scheduled post and delete the old one (Edit, tick it, Delete). X drops a typed opening quotation mark; `xtype` puts it back.
- **TikTok Studio** (signed in as peakmindshow): `source catalog/social/shorts/browser/tiktok.sh` after `x.sh`, then `tslot <n> <YYYY-MM-DD>` per post. It uploads the YouTube file (bleeped where a clip has one), uses the X post text as the caption, picks **Schedule**, the date and 12:00, and confirms the row in the content list. To stage two weeks at once, stage each, keep the first `posts.json` aside, and merge the two lists. Week 2 and week 3 (19 posts, Nov 17 to Dec 6) were scheduled this way on 2026-11-16.
  - The schedule window runs about 30 days ahead (on Nov 16 the last selectable day was Dec 15).
  - Times are 24-hour in the browser's zone ("(GMT-5) Local Time"); the list shows "Nov 17, 12:00 PM (GMT-5) New York" with a narrow no-break space before PM, so normalise whitespace before matching.
  - Dismiss "Turn on automatic content checks?" with **Cancel** and "New editing features added" with **Got it**. Choosing Schedule asks "Allow your video to be saved for scheduled posting?": **Allow**.
  - The first file pick sometimes doesn't attach; wait for "Uploaded" and pick again. If the Mac sleeps mid-run the schedule is lost silently, so keep it awake (`caffeinate`).
  - The content list is virtualised (about nine rows render at a time). Scroll its container in steps to see every row.
- **Instagram:** instagram.com's composer has no scheduling for Reels (Advanced settings has only hide counts and comments), only **Share**, which posts at once. Meta Business Suite would schedule, but it needs a separate Meta login, which is Matt's call. Nothing is scheduled on Instagram yet.
