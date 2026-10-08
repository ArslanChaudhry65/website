import { defineConfig } from 'astro/config';
export default defineConfig({
  site: 'https://arslanchaudhry.com',
  output: 'static',
  trailingSlash: 'always',
  build: { inlineStylesheets: 'never' },
  vite: { build: { cssMinify: false }, css: { transformer: 'postcss' } },
});
