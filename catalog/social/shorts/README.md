# Peak Mind shorts

Vertical (1080x1920) videos for X and YouTube Shorts, made from the approved clips in `../clips/`.

The look is type only, with no generated imagery: the voice is JT's and real, and AI art next to it reads as "AI slop" (decided with Matt on 2026-11-01).
Each video has a headline, word-by-word captions with the spoken word highlighted, "Recorded live on X" with the date, a live waveform and @PeakMindShow.

- `align_words.py`: word timings from whisper.cpp DTW, shifted 0.05 s earlier and snapped out of pauses. The default timestamps drifted, putting 18 of 119 words inside pauses on clip #1.
- `render_short.py`: draws frames with Pillow and pipes them to ffmpeg, because the Homebrew ffmpeg has no libass or drawtext. `--bleep` puts a tone over swears and masks them in the captions. Filler words stay in the audio but are left out of the captions.
- `week.py render|kit <week-NN.json>`: renders a week's clips into `~/Downloads/JT social clips/Shorts/` and writes `week-NN-kit.md`, which holds the X post text, YouTube title and description, and post date for each clip.

Clips that swear get two files: an uncensored one for X and a bleeped one for YouTube.
Nothing posts automatically. Each week's kit is approved by Matt before anything is scheduled.
