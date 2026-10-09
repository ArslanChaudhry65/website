import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

const work = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/work' }),
  schema: z.object({
    title: z.string(), description: z.string(), number: z.string(),
    category: z.string(), kind: z.enum(['Case study', 'Decision note']),
    role: z.string(), period: z.string(), status: z.string(),
    decision: z.string(), result: z.string(), order: z.number(),
    diagram: z.enum(['enrolment', 'migration']),
    reviewRequired: z.boolean().default(true),
  }),
});
const writing = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/writing' }),
  schema: z.object({
    title: z.string(), description: z.string(), topic: z.string(),
    relatedWork: z.string(), order: z.number(),
    reviewRequired: z.boolean().default(true),
    publishedAt: z.coerce.date().optional(),
  }),
});
export const collections = { work, writing };
