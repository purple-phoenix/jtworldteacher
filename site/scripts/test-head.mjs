#!/usr/bin/env node
// Inspect built files only. js-yaml and parse5 are already in Astro's locked tree.
// Preview: HEAD_BASE=/night/jtworldteacher/ HEAD_ORIGIN=https://preview.example node scripts/test-head.mjs /path/to/build
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, relative, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { load } from 'js-yaml';
import { parse } from 'parse5';
import config from '../astro.config.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dist = resolve(process.argv[2] || join(root, 'dist'));
const read = (path) => readFileSync(join(dist, path), 'utf8');
const production = new URL(config.site).origin;
const expectedBase = process.env.HEAD_BASE || "/";
const expectedOrigin = process.env.HEAD_ORIGIN || production;
function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(join(dir, e.name)) : [join(dir, e.name)]);
}
function elements(node) {
  return [node, ...(node.childNodes || []).flatMap(elements)];
}
function headOf(html) {
  const head = elements(parse(html)).find((n) => n.tagName === 'head');
  assert(head, 'missing head');
  return elements(head).map((n) => ({
    tag: n.tagName,
    attrs: Object.fromEntries((n.attrs || []).map((a) => [a.name, a.value])),
    text: (n.childNodes || []).map((c) => c.value || '').join(''),
  }));
}
function one(nodes, tag, key, value) {
  const matches = nodes.filter((n) => n.tag === tag && n.attrs[key] === value);
  assert.equal(matches.length, 1, `expected one ${tag} ${key}=${value}`);
  return matches[0];
}
const episodes = new Map(walk(join(root, 'src/content/episodes')).filter((f) => f.endsWith('.md')).map((f) => {
  const data = load(readFileSync(f, 'utf8').split(/^---\s*$/m)[1]);
  return [`podcast/${relative(join(root, 'src/content/episodes'), f).replace(/\.md$/, '')}/index.html`, data];
}).filter(([, data]) => !data.draft));
// Read the show's existing values directly, independently of the generated head.
const showSource = readFileSync(join(root, 'src/pages/feed.xml.ts'), 'utf8');
const showTitle = showSource.match(/title: '([^']+)'/)[1];
const showDescription = showSource.match(/description:\s*'([^']+)'/)[1];
const files = walk(dist).filter((f) => f.endsWith('.html'));
assert(files.length > 0, 'build first: no HTML found');
const expectedUrls = [];
const seenEpisodes = new Set();
for (const file of files) {
  const path = relative(dist, file).replaceAll('\\', '/');
  try {
    const nodes = headOf(readFileSync(file, 'utf8'));
    const pagePath = '/' + path.replace(/index\.html$/, '');
    const canonical = new URL(pagePath, production).href;
    expectedUrls.push(canonical);
    assert.equal(one(nodes, 'link', 'rel', 'canonical').attrs.href, canonical);
    assert.equal(one(nodes, 'meta', 'property', 'og:url').attrs.content, canonical);
    const feed = new URL(one(nodes, 'link', 'rel', 'alternate').attrs.href);
    assert.equal(one(nodes, 'link', 'rel', 'alternate').attrs.type, 'application/rss+xml');
    assert.equal(feed.href, new URL(expectedBase + 'feed.xml', expectedOrigin).href);
    const base = feed.pathname.slice(0, -'feed.xml'.length);
    assert(existsSync(join(dist, 'feed.xml')), 'missing feed');
    const ep = episodes.get(path);
    const image = ep?.image || 'podcast-cover.jpg';
    const expectedImage = new URL(/^https?:\/\//.test(image) ? image : base + image.replace(/^\/+/, ''), feed.origin).href;
    for (const [key, value] of [['property', 'og:image'], ['name', 'twitter:image']]) {
      const url = new URL(one(nodes, 'meta', key, value).attrs.content);
      assert(['https:', 'http:'].includes(url.protocol));
      assert.equal(url.href, expectedImage);
      if (url.origin === feed.origin) {
        assert(url.pathname.startsWith(base), 'image must follow preview base');
        assert(existsSync(join(dist, decodeURIComponent(url.pathname.slice(base.length)))), 'missing local share image');
      }
    }
    assert.equal(one(nodes, 'meta', 'name', 'twitter:card').attrs.content, 'summary_large_image');
    if (path === 'podcast/index.html') {
      assert.equal(one(nodes, 'meta', 'name', 'description').attrs.content, showDescription);
    }
    if (ep) {
      seenEpisodes.add(path);
      assert.equal(one(nodes, 'meta', 'property', 'og:type').attrs.content, 'article');
      const data = JSON.parse(one(nodes, 'script', 'type', 'application/ld+json').text);
      assert.equal(data['@context'], 'https://schema.org');
      assert.equal(data['@type'], 'PodcastEpisode');
      assert.equal(data.name, ep.title);
      assert.equal(data.url, canonical);
      assert.equal(data.description, ep.description);
      assert.equal(new Date(data.datePublished).toISOString(), new Date(ep.pubDate).toISOString());
      assert.match(data.duration, /^PT\d+S$/);
      assert.equal(data.duration, `PT${ep.durationSeconds}S`);
      assert.equal(data.associatedMedia['@type'], 'AudioObject');
      assert.equal(data.associatedMedia.contentUrl, ep.audioUrl);
      assert.equal(data.associatedMedia.encodingFormat, ep.audioType || 'audio/mp4');
      assert.equal(data.partOfSeries['@type'], 'PodcastSeries');
      assert.equal(data.partOfSeries.name, showTitle);
      assert.equal(data.partOfSeries.description, showDescription);
      assert.equal(data.partOfSeries.url, production + '/podcast/');
    }
  } catch (error) {
    throw new Error(`${path}: ${error.message}`, { cause: error });
  }
}
assert.equal(seenEpisodes.size, episodes.size, 'every published episode needs a built page');
const sitemap = read('sitemap.xml');
assert(sitemap.includes('xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'));
const urls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1].replaceAll('&amp;', '&'));
assert.equal(new Set(urls).size, urls.length, 'duplicate sitemap URLs');
assert.deepEqual(urls.sort(), expectedUrls.sort(), 'sitemap must list exactly the built HTML pages at production URLs');
assert.match(read('robots.txt'), /^User-agent: \*$/m);
assert.match(read('robots.txt'), /^Allow: \/$/m);
assert(read('robots.txt').includes(`Sitemap: ${production}/sitemap.xml`));
console.log(`ok: metadata, feed discovery, ${episodes.size} episodes, robots and exact ${files.length}-page sitemap (${dist})`);
