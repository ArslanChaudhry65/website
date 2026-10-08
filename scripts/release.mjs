import { readFileSync, readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
const source = readFileSync('src/data/site.ts','utf8');
const reasons = [];
if (!/publicationApproved:\s*true/.test(source)) reasons.push('Approve the copy in src/data/site.ts.');
if (/address:\s*['"]['"]/.test(source)) reasons.push('Complete publisher details.');
for (const folder of ['src/content/work','src/content/writing']) {
 for (const name of readdirSync(folder)) {
  if (name.endsWith('.md') && /reviewRequired:\s*true/.test(readFileSync(folder+'/'+name,'utf8'))) reasons.push('Review '+folder+'/'+name);
 }
}
if (reasons.length) { console.error('Public build needs:\n'+reasons.map(x=>' - '+x).join('\n')); process.exit(1); }
const result=spawnSync(process.execPath,['node_modules/astro/bin/astro.mjs','build'],{stdio:'inherit',env:{...process.env,ASTRO_TELEMETRY_DISABLED:'1',PUBLICATION_MODE:'public'}});
process.exit(result.status ?? 1);
