# Progress

Checkpoint of where the `jtworldteacher` project stands. Update as work continues.

## What this project is

A podcast + site for **JT McCarthy** (X: [@McCarthy_JT](https://x.com/McCarthy_JT)) — Technical Remote Viewing, Vedic / mundane astrology, "Against the Archons" Gnostic framing, UFOx critique. Built and operated by his brother **Matt McCarthy** with JT's consent.

Show name: **"JT — Astrology & Simulation Theory."**

Two-track repo:
- `site/` — public Astro site, deployed to GitHub Pages.
- `catalog/` — private research (X post screenshots, Space audio, transcripts, analysis notes). Not published.

## Live URLs

| What | URL |
|---|---|
| Site | <https://jtworldteacher.com> |
| RSS feed | <https://jtworldteacher.com/feed.xml> |
| Episode list | <https://jtworldteacher.com/podcast/> |
| Cover art | <https://jtworldteacher.com/podcast-cover.jpg> |
| Audio (one example) | <https://media.jtworldteacher.com/episodes/2026-04-01-the-return-of-the-king.m4a> |

## Infrastructure

- **Domain**: `jtworldteacher.com` (registered at Porkbun, DNS managed by Cloudflare). Nameservers switched Porkbun → Cloudflare during setup.
- **Site host**: GitHub Pages via `.github/workflows/deploy.yml` (triggers on push to `main` touching `site/**` or the workflow file, or manual dispatch). Merging a PR to `main` deploys.
- **HTTPS**: GH Pages Let's Encrypt cert, enforced.
- **Audio host**: Cloudflare R2 bucket `jtworldteacher-podcast`, public via custom domain `media.jtworldteacher.com`. All audio under `/episodes/<slug>.m4a`.
- **RSS feed namespaces**: iTunes, content, atom, podcast (PSP-1 compliant). Validator-checked at <https://podba.se/validate/>; only red was "byte-range support" which is a false negative (R2 returns HTTP 206 correctly — verified by curl).
- **rclone** configured locally for the audio upload workflow (see `~/.config/rclone/rclone.conf`, R2 API token saved in 1Password).

## Episode status

24 episodes total (all published, all in the RSS feed), oldest first. "Stub" means the page still says "Detailed show notes coming":

| Date | Title | Show notes | Audio on R2 | Live |
|---|---|---|---|---|
| 2025-05-28 | BIGFOOT presents the state of reality with remote viewers Morgan Farrell & Dan Mann | ⏳ stub — transcript ready | ✅ | ✅ (as stub) |
| 2025-05-31 | THE ASTRO RV PROJECT with remote viewer Morgan Farrell | ⏳ stub — transcript ready | ✅ | ✅ (as stub) |
| 2025-06-20 | Sacred time and synchronicity storytime | ⏳ stub (pre-show fragment, 8 min) | ✅ | ✅ (as stub) |
| 2025-06-27 | Thinking about World War 3 | ⏳ stub — transcript ready | ✅ | ✅ (as stub) |
| 2025-07-16 | Human nature and the paranormal | ⏳ stub — transcript ready | ✅ | ✅ (as stub) |
| 2026-01-11 | Karmic Deep Impact | ✅ enriched | ✅ | ✅ |
| 2026-01-20 | Thunderdome: #SaturnNeptune and the Archons | ✅ enriched | ✅ | ✅ |
| 2026-01-27 | The Empire Never Ended: Secret of the "Psychic Gene" | ✅ enriched | ✅ | ✅ |
| 2026-03-19 | The Long Emergency | ✅ enriched | ✅ | ✅ |
| 2026-03-27 | You're Screwed. Astrology Questions Answered | ✅ enriched | ✅ | ✅ |
| 2026-04-01 | The Return of the King | ✅ enriched | ✅ | ✅ |
| 2026-04-02 | The Against the Archons emergent archetype in media | ✅ enriched | ✅ | ✅ |
| 2026-04-05 | Astro RV Alert! | ✅ enriched | ✅ | ✅ |
| 2026-04-22 | Suck it, Dan Waites | ✅ enriched | ✅ | ✅ |
| **2026-04-25** | **Technical Remote Viewing** | ⏳ **stub — transcript ready (365K, 7-hour audio); needs agent enrichment** | ✅ | ✅ (as stub) |
| 2026-04-29 | Oriental Archons! | ✅ enriched | ✅ | ✅ |
| 2026-05-02 | Final Feedback... Intuitive Underground were right about everything | ✅ enriched | ✅ | ✅ |
| 2026-05-07 | UFOx: THE CRUSADE WITHIN UFOLOGY | ✅ enriched | ✅ | ✅ |
| 2026-05-08 | Disclosure and Technical Remote Viewing | ✅ enriched | ✅ | ✅ |
| 2026-07-04 | The Revelation of the Hierarchy (Peak Mind) | ✅ enriched | ✅ | ✅ |
| 2026-07-05 | American Disclosure (Peak Mind) | ✅ enriched | ✅ | ✅ |
| 2026-09-02 | Technical Remote Viewing and the Kill Shot (Peak Mind) | ✅ enriched | ✅ | ✅ |
| 2026-09-09 | Intuitive Underground and the Power of Remote Viewing (Peak Mind) | ✅ enriched | ✅ | ✅ |
| 2026-09-16 | The World Tree and the Eclipse in Leo (Peak Mind) | ✅ enriched | ✅ | ✅ |

## Open todos

1. **Enrich the Technical Remote Viewing (Apr 25) episode** — its transcript exists at `catalog/spaces/transcripts/2026-04-25-technical-remote-viewing.txt` (365 KB, the 7-hour episode). Needs a dispatched agent to read it and produce show notes in the same format as the other 13. Then update `site/src/content/episodes/2026-04-25-technical-remote-viewing.md` (currently still has the "Detailed show notes coming" stub), commit + push.
2. **Submit RSS feed to podcast directories** — likely already done by Matt, but worth confirming. The feed URL is `https://jtworldteacher.com/feed.xml`. Owner email in the feed is `josephtimothymccarthy@gmail.com` (for Apple verification).
   - Apple Podcasts Connect: <https://podcastsconnect.apple.com/>
   - Spotify for Podcasters: <https://podcasters.spotify.com/>
   - YouTube Music: <https://podcasters.youtube.com/>
   - Amazon Music: <https://podcasters.amazon.com/>
   - After Apple accepts, Overcast / Pocket Casts / Castro / Castbox auto-pick it up.
3. **Real cover art** (cosmetic, not blocking) — current art at `site/public/podcast-cover.jpg` is a 3000×3000 typographic placeholder using the site's cream/ink/purple palette. Apple-spec compliant but generic. Replace whenever JT provides art he likes.
4. **Wire up the placeholder links**: Apple and YouTube are still `href="#"` (with the "soon" treatment) in `index.astro`, `podcast/index.astro`, `podcast/[slug].astro` and `Footer.astro`, and the footer's "One-time contribution" link is also `#`. The contact email is already wired (`mailto:` in `Footer.astro` and `consultations.astro`). (Spotify is now wired to the public show `https://open.spotify.com/show/033LHLE9BxNUNTLSzmDqfC` across `index.astro`, `podcast/index.astro`, `podcast/[slug].astro`, and `Footer.astro`.)
5. **Site bio / about copy**: `about.astro` still has the placeholder ~300-word bio (marked with a TODO). Replace it with the real bio.
6. **Ownership transfer to JT** when he's ready — update `feed.xml.ts` `SHOW.ownerEmail` to JT's address and re-verify with directories; add him as user in Apple/Spotify dashboards.

## How to add a new episode

When JT does a new X Space:

1. Add the tweet URL to `catalog/spaces/queue.txt`.
2. Run `bash catalog/scripts/parallel-pipeline.sh catalog/spaces/queue.txt [PARALLELISM]`. It downloads the audio and writes the catalog stub post (`download-space.sh`), then transcribes it to `.txt` + `.vtt` (`transcribe-pending.sh`, which converts to WAV first).
3. Trim the audio to the show and shift the transcript to match (see AGENTS.md, "Episodes are edited to the show").
4. Run `bash catalog/scripts/generate-episode-pages.sh` to create the stub site episode page. It never overwrites an existing page.
5. For full show notes, dispatch an agent to read the transcript and write the notes in the convention described in AGENTS.md.
6. Upload the audio to R2: `rclone copy catalog/spaces/audio/<slug>.m4a r2:jtworldteacher-podcast/episodes/ --metadata --metadata-set content-type=audio/mp4`. Then verify the public `Content-Type`, `Content-Length` and a `206` range response.
7. Optionally, add the episode to the topic hubs in `site/src/data/topics.ts`.
8. Open a PR. Merging to `main` deploys via GH Actions, and the episode goes live and appears in the RSS feed within a minute or so.

The Peak Mind Spotify upload is a separate manual step: see `catalog/PEAK_MIND_SPOTIFY.md`.

Full workflow doc: `PODCAST.md` (root). Catalog workflow: `catalog/WORKFLOW.md`.

## Key file locations

```
jtworldteacher/
├── AGENTS.md                     # agent memory: pipeline sharp edges (CLAUDE.md imports it)
├── PODCAST.md                    # publishing workflow (R2 setup, episode add, directory submission)
├── PROGRESS.md                   # this file
├── docs/platform-plan.md         # platform strategy notes
├── .github/workflows/deploy.yml  # GH Pages deploy
├── site/
│   ├── astro.config.mjs          # site URL = jtworldteacher.com
│   ├── scripts/test-pubdate-tz.mjs  # `npm run test:pubdate-tz` regression check
│   ├── src/
│   │   ├── content.config.ts     # episode schema
│   │   ├── content/episodes/     # one .md per episode (publishable)
│   │   ├── components/           # Nav, Footer, AudioPlayer, EpisodeCover, …
│   │   ├── data/site.ts          # series + consultation offerings
│   │   ├── data/topics.ts        # topic hubs: topic → episodes + timestamps
│   │   ├── layouts/Layout.astro  # site-wide layout (<head>, SEO meta, nav + footer)
│   │   └── pages/
│   │       ├── index.astro       # home
│   │       ├── about.astro, writing.astro, consultations.astro
│   │       ├── feed.xml.ts       # RSS feed (iTunes + podcast namespace)
│   │       ├── podcast/
│   │       │   ├── index.astro   # episode list
│   │       │   └── [slug].astro  # episode page (audio player, show notes, topics; `#t=<sec>` cues the player)
│   │       └── topics/
│   │           ├── index.astro   # /topics/ index
│   │           └── [topic].astro # one hub page per topic in data/topics.ts
│   └── public/
│       ├── CNAME                 # custom-domain config for GH Pages
│       └── podcast-cover.jpg     # 3000×3000 cover art
└── catalog/                      # private research (NOT deployed)
    ├── README.md
    ├── WORKFLOW.md               # catalog-side workflow
    ├── PEAK_MIND_SPOTIFY.md      # Peak Mind manual Spotify upload-kit runbook
    ├── media/                    # screenshots of JT's X posts
    ├── posts/                    # one .md per cataloged post or Space
    ├── spaces/
    │   ├── audio/                # m4a (gitignored — large)
    │   ├── transcripts/          # whisper-cpp output, tracked in git
    │   └── queue.txt             # URLs to be processed
    └── scripts/
        ├── parallel-pipeline.sh  # parallel download + sequential transcribe
        ├── download-space.sh     # single-URL download
        ├── transcribe-pending.sh # transcribe any m4a lacking a .txt
        ├── process-spaces.sh     # older sequential script (still works)
        ├── generate-episode-pages.sh  # generate stub site episode pages
        ├── prepare_peak_mind_kit.py   # Peak Mind Spotify kit (local only; never uploads)
        └── tests/
```

## Tools required locally

- `yt-dlp` + `ffmpeg` (brew)
- `whisper-cpp` (brew) + model at `~/.whisper-models/ggml-large-v3-turbo.bin`
- `rclone` (brew) configured with R2 credentials
- `imagemagick` (brew) — only if regenerating cover art

## Gotchas / known issues

- **Slugify truncates at 60 chars, mid-word** — in `catalog/scripts/download-space.sh`, the `slugify()` function does `cut -c1-60` which can chop a word in half. E.g. "Final Feedback... Intuitive Underground were right about everything" became `...were-right-about-everyt`. The truncated slug becomes the audio filename and R2 URL — once published you don't want to rename it (would break the RSS enclosure). Either accept ugly truncations or improve slugify to cut at word boundaries before adding new long-titled episodes.
- **Audio filename and episode-page slug can diverge** — for 2 episodes (Thunderdome, Final Feedback) the site episode `.md` was named with a cleaner slug than the auto-generated audio filename. We resolved by setting `audioUrl` in frontmatter to the actual R2 audio filename, independent of the `.md` filename. **Pattern to follow**: audio filename is canonical for R2 URLs (never rename after upload — breaks subscribers); episode `.md` filename is canonical for `/podcast/<slug>/` website URL; they can differ; reconcile via the `audioUrl` frontmatter field.
- **podba.se validator reports byte-range support as failing** — false positive. R2 returns proper HTTP 206 Partial Content with Content-Range header on our audio. Verified by curl: `curl -sI -H "Range: bytes=0-1023" https://media.jtworldteacher.com/episodes/<file>.m4a` returns 206. Apple does its own check and the audio passes. Ignore this red mark in the validator.
- **Astro `import.meta.env.BASE_URL` was unreliable in `feed.xml.ts`** during the GH-Pages-subpath phase — we abandoned URL-object resolution and used direct string concatenation in `feed.xml.ts` (search for `siteRoot` / `absolute`). It works now with the apex domain, but if anyone re-introduces a base path later, the existing string-concat form should keep working.

## Unknown state (from the previous session)

- **Whether RSS feed was actually submitted to Apple Podcasts Connect / Spotify / YouTube Music / Amazon Music.** Matt said he would do it but the previous session ended before confirming. Since then a public Spotify show (`https://open.spotify.com/show/033LHLE9BxNUNTLSzmDqfC`) has been linked across the site. Apple, YouTube and Amazon are still unconfirmed, and the site's Apple and YouTube links are still placeholders. Next agent should ask or check via the inboxes for verification emails to `josephtimothymccarthy@gmail.com`. If not yet submitted, walk through the directory submission steps in PODCAST.md §"First-time directory submission."

## Auxiliary memory

Claude's project memory for this repo is at `~/.claude/projects/-Users-mattmccarthy-github-jtworldteacher/memory/`:
- `user_brother_jt.md` — Matt is building this for JT, not for himself
- `project_overview.md` — site / catalog / podcast architecture
- `jt_voice_and_themes.md` — JT's coined vocabulary, rhetorical moves, named-person evaluations; load-bearing for writing copy that sounds like him
- `peak_mind_podcast.md` — the Wednesday Peak Mind show (JT + Matt) and how new episodes are found

Future Claude sessions on this repo should read those before writing any site copy.
