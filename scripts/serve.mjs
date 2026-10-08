import { createServer } from 'node:http';
import { readFileSync, statSync, existsSync } from 'node:fs';
import path from 'node:path';
const root=path.resolve('dist');
const index=process.argv.indexOf('--port');
const port=index>=0?Number(process.argv[index+1]):4321;
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2','.pdf':'application/pdf','.xml':'application/xml','.txt':'text/plain; charset=utf-8'};
createServer((req,res)=>{
 try {
  const url=new URL(req.url,'http://127.0.0.1');
  let file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
  if(file!==root && !file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  if(existsSync(file)&&statSync(file).isDirectory()){
   if(!url.pathname.endsWith('/')){res.writeHead(301,{Location:url.pathname+'/'+url.search});res.end();return;}
   file=path.join(file,'index.html');
  }
  let status=200;
  if(!existsSync(file)||!statSync(file).isFile()){file=path.join(root,'404.html');status=404;}
  const body=readFileSync(file);
  res.writeHead(status,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store','X-Robots-Tag':'noindex, nofollow'});
  res.end(req.method==='HEAD'?undefined:body);
 } catch {res.writeHead(400);res.end('Bad request');}
}).listen(port,'127.0.0.1',()=>console.log('Local preview: http://127.0.0.1:'+port));
