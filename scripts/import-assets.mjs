import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs';
import path from 'node:path';
const identity = process.argv[2];
const cv = process.argv[3];
if (!identity || !cv) throw new Error('Pass the supplied design identity directory and existing CV path.');
mkdirSync('public/fonts',{recursive:true});
mkdirSync('public/cv',{recursive:true});
const css = readFileSync(path.join(identity,'bei-bedarf/plex-embedded.css'),'utf8');
const blocks = [...css.matchAll(/@font-face\s*\{([^}]+)\}/g)].map(x=>x[1]);
for(const [family,style,weight,name] of [['IBM Plex Sans','normal','100 700','plex-sans'],['IBM Plex Sans','italic','100 700','plex-sans-italic'],['IBM Plex Mono','normal','400','plex-mono']]){
 const block=blocks.find(x=>x.includes(family) && new RegExp('font-style:\\s*'+style).test(x) && new RegExp('font-weight:\\s*'+weight+';').test(x));
 if(!block) throw new Error('Font not found: '+name);
 const encoded=block.match(/base64,([A-Za-z0-9+/=]+)/)?.[1];
 if(!encoded) throw new Error('Missing font bytes: '+name);
 writeFileSync('public/fonts/'+name+'.woff2',Buffer.from(encoded,'base64'));
}
copyFileSync(path.join(identity,'hochladen/tokens.css'),'src/styles/tokens.css');
copyFileSync(path.join(identity,'hochladen/lint.py'),'scripts/design-lint.py');
copyFileSync(cv,'public/cv/arslan-chaudhry.pdf');
console.log('Copied source tokens, design linter and existing CV. Extracted three local font faces.');
