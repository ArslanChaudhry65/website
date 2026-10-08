# Arslan Chaudhry: personal website

An English, static Astro website based on the approved review direction and Design Identity v1.2.4.

## Run

Node 22.12 or newer.

```sh
npm ci
npm run dev
npm run check
npm run build
npm run preview
```

The default build is a local editorial preview: noindex, blocked in robots.txt, and an empty sitemap and RSS feed. Nothing has been deployed.

## Content

- Homepage: src/pages/index.astro
- Cases and decision note: src/content/work/
- Article drafts: src/content/writing/
- Contact and publication settings: src/data/site.ts
- Design tokens: src/styles/tokens.css, copied unchanged from the supplied identity
- Site styling: src/styles/global.css

Update Markdown and frontmatter to change a case. The collection schema validates required fields at build time. Reuse headings from an existing case. Individual ownership is expressed conservatively. Missing measurements are not replaced with targets.

The two essays are proposed first-person copy derived from the cases. They require Arslan's editorial approval. Add their actual publishedAt date when publishing to include them in RSS. Reusable content templates are in templates/.

## Before public deployment

Review LAUNCH.md, complete publisher details and privacy copy, review each content file, then set publicationApproved in src/data/site.ts. Use npm run build:release for indexable output and npm run deploy for Cloudflare Workers Static Assets. Deploy requires a configured Cloudflare account and explicit publication approval. This project creates no remote repository and changes no DNS.

## Design

IBM Plex Sans for the website, Mono for metadata. Warm surfaces, petrol accent, no shadows, 4 px radius, source tokens. Local font assets were extracted from the supplied embedded font CSS to avoid third-party requests. Theme preference is the only browser storage. No analytics or client framework.

## Editorial basis

The private prototype and the September 2026 case notes were used as source material. Customer names, exact customer volumes and internal ticket identifiers are omitted. No throughput, revenue or adoption result has been invented.

## Verification

Run npm run check and npm run build. The optional scripts/verify.mjs checks all generated routes, links, metadata, mobile overflow and theme behaviour with Playwright and axe-core. Pass PLAYWRIGHT_MODULE as the absolute path to an installed Playwright index.mjs, or install Playwright in the development environment. It is not a production dependency. scripts/lint-design.mjs runs the supplied design linter against HTML with its linked styles inlined for inspection. QA.md records results and the artifact-specific warning accepted for standalone HTML.
