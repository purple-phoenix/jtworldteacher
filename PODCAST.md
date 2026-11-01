# Podcast publishing workflow

How "JT — Astrology & Simulation Theory" gets from a downloaded X Space → public podcast episode.

## One-time setup (do this before first publish)

### 1. Audio hosting — Cloudflare R2

GitHub Pages can't serve large media files at scale. Audio lives on R2.

1. Sign up at <https://dash.cloudflare.com/> (free).
2. R2 → Create bucket. The live bucket is named `jtworldteacher-podcast`. Always address it by that exact name: the local token can't list buckets, so a wrong name fails with misleading errors (see AGENTS.md).
3. Settings → "Public access" → "Connect custom domain" → enter `media.jtworldteacher.com`. (Cloudflare will give you a CNAME target to add at Porkbun — already covered in §4 below.) The audio URL pattern becomes `https://media.jtworldteacher.com/episodes/<slug>.m4a`.
4. Generate an API token (R2 → Manage R2 API Tokens → "Object Read & Write" on this bucket). Save the **Access Key ID** + **Secret** somewhere safe (1Password). You'll only need these locally to upload — they don't go in the repo.
5. After uploading the first audio file, update `audioUrl` in each `site/src/content/episodes/*.md` to point at `https://media.jtworldteacher.com/episodes/<slug>.m4a`.

### 2. Cover art

Apple Podcasts requires square JPG/PNG, **3000 × 3000 px**, sRGB, < 500 KB.

- Drop it at `site/public/podcast-cover.jpg`.
- Same image gets used for every episode unless an episode sets its own `image:` frontmatter (also a path relative to `site/public/`).
- For the show artwork on R2 (some directories prefer the cover art served from the same origin as the audio), upload a copy to R2 too at `cover.jpg`.

### 3. Owner email + show metadata

Show metadata lives in the `SHOW` constant at the top of `site/src/pages/feed.xml.ts` (title, `ownerEmail`, category, etc.). It's already filled in; `ownerEmail` is currently `josephtimothymccarthy@gmail.com`. Apple Podcasts emails this address for verification.

### 4. Custom domain

Site domain: **`jtworldteacher.com`** (registered at Porkbun).

The site URL is configured in `site/astro.config.mjs` (`site: 'https://jtworldteacher.com'`) and a `CNAME` file lives at `site/public/CNAME` so GitHub Pages picks it up on deploy.

**DNS is managed at Cloudflare.** The domain is still registered at Porkbun, but its nameservers were switched to Cloudflare during setup, so add or edit records in the Cloudflare dashboard. Today the apex and `media` resolve to Cloudflare (proxied), and `www` is a CNAME to `purple-phoenix.github.io`. The records used at setup were:

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| ALIAS | (blank) | `purple-phoenix.github.io` | 600 |
| CNAME | `www` | `purple-phoenix.github.io` | 600 |
| CNAME | `media` | `<R2 bucket public hostname>` (set after R2 setup, see step 1) | 600 |

If an apex ALIAS/CNAME doesn't work cleanly, use 4 A records on apex instead:
- `185.199.108.153`
- `185.199.109.153`
- `185.199.110.153`
- `185.199.111.153`
(and optionally the matching AAAA records: `2606:50c0:8000::153` through `2606:50c0:8003::153`)

**Then in the GitHub repo settings:**
1. Settings → Pages → Custom domain → enter `jtworldteacher.com` → Save.
2. Wait ~1-5 min for DNS to propagate and GH Pages to provision HTTPS.
3. Check the "Enforce HTTPS" box once it's offered.

**Audio host:** Set the R2 bucket's public custom domain to `media.jtworldteacher.com` (Cloudflare R2 → Settings → Custom Domains). Episode `audioUrl`s in the markdown should then look like `https://media.jtworldteacher.com/episodes/<slug>.m4a`. Keeping audio on its own subdomain means we can swap hosts later (move from R2 to S3, etc.) by changing one DNS record — episode URLs stay valid forever.

## Per-episode workflow

For each Space you want to publish:

### 1. Download + transcribe

See [`catalog/WORKFLOW.md`](catalog/WORKFLOW.md). Whisper needs a 16 kHz mono WAV, not the `.m4a`. You'll end up with:
- `catalog/spaces/audio/YYYY-MM-DD-slug.m4a`
- `catalog/spaces/transcripts/YYYY-MM-DD-slug.txt` and `.vtt`

Then trim the audio to the show (hold music and pre-show chatter at the start, dead air at the end, nothing inside), and shift the transcript to match. The procedure is in AGENTS.md, "Episodes are edited to the show". Every later step uses the edited file.

### 2. Upload audio to R2

Easiest is the dashboard: R2 → bucket → Upload → drop the `.m4a` into an `episodes/` folder. Or use `rclone`:

```bash
# one-time rclone config
rclone config   # follow prompts: New remote → name "r2" → S3 → Cloudflare R2 → paste keys

# upload (keep the MP4 MIME type; rclone on macOS would otherwise send audio/mp4a-latm)
rclone copy catalog/spaces/audio/YYYY-MM-DD-slug.m4a r2:jtworldteacher-podcast/episodes/ \
  --metadata --metadata-set content-type=audio/mp4
```

The final URL will be `https://media.jtworldteacher.com/episodes/YYYY-MM-DD-slug.m4a`. Check that it serves `Content-Type: audio/mp4`, the right `Content-Length`, and a `206` for a range request.

### 3. Create the episode markdown

`bash catalog/scripts/generate-episode-pages.sh` creates a stub page for every audio file that doesn't have one yet; it never overwrites. Or create `site/src/content/episodes/YYYY-MM-DD-slug.md` by hand. Follow the existing episodes:

```markdown
---
title: "Episode title"
pubDate: 2026-04-01
description: "Short one-line description for the RSS feed."
audioUrl: "https://media.jtworldteacher.com/episodes/YYYY-MM-DD-slug.m4a"
audioLength: 64460131   # exact bytes of the edited file — `stat -f "%z" file.m4a` on macOS
audioType: "audio/mp4"   # m4a / aac is audio/mp4; mp3 is audio/mpeg
duration: "1:30:22"     # hh:mm:ss
durationSeconds: 5422
episodeType: "full"     # full | trailer | bonus
explicit: false
draft: false            # set to true to keep it out of the feed while drafting
spaceUrl: "https://x.com/i/spaces/..."
spaceId: "1XXXXXXXXXX"
---

## About this episode

A few paragraphs on what the episode is about.

## Show notes

- Bulleted rundown of the segments

## Notable quotes

> "A line from the transcript."
```

The house style omits `episode:` and `summary:` in the frontmatter, even though the schema allows them. Don't embed the transcript in the page; it stays committed under `catalog/spaces/transcripts/`. To list the episode on the topic hubs, add it to `site/src/data/topics.ts`. Timestamps there are seconds into the edited audio.

### 4. Build + preview locally

```bash
cd site
npm run build   # validates frontmatter against src/content.config.ts and the topic map; regenerates dist/feed.xml
npm run dev
# open http://localhost:4321/podcast/ to verify the episode appears
# open http://localhost:4321/feed.xml to verify the RSS is valid
```

Validate the feed:

```bash
curl -s http://localhost:4321/feed.xml > /tmp/feed.xml
# then paste into https://podba.se/validate/ or https://castfeedvalidator.com/
```

### 5. Deploy

Commit on a branch and open a PR. Merging to `main` (any change under `site/**`) runs `.github/workflows/deploy.yml`, which builds the site and deploys it to GitHub Pages.

```bash
git switch -c add-episode-YYYY-MM-DD
git add site/src/content/episodes/YYYY-MM-DD-slug.md catalog/
git commit -m "Add episode: <title>"
git push -u origin HEAD   # then open the PR
```

## First-time directory submission

Do this **once**, after the first non-draft episode is live and the feed validates.

| Directory | Where | How long |
|---|---|---|
| **Apple Podcasts** | <https://podcastsconnect.apple.com/> → New Show → paste your feed URL | 1–7 days manual review |
| **Spotify** | <https://podcasters.spotify.com/> → Add or claim podcast → paste feed URL | Usually < 24 hr |
| **YouTube Music** | <https://podcasters.youtube.com/> → Add or claim → paste feed URL | < 24 hr |
| **Amazon Music** | <https://podcasters.amazon.com/> | < 48 hr |
| **iHeartRadio** | <https://www.iheart.com/content/submit-your-podcast/> | Variable |
| **Overcast, Pocket Casts, Castro, Castbox** | Auto-discovered once Apple accepts | — |

Save the public Spotify / Apple / YouTube URLs after submission and paste them into the platform links in:
- `site/src/pages/index.astro`
- `site/src/pages/podcast/index.astro`
- `site/src/pages/podcast/[slug].astro`
- `site/src/components/Footer.astro`

Spotify is already wired (`https://open.spotify.com/show/033LHLE9BxNUNTLSzmDqfC`). Apple and YouTube are still `#` placeholders with the "soon" treatment.

## File layout

```
site/
├── astro.config.mjs           # site URL (https://jtworldteacher.com)
├── src/
│   ├── content.config.ts      # episode schema
│   ├── content/
│   │   └── episodes/
│   │       └── YYYY-MM-DD-slug.md     # one per episode
│   ├── data/
│   │   └── topics.ts                   # topic hubs: topic → episodes + timestamps
│   ├── layouts/
│   │   └── Layout.astro
│   └── pages/
│       ├── index.astro                 # home
│       ├── feed.xml.ts                 # RSS feed (the podcast feed)
│       ├── podcast/
│       │   ├── index.astro             # episode list
│       │   └── [slug].astro            # episode detail page (#t=<seconds> cues the player)
│       └── topics/
│           ├── index.astro             # /topics/ index
│           └── [topic].astro           # one page per topic
└── public/
    ├── CNAME                           # custom domain for GH Pages
    └── podcast-cover.jpg               # 3000×3000 cover art
```

## Notes & gotchas

- **`audioLength` is required by Apple Podcasts** — it must be the exact byte count of the file on R2. Get it via `stat -f "%z" file.m4a` (macOS) or `wc -c < file.m4a`.
- **m4a/AAC mimetype is `audio/mp4`**, not `audio/m4a`. Don't change this.
- **Don't move audio URLs after publishing** — clients cache enclosure URLs; a moved file = no episode for some listeners.
- **Don't change the feed URL after submitting** — same reason, but worse: total subscriber loss. Use a custom domain from day one.
- **Episode `draft: true`** keeps an episode in the repo but out of the RSS feed and the site episode list. Useful for staging. A draft episode that is still listed in `site/src/data/topics.ts` fails the build, so remove it there first.
