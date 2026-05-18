# Podcast publishing workflow

How "JT — Astrology & Simulation Theory" gets from a downloaded X Space → public podcast episode.

## One-time setup (do this before first publish)

### 1. Audio hosting — Cloudflare R2

GitHub Pages can't serve large media files at scale. Audio lives on R2.

1. Sign up at <https://dash.cloudflare.com/> (free).
2. R2 → Create bucket → name it `jtworld-podcast` (or similar).
3. Settings → "Public access" → "Connect custom domain" → enter `media.jtworldteacher.com`. (Cloudflare will give you a CNAME target to add at Porkbun — already covered in §4 below.) The audio URL pattern becomes `https://media.jtworldteacher.com/episodes/<slug>.m4a`.
4. Generate an API token (R2 → Manage R2 API Tokens → "Object Read & Write" on this bucket). Save the **Access Key ID** + **Secret** somewhere safe (1Password). You'll only need these locally to upload — they don't go in the repo.
5. After uploading the first audio file, update `audioUrl` in each `site/src/content/episodes/*.md` to point at `https://media.jtworldteacher.com/episodes/<slug>.m4a`.

### 2. Cover art

Apple Podcasts requires square JPG/PNG, **3000 × 3000 px**, sRGB, < 500 KB.

- Drop it at `site/public/podcast-cover.jpg`.
- Same image gets used for every episode unless an episode sets its own `image:` frontmatter (also a path relative to `site/public/`).
- For the show artwork on R2 (some directories prefer the cover art served from the same origin as the audio), upload a copy to R2 too at `cover.jpg`.

### 3. Owner email + show metadata

Edit `site/src/pages/feed.xml.ts` — the `SHOW` constant at the top has placeholders for `ownerEmail`, category, etc. Apple Podcasts will email this address for verification.

### 4. Custom domain

Site domain: **`jtworldteacher.com`** (registered at Porkbun).

The site URL is configured in `site/astro.config.mjs` (`site: 'https://jtworldteacher.com'`) and a `CNAME` file lives at `site/public/CNAME` so GitHub Pages picks it up on deploy.

**DNS records to add at Porkbun** (Dashboard → jtworldteacher.com → DNS):

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| ALIAS | (blank) | `purple-phoenix.github.io` | 600 |
| CNAME | `www` | `purple-phoenix.github.io` | 600 |
| CNAME | `media` | `<R2 bucket public hostname>` (set after R2 setup, see step 1) | 600 |

If Porkbun's ALIAS doesn't work cleanly, use 4 A records on apex instead:
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

See [`catalog/WORKFLOW.md`](catalog/WORKFLOW.md). You'll end up with:
- `catalog/spaces/audio/YYYY-MM-DD-slug.m4a`
- `catalog/spaces/transcripts/YYYY-MM-DD-slug.txt`

### 2. Upload audio to R2

Easiest is the dashboard: R2 → bucket → Upload → drop the `.m4a` into an `episodes/` folder. Or use `rclone`:

```bash
# one-time rclone config
rclone config   # follow prompts: New remote → name "r2" → S3 → Cloudflare R2 → paste keys

# upload
rclone copy catalog/spaces/audio/YYYY-MM-DD-slug.m4a r2:jtworld-podcast/episodes/
```

The final URL will be `<R2_DOMAIN>/episodes/YYYY-MM-DD-slug.m4a`.

### 3. Create the episode markdown

Create `site/src/content/episodes/YYYY-MM-DD-slug.md`:

```markdown
---
title: "Episode title"
pubDate: 2026-04-01
description: "Short one-line description for the RSS feed."
audioUrl: "https://<R2_DOMAIN>/episodes/YYYY-MM-DD-slug.m4a"
audioLength: 64460131   # exact bytes — `stat -f "%z" file.m4a` on macOS
audioType: "audio/mp4"   # m4a / aac is audio/mp4; mp3 is audio/mpeg
duration: "1:30:22"     # hh:mm:ss
durationSeconds: 5422
episode: 2              # episode number (optional but recommended)
episodeType: "full"     # full | trailer | bonus
explicit: false
draft: false            # set to true to keep it out of the feed while drafting
spaceUrl: "https://x.com/i/spaces/..."
spaceId: "1XXXXXXXXXX"
---

## About this episode

Show notes go here. Use multiple paragraphs.

## Transcript

(Paste cleaned transcript here, or include it via a separate markdown chunk.)
```

### 4. Build + preview locally

```bash
cd site
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

Commit + push to `main`. The GH Actions workflow at `.github/workflows/deploy.yml` builds and deploys to GitHub Pages automatically.

```bash
git add site/src/content/episodes/YYYY-MM-DD-slug.md
git commit -m "Add episode: <title>"
git push
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

Save the public Spotify / Apple URLs after submission and paste them into:
- `site/src/pages/index.astro` (the "Spotify" / "Apple Podcasts" `<li>`s)
- `site/src/pages/podcast/index.astro` (same)

## File layout

```
site/
├── astro.config.mjs           # site URL + base path
├── src/
│   ├── content.config.ts      # episode schema
│   ├── content/
│   │   └── episodes/
│   │       └── YYYY-MM-DD-slug.md     # one per episode
│   ├── layouts/
│   │   └── Layout.astro
│   └── pages/
│       ├── index.astro                 # home
│       ├── feed.xml.ts                 # RSS feed (the podcast feed)
│       └── podcast/
│           ├── index.astro             # episode list
│           └── [slug].astro            # episode detail page
└── public/
    └── podcast-cover.jpg               # 3000×3000 cover art (you need to add this)
```

## Notes & gotchas

- **`audioLength` is required by Apple Podcasts** — it must be the exact byte count of the file on R2. Get it via `stat -f "%z" file.m4a` (macOS) or `wc -c < file.m4a`.
- **m4a/AAC mimetype is `audio/mp4`**, not `audio/m4a`. Don't change this.
- **Don't move audio URLs after publishing** — clients cache enclosure URLs; a moved file = no episode for some listeners.
- **Don't change the feed URL after submitting** — same reason, but worse: total subscriber loss. Use a custom domain from day one.
- **Episode `draft: true`** keeps an episode in the repo but out of the RSS feed and the site episode list. Useful for staging.
