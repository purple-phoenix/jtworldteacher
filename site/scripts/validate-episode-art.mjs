import { createHash } from "node:crypto";
import { readFile, stat } from "node:fs/promises";
import { resolve } from "node:path";
import process from "node:process";
import sharp from "sharp";

const siteRoot = resolve(import.meta.dirname, "..");
const manifestPath = resolve(siteRoot, "src/data/peak-mind-episode-art.json");
const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const spotifyFlag = process.argv.indexOf("--spotify-dir");
const spotifyDir = spotifyFlag === -1 ? null : resolve(process.argv[spotifyFlag + 1] || "");
const deferredSlug = "2026-10-07-proof-of-work-and-the-simulations-challenge-rating";
const authorizedSlugs = new Set([
  "2026-07-04-the-revelation-of-the-hierarchy",
  "2026-07-05-american-disclosure",
  "2026-09-02-technical-remote-viewing-and-the-kill-shot",
  "2026-09-09-intuitive-underground-and-the-power-of-remote-viewing",
  "2026-09-16-the-world-tree-and-the-eclipse-in-leo",
  deferredSlug,
]);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function parseScalar(raw) {
  const value = raw.trim();
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }
  if (value === "true") return true;
  if (value === "false") return false;
  if (/^-?\d+$/.test(value)) return Number(value);
  return value;
}

async function readFrontmatter(relativePath) {
  const text = await readFile(resolve(siteRoot, relativePath), "utf8");
  const lines = text.split(/\r?\n/);
  assert(lines[0] === "---", `${relativePath}: missing opening frontmatter delimiter`);
  const end = lines.indexOf("---", 1);
  assert(end > 0, `${relativePath}: missing closing frontmatter delimiter`);
  return Object.fromEntries(
    lines
      .slice(1, end)
      .filter((line) => line.trim() && !line.trimStart().startsWith("#"))
      .map((line) => {
        const separator = line.indexOf(":");
        assert(separator > 0, `${relativePath}: unsupported frontmatter line: ${line}`);
        return [line.slice(0, separator).trim(), parseScalar(line.slice(separator + 1))];
      }),
  );
}

async function validateImage(path, expectedSize, label) {
  const metadata = await sharp(path).metadata();
  await sharp(path).resize(1, 1).raw().toBuffer();
  assert(metadata.format === "jpeg", `${label}: expected JPEG, received ${metadata.format}`);
  assert(metadata.width === expectedSize && metadata.height === expectedSize, `${label}: expected ${expectedSize}×${expectedSize}, received ${metadata.width}×${metadata.height}`);
  assert(metadata.channels === 3, `${label}: expected three RGB channels, received ${metadata.channels}`);
  assert(metadata.space === "srgb", `${label}: expected sRGB, received ${metadata.space}`);
}

assert(manifest.version === 1, "Unsupported Peak Mind art manifest version");
assert(manifest.episodes.length === authorizedSlugs.size, `Expected ${authorizedSlugs.size} Peak Mind art records, received ${manifest.episodes.length}`);

const seenSlugs = new Set();

for (const episode of manifest.episodes) {
  assert(authorizedSlugs.has(episode.slug), `Unauthorized Peak Mind episode slug: ${episode.slug}`);
  assert(!seenSlugs.has(episode.slug), `Duplicate Peak Mind episode slug: ${episode.slug}`);
  seenSlugs.add(episode.slug);

  const expectedFilename = `${episode.slug}.jpg`;
  const expectedSitePath = `episodes/${expectedFilename}`;
  const expectedSiteEpisodePath = episode.slug === deferredSlug ? null : `src/content/episodes/${episode.slug}.md`;
  const expectedSiteStatus = episode.slug === deferredSlug ? "deferred-no-authoritative-episode" : "wired";
  assert(episode.filename === expectedFilename, `${episode.slug}: expected output filename ${expectedFilename}, received ${episode.filename}`);
  assert(episode.sitePath === expectedSitePath, `${episode.slug}: expected site image path ${expectedSitePath}, received ${episode.sitePath}`);
  assert(episode.siteEpisodePath === expectedSiteEpisodePath, `${episode.slug}: expected episode path ${expectedSiteEpisodePath}, received ${episode.siteEpisodePath}`);
  assert(episode.siteStatus === expectedSiteStatus, `${episode.slug}: expected site status ${expectedSiteStatus}, received ${episode.siteStatus}`);

  const webPath = resolve(siteRoot, "public", episode.sitePath);
  await validateImage(webPath, manifest.webDimensions[0], `${episode.slug} web cover`);

  if (episode.siteStatus === "wired") {
    assert(episode.enclosure, `${episode.slug}: wired entry has no enclosure contract`);
    const frontmatter = await readFrontmatter(episode.siteEpisodePath);
    assert(frontmatter.title === episode.title, `${episode.slug}: title does not match manifest`);
    assert(frontmatter.image === episode.sitePath, `${episode.slug}: image does not match manifest`);
    for (const [key, expected] of Object.entries(episode.enclosure)) {
      assert(frontmatter[key] === expected, `${episode.slug}: enclosure field ${key} changed (expected ${expected}, received ${frontmatter[key]})`);
    }
  } else if (episode.siteStatus === "deferred-no-authoritative-episode") {
    assert(episode.enclosure === null, `${episode.slug}: deferred entry must not invent enclosure metadata`);
    assert(episode.deferredReason, `${episode.slug}: deferred entry must explain why mapping is postponed`);
  }

  if (spotifyDir) {
    const spotifyPath = resolve(spotifyDir, episode.filename);
    await validateImage(spotifyPath, manifest.spotifyDimensions[0], `${episode.slug} Spotify cover`);
    const file = await readFile(spotifyPath);
    episode.actualSpotifyBytes = (await stat(spotifyPath)).size;
    episode.actualSpotifySha256 = createHash("sha256").update(file).digest("hex");
  }
}

await validateImage(resolve(siteRoot, "public/podcast-cover.jpg"), 3000, "authoritative podcast cover");

if (spotifyDir) {
  const externalManifest = JSON.parse(await readFile(resolve(spotifyDir, "manifest.json"), "utf8"));
  assert(externalManifest.episodes.length === 6, "Spotify manifest must contain six records");
  for (const episode of manifest.episodes) {
    const external = externalManifest.episodes.find((item) => item.slug === episode.slug);
    assert(external, `${episode.slug}: missing from Spotify manifest`);
    assert(external.title === episode.title, `${episode.slug}: Spotify manifest title mismatch`);
    assert(external.outputFilename === episode.filename, `${episode.slug}: Spotify manifest filename mismatch`);
    assert(external.sitePath === episode.sitePath, `${episode.slug}: Spotify manifest site path mismatch`);
    assert(external.dimensions === "3000x3000", `${episode.slug}: Spotify manifest dimension mismatch`);
    assert(external.byteSize === episode.actualSpotifyBytes, `${episode.slug}: Spotify manifest byte size mismatch`);
    assert(external.sha256 === episode.actualSpotifySha256, `${episode.slug}: Spotify manifest SHA-256 mismatch`);
  }
}

console.log(`Validated ${manifest.episodes.length} Peak Mind covers (${authorizedSlugs.size - 1} wired, 1 deliberately deferred)${spotifyDir ? " plus Spotify exports and manifest" : ""}.`);
