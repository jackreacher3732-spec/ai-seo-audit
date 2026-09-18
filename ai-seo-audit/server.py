from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser
import json, re, ssl

class SEOParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.title=''; self.desc=''; self.h1=0; self.h2=0; self.images=0; self.images_alt=0; self.links=[]; self.canonical=''; self.robots=''; self.in_title=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='title': self.in_title=True
        if tag=='meta':
            n=(a.get('name') or '').lower(); p=(a.get('property') or '').lower()
            if n=='description': self.desc=a.get('content','')
            if n=='robots': self.robots=a.get('content','')
        if tag=='link' and (a.get('rel') or '').lower()=='canonical': self.canonical=a.get('href','')
        if tag=='h1': self.h1+=1
        if tag=='h2': self.h2+=1
        if tag=='img':
            self.images+=1
            if a.get('alt','').strip(): self.images_alt+=1
        if tag=='a' and a.get('href'): self.links.append(a['href'])
    def handle_endtag(self, tag):
        if tag=='title': self.in_title=False
    def handle_data(self, data):
        if self.in_title: self.title += data.strip()

def audit(url):
    if not re.match(r'^https?://', url): url='https://'+url
    req=Request(url,headers={'User-Agent':'AI-SEO-AuditBot/1.0'})
    with urlopen(req,timeout=15,context=ssl.create_default_context()) as r:
        final=r.geturl(); html=r.read(1000000).decode('utf-8','ignore'); status=r.status
    p=SEOParser(); p.feed(html)
    host=urlparse(final).netloc
    checks=[]
    def add(name, ok, detail, priority='medium'):
        checks.append({'name':name,'status':'pass' if ok else 'fail','detail':detail,'priority':priority})
    add('HTTPS', final.startswith('https://'), 'Secure HTTPS connection detected.' if final.startswith('https://') else 'Site is not using HTTPS.','high')
    add('Title tag', 10<=len(p.title)<=60, f'Title length: {len(p.title)} characters.', 'high')
    add('Meta description', 70<=len(p.desc)<=160, f'Description length: {len(p.desc)} characters.', 'high')
    add('H1 structure', p.h1==1, f'Found {p.h1} H1 tag(s).', 'high')
    add('H2 structure', p.h2>=1, f'Found {p.h2} H2 tag(s).', 'medium')
    add('Image alt text', p.images==0 or p.images_alt==p.images, f'{p.images_alt}/{p.images} images have alt text.', 'medium')
    add('Canonical', bool(p.canonical), 'Canonical URL is present.' if p.canonical else 'No canonical link detected.','medium')
    robots=urljoin(final,'/robots.txt'); sitemap=urljoin(final,'/sitemap.xml')
    for label,u in [('robots.txt',robots),('XML sitemap',sitemap)]:
        try:
            q=Request(u,headers={'User-Agent':'AI-SEO-AuditBot/1.0'})
            with urlopen(q,timeout=6) as rr: ok=rr.status<400
        except Exception: ok=False
        add(label,ok, f'{label} is accessible.' if ok else f'{label} was not detected at the standard URL.','medium')
    internal=sum(1 for x in p.links if x.startswith('/') or urlparse(x).netloc==host or not urlparse(x).netloc)
    add('Internal links', internal>=3, f'Found approximately {internal} internal link(s).','low')
    passed=sum(x['status']=='pass' for x in checks); score=round(100*passed/len(checks))
    return {'url':final,'status_code':status,'score':score,'checks':checks,'summary':{'passed':passed,'issues':len(checks)-passed,'total':len(checks)}}

class Handler(BaseHTTPRequestHandler):
    def send_json(self,obj,code=200):
        b=json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        if self.path!='/api/audit': return self.send_json({'error':'Not found'},404)
        try:
            n=int(self.headers.get('Content-Length',0)); data=json.loads(self.rfile.read(n)); result=audit(data.get('url','').strip())
            self.send_json(result)
        except Exception as e: self.send_json({'error':str(e)},400)
    def log_message(self,*args): pass

print('AI SEO Audit API running on http://localhost:8000')
HTTPServer(('0.0.0.0',8000),Handler).serve_forever()
