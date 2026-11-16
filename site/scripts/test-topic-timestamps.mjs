#!/usr/bin/env node
/**
 * Regression: every mention in src/data/topics.ts must point at a real moment.
 *
 * For each mention:
 *   - the episode page exists and is not a draft;
 *   - the time (whole seconds) equals the start of a cue in the episode's
 *     transcript (catalog/spaces/transcripts/<audio-slug>.vtt) cut down to the
 *     whole second (floor, not rounded);
 *   - the time is inside the episode's durationSeconds.
 *
 * The transcript is found through the episode page's audioUrl, because two
 * episodes have a page name that differs from their audio name.
 *
 * Run with: npm run test:topics
 */

import { readFileSync, existsSync } from "node:fs";
import { dirname, join, basename } from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = join(siteRoot, "..");
const { TOPICS } = await import(join(siteRoot, "src/data/topics.ts"));

function frontmatterValue(text, key) {
  const m = text.match(new RegExp(`^${key}:\\s*"?([^"\\n]+?)"?\\s*$`, "m"));
  return m ? m[1] : null;
}

function cueStarts(vtt) {
  const starts = new Set();
  const re = /^(\d+):(\d{2}):(\d{2})\.\d{3}\s+-->/gm;
  let m;
  while ((m = re.exec(vtt))) {
    starts.add(Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]));
  }
  return starts;
}

const episodeCache = new Map();
function loadEpisode(slug) {
  if (episodeCache.has(slug)) return episodeCache.get(slug);
  let info = { error: null };
  const page = join(siteRoot, "src/content/episodes", `${slug}.md`);
  if (!existsSync(page)) {
    info.error = `no episode page ${slug}.md`;
  } else {
    const text = readFileSync(page, "utf8");
    const audioUrl = frontmatterValue(text, "audioUrl");
    const duration = Number(frontmatterValue(text, "durationSeconds"));
    const draft = frontmatterValue(text, "draft") === "true";
    const audioSlug = audioUrl ? basename(audioUrl).replace(/\.m4a$/, "") : null;
    const vttPath = audioSlug
      ? join(repoRoot, "catalog/spaces/transcripts", `${audioSlug}.vtt`)
      : null;
    if (draft) info.error = "episode is a draft";
    else if (!audioSlug || !duration) info.error = "missing audioUrl or durationSeconds";
    else if (!existsSync(vttPath)) info.error = `no transcript at ${vttPath}`;
    else info = { error: null, duration, starts: cueStarts(readFileSync(vttPath, "utf8")) };
  }
  episodeCache.set(slug, info);
  return info;
}

let checked = 0;
const failures = [];
for (const topic of TOPICS) {
  for (const ep of topic.episodes) {
    const info = loadEpisode(ep.slug);
    for (const m of ep.mentions) {
      checked++;
      const where = `${topic.id} / ${ep.slug} @ ${m.t}s`;
      if (info.error) failures.push(`${where}: ${info.error}`);
      else if (!Number.isInteger(m.t) || m.t < 0) failures.push(`${where}: time is not a whole number of seconds`);
      else if (m.t > info.duration) failures.push(`${where}: past durationSeconds (${info.duration})`);
      else if (!info.starts.has(m.t)) failures.push(`${where}: no transcript cue starts at this second`);
    }
  }
}

if (failures.length) {
  for (const f of failures) console.error(`FAIL: ${f}`);
  console.error(`${failures.length} of ${checked} mentions failed`);
  process.exit(1);
}
console.log(`ok: all ${checked} topic mentions point at a cue start inside the episode`);
