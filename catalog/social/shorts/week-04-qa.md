# Week 4 preparation checks

Nothing posted or scheduled. All dates use 12:00 PM America/New_York (EST, UTC-05:00 in December).

## Cut verification

Each isolated final cut was transcribed again with Whisper DTW after trimming the source recording. The first and last words below come from those final-cut transcripts. Full word timings are retained on the mini in `/Users/mtmccarthy/peak-mind-shorts/.words/`.

| # | Date | First words | Last words | Seconds |
|---|---|---|---|---|
| 45 | 2026-12-05 | When you look at what | using way too much ketamine. | 31.70 |
| 46 | 2026-12-07 | You can't say, if I | the way that it is. | 39.17 |
| 47 | 2026-12-08 | My first job, I was | We weren't serious about it. | 77.45 |
| 48 | 2026-12-09 | But the real secret of | persistent predatory personality traits. | 70.91 |
| 49 | 2026-12-10 | there was an article about | for the people around us | 82.65 |
| 50 | 2026-12-11 | There are a lot of | emphasis is on the experiment. | 56.54 |
| 51 | 2026-12-12 | If we were viewing a | I were in that position. | 31.66 |
| 52 | 2026-12-13 | A Tibetan sand mandala. If | it up in a pile. | 70.62 |
| 63 | 2026-12-14 | I know with Neanderthals particularly, | very long for that reason. | 69.63 |
| 54 | 2026-12-15 | I think that our unconscious | past, present, and the future. | 87.70 |
| 55 | 2026-12-16 | A lot of us would | more than 10 to 1. | 70.40 |
| 56 | 2026-12-17 | A lot of us clutter. | it out into the ocean. | 71.53 |
| 57 | 2026-12-18 | What happened was Lily started | never hear about this anymore. | 58.90 |
| 58 | 2026-12-19 | you create a game right | without ever having dinosaurs exist | 42.92 |
| 59 | 2026-12-20 | Here's another assumption. Exponential growth. | right whales in the ocean. | 72.81 |
| 60 | Spare | And there's a big ethical | want to fuel escapist behaviors. | 30.97 |
| 61 | Spare | When you have a question, | listen to what they say. | 51.66 |
| 62 | Spare | The danger in this thinking, | of person to do it. | 62.42 |

## Selection decisions

Started with the new-source top 15. Dated picks favor stories, humor and thought experiments. No selected range was flagged estimated; all were independently aligned to the audio. The source files attribute these host monologues to JT, with no guest-led ranges selected.

- Moved false hope, primary-source research and coincidence cautions to undated spares: useful complete thoughts, but more advisory than the dated choices.
- Dropped constant reinvention from this batch: its ranked cue ends in an unfinished thought; shortening to the main payoff misses the 30-second requirement. Replaced with the book-and-time analogy.
- Added dolphin/UN lore, the fictional game-world history thought experiment and the alien-population/whale analogy for surprise and variety.
- Excluded all previously used, held and dropped moments; no vaccine content, guest-led selections, estimated ranges or repeated Edison, zombie, challenge-rating or score-chasing stories.
- Dropped #53 (the MacBook story, Dec 14) at Matt's request on 2026-11-16. It is kept in `week-04-dropped.json`; its videos moved to `/Users/mtmccarthy/peak-mind-shorts/week-04-dropped/`.
- Lilly stories are attributed accounts, not endorsements or verified contact. The game-world clip retains the explicit qualification that JT is not saying this happened.

## Platform files

X uses the uncensored file. YouTube Shorts, TikTok and Instagram use the bleeped version whenever present. Only the two Wednesday slots promote that evening’s live show. No staging or scheduling was run.

## Playback checks

All 20 HTTPS media links passed native video playback and seeking to 75 percent in fresh incognito browser tabs through the tailnet URL. Each reported 1080 by 1920 video, readyState 4 and no media error. The raw results are retained at <https://matts-mac-mini.tailebcf61.ts.net:5490/week-04/browser-checks.json>. This was a browser check of the phone-openable links, not a physical-phone test.

Caption spelling corrections after transcription: Samsung (Whisper: samson), and Lilly (Whisper: Lily). Spoken device wording is otherwise retained. All 20 files fully decoded with ffmpeg without errors. The contact sheet was visually checked for headline, caption and brand layout.

Bleep QA: all three detected swear windows across gas-station and MacBook clips showed a 1 kHz tone in the decoded bleeped file. Corrected-name renders were decoded and playback/seek checked again. HTTP range requests return 206, video/mp4 and the requested byte count; POST is rejected (501).
