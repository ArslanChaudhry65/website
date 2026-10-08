# Verification

Checked on 17 September 2026.

## Completed

- Static build: 13 HTML pages, including the custom 404 page.
- Astro type/content checks: zero errors, warnings or hints.
- Cloudflare Workers deployment dry run: passed; no upload or publication.
- Browser checks: 12 content pages and 61 distinct internal links or anchors.
- Responsive overflow checks at 360, 768 and 1440 CSS pixels.
- Automatic WCAG A/AA checks on all content pages in light mode and the homepage in dark mode.
- No violations reported by axe-core.
- Keyboard skip link focuses the main content.
- Theme toggle updates aria-pressed and persists across reloads.
- System dark preference is respected.
- Case content remains available with JavaScript disabled.
- No third-party requests were made by the pages.
- Email and LinkedIn links match the supplied contact details.
- Desktop light, desktop dark, mobile and case screenshots inspected.
- Supplied design linter: zero errors across all 13 HTML pages.
- Public build guard rejects the incomplete editorial and publisher state.

## Design linter interpretation

The supplied checker has one warning per page: lang is only on the html element. Its recommendation to repeat lang on a wrapper is specific to embedded Claude Artifacts, where the outer HTML is generated elsewhere. This is a standalone website. lang="en" on html is correct and is verified in the browser, so the warning is intentionally retained.

CSS minification is disabled to preserve the exact source spelling of the tokens for this checker. Compression at the host can still compress the CSS transfer. The unchanged token file is the source of truth.

The checker operates on generated HTML with linked local CSS and font bytes inlined into temporary inspection files. It does not change the delivered website.

## Limits

Automatic accessibility checks are not a complete WCAG audit. No full assistive-technology session or production field performance data is claimed. No public deployment, DNS change or content approval has occurred.

Detailed machine reports and screenshots are in .qa/ and are excluded from version control.
