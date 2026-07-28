#!/usr/bin/env node
/**
 * Regression: date-only episode pubDates must render the frontmatter calendar
 * day even when the build runs in a US timezone (UTC-offset).
 *
 * Reproduces the scout finding: pubDate 2026-07-05 rendered as July 4 under
 * America/New_York because Intl.DateTimeFormat used local time on a UTC-midnight Date.
 *
 * Run with: TZ=America/New_York npm run test:pubdate-tz
 * (or via npm run test:pubdate-tz, which sets TZ)
 */

import { spawnSync } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const tz = process.env.TZ || "";

function fail(msg) {
  console.error(`FAIL: ${msg}`);
  process.exit(1);
}

function ok(msg) {
  console.log(`ok: ${msg}`);
}

if (tz !== "America/New_York") {
  fail(
    `expected TZ=America/New_York (got ${JSON.stringify(tz)}). ` +
      `This test only proves the bug under a non-UTC offset.`,
  );
}

// Sanity: same Date coercion as Astro/z.coerce.date() for "2026-07-05"
const coerced = new Date("2026-07-05");
if (coerced.toISOString() !== "2026-07-05T00:00:00.000Z") {
  fail(`unexpected Date coercion: ${coerced.toISOString()}`);
}

const localShifted = new Intl.DateTimeFormat("en-US", {
  month: "long",
  day: "numeric",
  year: "numeric",
}).format(coerced);
if (localShifted !== "July 4, 2026") {
  fail(
    `environment did not reproduce local shift (got ${JSON.stringify(localShifted)}; expected "July 4, 2026")`,
  );
}
ok("local formatting still shifts date-only UTC midnight to July 4 (precondition)");

const build = spawnSync("npm", ["run", "build"], {
  cwd: siteRoot,
  env: { ...process.env, TZ: "America/New_York" },
  encoding: "utf8",
  stdio: ["ignore", "pipe", "pipe"],
});
if (build.status !== 0) {
  console.error(build.stdout);
  console.error(build.stderr);
  fail(`astro build exited ${build.status}`);
}
ok("astro build completed under TZ=America/New_York");

function readDist(rel) {
  const p = join(siteRoot, "dist", rel);
  if (!existsSync(p)) fail(`missing build output: dist/${rel}`);
  return readFileSync(p, "utf8");
}

const home = readDist("index.html");
const episode = readDist("podcast/2026-07-05-american-disclosure/index.html");
const podcastIndex = readDist("podcast/index.html");
const feed = readDist("feed.xml");

/** Extract a short window around the first match of `needle` for scoped asserts. */
function contextAround(html, needle, radius = 400) {
  const i = html.indexOf(needle);
  if (i < 0) return null;
  return html.slice(Math.max(0, i - radius), Math.min(html.length, i + needle.length + radius));
}

// Homepage latest card (American Disclosure) uses short format: "Jul 5, 2026"
const homeCtx = contextAround(home, "American Disclosure");
if (!homeCtx) fail("homepage missing American Disclosure latest card");
if (!homeCtx.includes("Jul 5, 2026")) {
  fail(`homepage American Disclosure missing "Jul 5, 2026" (got shifted date). Context: ${homeCtx.slice(0, 200)}`);
}
if (homeCtx.includes("Jul 4, 2026")) {
  fail(`homepage American Disclosure still shows "Jul 4, 2026" — timezone shift not fixed`);
}
ok('homepage shows "Jul 5, 2026" for American Disclosure');

// Episode page uses long format: "Sunday, July 5, 2026"
if (!episode.includes("Sunday, July 5, 2026")) {
  fail(`episode page missing "Sunday, July 5, 2026"`);
}
if (episode.includes("July 4, 2026") || episode.includes("Saturday, July 4")) {
  fail(`episode page still shows July 4 — timezone shift not fixed`);
}
ok('episode page shows "Sunday, July 5, 2026"');

// Podcast index featured + row for American Disclosure (not the legitimate Jul 4 episode)
const featuredCtx = contextAround(podcastIndex, "American Disclosure");
if (!featuredCtx) fail("podcast index missing American Disclosure");
if (!featuredCtx.includes("Sunday, July 5, 2026") && !featuredCtx.includes("Jul 5, 2026")) {
  fail(`podcast index American Disclosure missing July 5 formatted date`);
}
if (featuredCtx.includes("Jul 4, 2026") || featuredCtx.includes("July 4, 2026") || featuredCtx.includes("Saturday, July 4")) {
  fail(`podcast index American Disclosure still shows July 4 — timezone shift not fixed`);
}
ok("podcast index shows July 5 for American Disclosure");

// RSS must keep emitting the correct calendar day (already correct; guard against regressions)
const itemMatch = feed.match(
  /<item>[\s\S]*?<title><!\[CDATA\[American Disclosure\.?\]\]><\/title>[\s\S]*?<pubDate>([^<]+)<\/pubDate>/,
);
const altMatch = feed.match(
  /<title>American Disclosure\.?<\/title>[\s\S]*?<pubDate>([^<]+)<\/pubDate>/,
);
const pubDate = (itemMatch || altMatch)?.[1];
if (!pubDate) fail("could not find American Disclosure pubDate in feed.xml");
// e.g. Sun, 05 Jul 2026 00:00:00 GMT
if (!/05 Jul 2026/.test(pubDate) && !/Jul 05 2026/.test(pubDate)) {
  fail(`RSS pubDate for American Disclosure is not July 5: ${JSON.stringify(pubDate)}`);
}
if (/04 Jul 2026/.test(pubDate) || /Jul 04 2026/.test(pubDate)) {
  fail(`RSS pubDate shifted to July 4: ${JSON.stringify(pubDate)}`);
}
ok(`RSS pubDate still July 5 (${pubDate})`);

console.log("All pubDate timezone regression checks passed.");
