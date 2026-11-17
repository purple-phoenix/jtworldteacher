import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import { TOPICS } from '../data/topics';
import config from '../../astro.config.mjs';

const escapeXml = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export async function GET(_context: APIContext) {
  // Discover static HTML routes; XML endpoints and dynamic templates are excluded.
  const staticPaths = Object.keys(import.meta.glob('./**/*.astro'))
    .filter((path) => !path.includes('['))
    .map((path) => '/' + path.slice(2).replace(/(?:^|\/)index\.astro$/, '/').replace(/\.astro$/, '/').replace(/^\//, ''));
  const episodes = await getCollection('episodes', ({ data }) => !data.draft);
  const paths = [
    ...staticPaths,
    ...episodes.map((ep) => `/podcast/${ep.id.replace(/\.md$/, '')}/`),
    ...TOPICS.map((topic) => `/topics/${topic.id}/`),
  ];
  // Always production addresses, even in a build with a private preview base.
  const urls = [...new Set(paths.map((path) => new URL(path, config.site).href))].sort();
  return new Response(`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.map((url) => `<url><loc>${escapeXml(url)}</loc></url>`).join('')}</urlset>`, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
}
