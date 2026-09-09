from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urlparse
import json, re, sys, xml.etree.ElementTree as ET
from config import SITE_URL

ROOT=Path(__file__).resolve().parents[1]; DIST=ROOT/'dist'
errors=[]; warnings=[]; rows=[]
index_files=list(DIST.rglob('index.html'))
canonicals=[]; titles=[]; descs=[]
article_schema=0; recipe_schema=0; breadcrumb_schema=0; profile_schema=0
for f in index_files:
    s=BeautifulSoup(f.read_text(encoding='utf-8'),'html.parser')
    title=s.title.get_text(' ',strip=True) if s.title else ''
    desc=(s.find('meta',attrs={'name':'description'}) or {}).get('content','') if s.find('meta',attrs={'name':'description'}) else ''
    can=(s.find('link',rel='canonical') or {}).get('href','') if s.find('link',rel='canonical') else ''
    titles.append(title); descs.append(desc); canonicals.append(can)
    if not can.startswith(SITE_URL+'/'): errors.append(f'{f}: canonical not on SITE_URL: {can}')
    if len(title)>65: warnings.append(f'{f}: title {len(title)} chars')
    if len(desc)<105: warnings.append(f'{f}: description short ({len(desc)})')
    if len(desc)>165: errors.append(f'{f}: description too long ({len(desc)})')
    robots=s.find('meta',attrs={'name':'robots'})
    if not robots or 'index' not in robots.get('content',''): errors.append(f'{f}: missing index robots directive')
    for meta in [
        ('property','og:title'),('property','og:description'),('property','og:url'),('property','og:image'),('property','og:image:alt'),
        ('name','twitter:card'),('name','twitter:title'),('name','twitter:description'),('name','twitter:image'),('name','twitter:image:alt')]:
        if not s.find('meta',attrs={meta[0]:meta[1]}): errors.append(f'{f}: missing {meta[1]}')
    # heading id uniqueness
    ids=[h.get('id') for h in s.find_all(['h2','h3']) if h.get('id')]
    dups=[x for x,n in Counter(ids).items() if n>1]
    if dups: errors.append(f'{f}: duplicate heading ids {dups}')
    scripts=s.find_all('script',attrs={'type':'application/ld+json'})
    if len(scripts)!=1: errors.append(f'{f}: expected one JSON-LD block, got {len(scripts)}')
    for sc in scripts:
        try: data=json.loads(sc.string or sc.get_text())
        except Exception as e:
            errors.append(f'{f}: invalid JSON-LD {e}'); continue
        graph=data.get('@graph',[]) if isinstance(data,dict) else []
        idschema=[x.get('@id') for x in graph if isinstance(x,dict) and x.get('@id')]
        dupids=[x for x,n in Counter(idschema).items() if n>1]
        if dupids: warnings.append(f'{f}: duplicate schema @id {dupids}')
        types=[]
        for node in graph:
            if not isinstance(node,dict): continue
            t=node.get('@type'); types += t if isinstance(t,list) else [t]
        article_schema += types.count('Article')
        recipe_schema += types.count('Recipe')
        breadcrumb_schema += types.count('BreadcrumbList')
        profile_schema += types.count('ProfilePage')
        if can!=SITE_URL+'/' and 'BreadcrumbList' not in types: errors.append(f'{f}: missing BreadcrumbList schema')
        if '/authors/farrukh-abdullah/' not in can and can!=SITE_URL+'/' and '/about/' not in can and '/editorial-policy/' not in can and '/corrections-policy/' not in can and '/sources-research-methodology/' not in can and '/contact/' not in can and '/affiliate-disclosure/' not in can:
            if '/extras/cullen-skink-recipe/' in can:
                if 'Recipe' not in types: errors.append(f'{f}: recipe page missing Recipe schema')
                if 'Article' in types: warnings.append(f'{f}: recipe page also has Article schema')
            elif 'Article' not in types: errors.append(f'{f}: article page missing Article schema')
    rows.append((f,can,title,desc))

for value,n in Counter(titles).items():
    if n>1: errors.append(f'duplicate title: {value!r} x{n}')
for value,n in Counter(descs).items():
    if n>1: errors.append(f'duplicate description: {value!r} x{n}')
for value,n in Counter(canonicals).items():
    if n>1: errors.append(f'duplicate canonical: {value!r} x{n}')

# Sitemap
sm=DIST/'sitemap.xml'
try:
    root=ET.parse(sm).getroot(); ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    locs=[e.text for e in root.findall('s:url/s:loc',ns)]
    if len(locs)!=61: errors.append(f'sitemap expected 61 URLs, found {len(locs)}')
    if len(locs)!=len(set(locs)): errors.append('sitemap contains duplicate URLs')
    if set(locs)!=set(canonicals): errors.append('sitemap URLs do not exactly match indexable canonicals')
except Exception as e: errors.append(f'invalid sitemap: {e}')
robots=(DIST/'robots.txt').read_text(encoding='utf-8')
if f'Sitemap: {SITE_URL}/sitemap.xml' not in robots: errors.append('robots.txt sitemap mismatch')
# 404
s404=BeautifulSoup((DIST/'404.html').read_text(encoding='utf-8'),'html.parser')
r404=s404.find('meta',attrs={'name':'robots'})
if not r404 or 'noindex' not in r404.get('content',''): errors.append('404 missing noindex')
if not (DIST/'llms.txt').exists(): warnings.append('llms.txt missing')

print('SEO QA', 'PASS' if not errors else 'FAIL')
print('Indexable pages:',len(index_files),'Article schema:',article_schema,'Recipe:',recipe_schema,'Breadcrumb:',breadcrumb_schema,'ProfilePage:',profile_schema)
print('Titles >65:',sum(len(x)>65 for x in titles),'Descriptions <105:',sum(len(x)<105 for x in descs),'Descriptions >165:',sum(len(x)>165 for x in descs))
if warnings:
    print('WARNINGS:',len(warnings))
    for w in warnings[:80]: print('-',w)
if errors:
    print('ERRORS:',len(errors))
    for e in errors[:120]: print('-',e)
    sys.exit(1)
