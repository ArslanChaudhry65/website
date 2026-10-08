import { getCollection } from 'astro:content';
import { isPublic, site } from '../data/site';
export async function GET() {
 const routes = ['/', '/work/', '/writing/', '/about/', '/contact/', ...(await getCollection('work')).map(x=>'/work/'+x.id+'/'), ...(await getCollection('writing')).map(x=>'/writing/'+x.id+'/')];
 const urls = isPublic ? routes.map(path=>'<url><loc>'+site.url+path+'</loc></url>').join('') : '';
 return new Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls+'</urlset>', {headers:{'Content-Type':'application/xml'}});
}
