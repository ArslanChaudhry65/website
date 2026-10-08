import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
const walk = d => readdirSync(d,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(d,e.name)): [path.join(d,e.name)]);
mkdirSync('.qa/design',{recursive:true});
const paths=[];
for(const file of walk('dist').filter(f=>f.endsWith('.html'))){
 let html=readFileSync(file,'utf8');
 html=html.replace(/<link\b[^>]*rel="stylesheet"[^>]*>/g,tag=>{
  const url=tag.match(/href="([^"]+)"/)?.[1];
  return url && url.startsWith('/') ? '<style>'+readFileSync(path.join('dist',url),'utf8')+'</style>' : tag;
 });
 // The artifact-oriented checker cannot follow local font URLs.
 // Inlining the same bytes makes glyph checks equivalent to the served site.
 html=html.replace(/url\(["']?\/?fonts\/([^"')]+)["']?\)/g,(_m,file)=>'url(data:font/woff2;base64,'+readFileSync('public/fonts/'+file).toString('base64')+')');
 const target=path.join('.qa/design',file.replaceAll(/[\\/]/g,'_'));
 writeFileSync(target,html);
 paths.push(target);
}
const result=spawnSync(process.env.PYTHON_EXECUTABLE || 'python',['scripts/design-lint.py',...paths,'--tokens','src/styles/tokens.css','--json'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'},maxBuffer:20*1024*1024});
if(result.error) throw result.error;
if(result.stderr) console.error(result.stderr);
writeFileSync('.qa/design-lint.json',result.stdout);
const parsed=JSON.parse(result.stdout);
for(const report of Array.isArray(parsed)?parsed:[parsed]){
 console.log(report.file,JSON.stringify(report.summary));
 for(const f of report.findings.filter(x=>x.severity==='fehler')) console.log(JSON.stringify(f));
}
process.exit(result.status ?? 1);
