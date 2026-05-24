import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { marked } from 'marked';

const SHOW = {
  title: 'JT — Astrology & Simulation Theory',
  description:
    'A long-form inquiry into what the chart says about the nature of the reality we appear to be inside of. Slow, unhurried, and meant for people already asking the question.',
  author: 'JT McCarthy',
  ownerEmail: 'josephtimothymccarthy@gmail.com',
  copyright: '© JT McCarthy',
  language: 'en-us',
  category: { text: 'Religion & Spirituality', sub: 'Spirituality' },
  image: 'podcast-cover.jpg',
  explicit: false,
  type: 'episodic' as const,
};

const xmlEscape = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export async function GET(context: APIContext) {
  if (!context.site) throw new Error('astro.config.mjs must set `site` for the RSS feed to build.');
  const siteRoot = String(context.site).replace(/\/+$/, '');
  const base = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '');
  const root = `${siteRoot}${base}/`;
  const absolute = (path: string) => root + path.replace(/^\/+/, '');

  const episodes = (await getCollection('episodes', ({ data }) => !data.draft)).sort(
    (a, b) => b.data.pubDate.getTime() - a.data.pubDate.getTime(),
  );

  const coverUrl = absolute(SHOW.image);

  const feedUrl = absolute('feed.xml');
  const podcastGuid = '798ea7a3-ff1d-5480-96d7-b963b6198ade';

  return rss({
    xmlns: {
      itunes: 'http://www.itunes.com/dtds/podcast-1.0.dtd',
      content: 'http://purl.org/rss/1.0/modules/content/',
      atom: 'http://www.w3.org/2005/Atom',
      podcast: 'https://podcastindex.org/namespace/1.0',
    },
    title: SHOW.title,
    description: SHOW.description,
    site: root,
    customData: `
      <atom:link href="${xmlEscape(feedUrl)}" rel="self" type="application/rss+xml" />
      <language>${SHOW.language}</language>
      <copyright>${xmlEscape(SHOW.copyright)}</copyright>
      <itunes:author>${xmlEscape(SHOW.author)}</itunes:author>
      <itunes:owner>
        <itunes:name>${xmlEscape(SHOW.author)}</itunes:name>
        <itunes:email>${xmlEscape(SHOW.ownerEmail)}</itunes:email>
      </itunes:owner>
      <itunes:image href="${xmlEscape(coverUrl)}" />
      <itunes:category text="${xmlEscape(SHOW.category.text)}">
        <itunes:category text="${xmlEscape(SHOW.category.sub)}" />
      </itunes:category>
      <itunes:explicit>${SHOW.explicit}</itunes:explicit>
      <itunes:type>${SHOW.type}</itunes:type>
      <podcast:guid>${podcastGuid}</podcast:guid>
      <podcast:locked owner="${xmlEscape(SHOW.ownerEmail)}">no</podcast:locked>
    `.trim(),
    items: episodes.map((ep) => {
      const slug = ep.id.replace(/\.md$/, '');
      const episodeUrl = absolute(`podcast/${slug}/`);
      const episodeImage = ep.data.image ? absolute(ep.data.image) : coverUrl;
      const bodyHtml = ep.body ? (marked.parse(ep.body, { async: false }) as string) : '';
      return {
        title: ep.data.title,
        pubDate: ep.data.pubDate,
        description: ep.data.description,
        content: bodyHtml || undefined,
        link: episodeUrl,
        enclosure: {
          url: ep.data.audioUrl,
          length: ep.data.audioLength,
          type: ep.data.audioType,
        },
        customData: `
          <itunes:title>${xmlEscape(ep.data.title)}</itunes:title>
          <itunes:duration>${ep.data.duration}</itunes:duration>
          <itunes:episodeType>${ep.data.episodeType}</itunes:episodeType>
          <itunes:explicit>${ep.data.explicit}</itunes:explicit>
          ${ep.data.season ? `<itunes:season>${ep.data.season}</itunes:season>` : ''}
          ${ep.data.episode ? `<itunes:episode>${ep.data.episode}</itunes:episode>` : ''}
          <itunes:image href="${xmlEscape(episodeImage)}" />
        `.trim(),
      };
    }),
  });
}
