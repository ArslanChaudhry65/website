import { getCollection } from 'astro:content';
import { isPublic, site } from '../data/site';
const escape = (value: string) => value.replace(/[<>&"']/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]!));
export async function GET() {
 const articles = isPublic ? (await getCollection('writing')).filter(a=>!a.data.reviewRequired && a.data.publishedAt).sort((a,b)=>b.data.publishedAt!.getTime()-a.data.publishedAt!.getTime()) : [];
 const items=articles.map(a=>{
  const url=site.url+'/writing/'+a.id+'/';
  return '<item><title>'+escape(a.data.title)+'</title><link>'+url+'</link><guid>'+url+'</guid><description>'+escape(a.data.description)+'</description><pubDate>'+a.data.publishedAt!.toUTCString()+'</pubDate></item>';
 }).join('');
 return new Response('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Arslan Chaudhry / Writing</title><link>'+site.url+'/writing/</link><description>'+escape(site.description)+'</description><language>en</language>'+items+'</channel></rss>',{headers:{'Content-Type':'application/rss+xml; charset=utf-8'}});
}
