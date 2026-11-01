# Peak Mind shorts

Vertical (1080x1920) videos for X and YouTube Shorts, made from the approved clips in `../clips/`.

The look is type only, with no generated imagery: the voice is JT's and real, and AI art next to it reads as "AI slop" (decided with Matt on 2026-11-01).
Each video has a headline, word-by-word captions with the spoken word highlighted, "Recorded live on X" with the date, a live waveform and @PeakMindShow.

- `align_words.py`: word timings from whisper.cpp DTW, shifted 0.05 s earlier and snapped out of pauses. The default timestamps drifted, putting 18 of 119 words inside pauses on clip #1.
- `render_short.py`: draws frames with Pillow and pipes them to ffmpeg, because the Homebrew ffmpeg has no libass or drawtext. `--bleep` puts a tone over swears and masks them in the captions. Filler words stay in the audio but are left out of the captions.
- `week.py render|kit <week-NN.json>`: renders a week's clips into `~/Downloads/JT social clips/Shorts/` and writes `week-NN-kit.md`, which holds the X post text, YouTube title and description, and post date for each clip.

Clips that swear get two files: an uncensored one for X and a bleeped one for YouTube.
Nothing posts automatically. Each week's kit is approved by Matt before anything is scheduled.

## Scheduling (after Matt approves the week's kit)

Run `week.py stage <week.json>`, then from the repo root `source catalog/social/shorts/browser/x.sh` (it also loads `youtube.sh`). The Peak Mind Chrome profile is already signed in to both sites. Delete `.upload-tmp/` when finished. Week 1 was scheduled this way on 2026-11-01: 7 YouTube Shorts and 7 X posts, Mon/Wed/Fri at 12:00 PM ET.

- **YouTube Studio:** upload, then fill in title, description and "not made for kids". Click Next three times, open **Schedule**, then set the date and time.
  - The time options use a narrow no-break space ("12:00 PM"), so typing a time doesn't work.
  - On some screens the time list saves one slot off from the option clicked. `set_noon` keeps trying until the field reads 12:00 PM.
  - Confirm success with the "will be set to public on …" message, not by reading the page summary, which gets cut off when the Shorts list is behind the dialog.
  - If a run leaves drafts, finish them from the video's own page (`studio.youtube.com/video/<id>/edit` → **Edit draft**).
- **X:** the composer's **Schedule post** panel (`data-testid=scheduleOption`) has six selects (Month, Day, Year, Hour, Minute, AM/PM). Set them with the native value setter and a `change` event.
  - Only click the button when it reads **Schedule** and the panel says "Will send on <date> at 12:00 PM". Never click it while it says **Post**.
  - Check the result at `x.com/compose/post/unsent/scheduled`.
