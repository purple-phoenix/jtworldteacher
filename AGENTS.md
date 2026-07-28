# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.

## Podcast pipeline sharp edges

- **whisper-cli needs WAV, not `.m4a`.** The Homebrew `whisper-cli` build on this machine only reads WAV; feeding it a Space `.m4a` fails instantly with `error: failed to read audio data as wav` (exit 0 but no output files — easy to miss). `catalog/WORKFLOW.md` shows running whisper directly on `.m4a`, which no longer works. First convert: `ffmpeg -i audio/<slug>.m4a -ar 16000 -ac 1 -c:a pcm_s16le /tmp/<slug>.wav`, then `whisper-cli -m ~/.whisper-models/ggml-large-v3-turbo.bin -f /tmp/<slug>.wav -otxt -ovtt -of catalog/spaces/transcripts/<slug>`.
- **R2 bucket is `jtworldteacher-podcast`, not `jtworld-podcast`.** Upload with `rclone copy catalog/spaces/audio/<slug>.m4a r2:jtworldteacher-podcast/episodes/`. The `r2:` rclone remote's token cannot `ListBuckets` (`rclone lsd r2:` returns 403 AccessDenied) and `no_check_bucket = true` is set, so listing/probing a wrong bucket name returns misleading `directory not found` / `NoSuchBucket` — always address the bucket by its exact name. Public URLs are `https://media.jtworldteacher.com/episodes/<slug>.m4a` (serves HTTP 206 range requests). The astroai `~/github/astroai/.env` token is a *different* Cloudflare account (`astro-media` bucket) and cannot reach the podcast bucket.
- **Episode markdown convention** (see existing `site/src/content/episodes/*.md`): frontmatter has no `episode:` number and no `summary:`; body is `## About this episode` + `## Show notes` + `## Notable quotes` (older episodes use `## Topics` + `## Quotes`). The full transcript is NOT embedded in the episode body — it lives committed as `.txt`/`.vtt` under `catalog/spaces/transcripts/`. Validate with `cd site && npm run build` (checks the Zod schema in `src/content.config.ts` and regenerates `dist/feed.xml`).
- **Preserve the podcast M4A MIME type when uploading with rclone.** On macOS, rclone infers `.m4a` as `audio/mp4a-latm`, but these enclosures are MP4 containers and should serve as `audio/mp4`. Upload with `--metadata --metadata-set content-type=audio/mp4`; if only correcting metadata on an otherwise unchanged object, also use `--ignore-times` so rclone does not skip it. Verify the public `Content-Type`, `Content-Length`, and a `206` range response after upload.
- **Display episode `pubDate` in UTC.** Date-only frontmatter (`pubDate: 2026-07-05`) becomes UTC midnight via `z.coerce.date()`; formatting with local `Intl.DateTimeFormat` shifts the day west of UTC (e.g. July 5 → July 4 in America/New_York). Page formatters use `timeZone: "UTC"`; regression: `cd site && npm run test:pubdate-tz`. Leave RSS alone — it already emits the correct day.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
