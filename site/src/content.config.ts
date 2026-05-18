import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const episodes = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/episodes' }),
  schema: z.object({
    title: z.string(),
    pubDate: z.coerce.date(),
    description: z.string(),
    summary: z.string().optional(),
    audioUrl: z.string().url(),
    audioLength: z.number().int().positive(),
    audioType: z.string().default('audio/mp4'),
    duration: z.string(),
    durationSeconds: z.number().int().positive(),
    season: z.number().int().positive().optional(),
    episode: z.number().int().positive().optional(),
    episodeType: z.enum(['full', 'trailer', 'bonus']).default('full'),
    explicit: z.boolean().default(false),
    draft: z.boolean().default(false),
    spaceUrl: z.string().url().optional(),
    spaceId: z.string().optional(),
    image: z.string().optional(),
  }),
});

export const collections = { episodes };
