import { mkdirSync, readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const {chromium}=process.env.PLAYWRIGHT_MODULE?await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE).href):await import('playwright');
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1200,height:630},deviceScaleFactor:1,colorScheme:'light'});
mkdirSync('public/og',{recursive:true});
const tokens=readFileSync('src/styles/tokens.css','utf8');
const font=readFileSync('public/fonts/plex-sans.woff2').toString('base64');
const mono=readFileSync('public/fonts/plex-mono.woff2').toString('base64');
const entries=[
 ['site','Product decisions under real constraints.','Enterprise software / Platforms / AI'],
 ['enrolment','Mass enrolment that survives a launch day.','Case study / Enterprise scale'],
 ['migration','Modernising an editor without a cutover day.','Case study / Platform modernisation'],
 ['reversible-migrations','Reversibility is a product capability.','Writing / Enterprise modernisation']
];
for(const [id,title,label] of entries){
 await page.setContent('<!doctype html><html lang="en"><head><meta charset="utf-8"><style>'+tokens+'@font-face{font-family:"IBM Plex Sans";src:url(data:font/woff2;base64,'+font+') format("woff2");font-weight:100 700}@font-face{font-family:"IBM Plex Mono";src:url(data:font/woff2;base64,'+mono+') format("woff2");font-weight:400}body{margin:0;background:var(--ac-paper-1);color:var(--ac-ink-0);font-family:var(--ac-font-sans)}.frame{box-sizing:border-box;width:1200px;height:630px;padding:var(--ac-space-18);display:flex;flex-direction:column}.name{font-size:var(--ac-text-heading-lg);font-weight:var(--ac-weight-semibold)}.name span{color:var(--ac-accent)}.label{margin-top:auto;margin-bottom:var(--ac-space-6);font-family:var(--ac-font-mono);font-size:var(--ac-text-caption);text-transform:uppercase;letter-spacing:var(--ac-tracking-label);color:var(--ac-ink-2)}h1{font-size:var(--ac-text-display-lg);line-height:var(--ac-leading-display);font-weight:var(--ac-weight-medium);letter-spacing:var(--ac-tracking-display);max-width:26ch;margin:0}.foot{margin-top:auto;padding-top:var(--ac-space-6);border-top:var(--ac-hairline) solid var(--ac-line-strong);font-size:var(--ac-text-body-lg);color:var(--ac-ink-2)}</style></head><body><div class="frame"><div class="name">Arslan Chaudhry<span>.</span></div><div class="label">'+label+'</div><h1>'+title+'</h1><div class="foot">arslanchaudhry.com</div></div></body></html>');
 await page.evaluate(()=>document.fonts.ready);
 await page.screenshot({path:'public/og/'+id+'.png'});
}
await browser.close();
console.log('Generated four static Open Graph images.');
