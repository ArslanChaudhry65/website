import { isPublic, site } from '../data/site';
export function GET() {
 return new Response(isPublic ? 'User-agent: *\nAllow: /\nSitemap: '+site.url+'/sitemap.xml\n' : 'User-agent: *\nDisallow: /\n', {headers:{'Content-Type':'text/plain; charset=utf-8'}});
}
