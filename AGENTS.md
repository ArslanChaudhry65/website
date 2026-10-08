# Working on this website

This is a static Astro site. Read README.md and LAUNCH.md before substantive changes.

- Keep case content in src/content/work and essays in src/content/writing.
- Use the existing schemas and layouts. Keep dependencies small.
- src/styles/tokens.css is copied from Arslan's supplied identity. Do not introduce a second palette or spacing scale.
- Use Sans for website text, Mono only for labels. Keep headings at weight 500, wordmark at 600. Preserve dark mode, print support and keyboard focus.
- State personal responsibility precisely. Do not invent metrics, customer names, ownership or completed outcomes. Preserve evidence limitations.
- Editorial drafts use reviewRequired: true. The default build is a noindex preview.
- Publication approval, hosting details and domain changes are handled at launch. Do not silently switch to public mode.
- Use npm run check and npm run build after implementation changes. Use the supplied design linter and browser checks for visual or interaction changes.
- A failed visual check should be corrected in the source rather than by weakening the checker.
- Font assets are local and include the IBM Plex license.
