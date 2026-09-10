from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import re, sys
ROOT=Path(__file__).resolve().parents[1]; DIST=ROOT/'dist'
html=list(DIST.rglob('*.html'))
errs=[]
article_pages=0; related_blocks=0; reference_pages=0
source_articles=list((ROOT/'content'/'articles').glob('*.md'))
source_trust=list((ROOT/'content'/'trust').glob('*.md'))
expected_html=1+len(source_articles)+len(source_trust)+1  # homepage + articles + trust + 404
if len(html)!=expected_html: errs.append(f'HTML file count expected {expected_html}, found {len(html)}')
paths=set()
for f in html:
    rel=f.relative_to(DIST)
    if rel.name=='index.html': url='/' if rel.parent==Path('.') else '/'+str(rel.parent).replace('\\','/')+'/'
    elif rel.name=='404.html': url='/404.html'
    else: url='/'+str(rel).replace('\\','/')
    paths.add(url)
for f in html:
    if f.name=='404.html': continue
    s=BeautifulSoup(f.read_text(encoding='utf-8'),'html.parser')
    h1=s.find_all('h1')
    if len(h1)!=1: errs.append(f'{f}: H1 count {len(h1)}')
    if not s.title or not s.title.get_text(strip=True): errs.append(f'{f}: missing title')
    if not s.find('meta',attrs={'name':'description'}): errs.append(f'{f}: missing description')
    if not s.find('link',attrs={'rel':'canonical'}): errs.append(f'{f}: missing canonical')
    for a in s.find_all('a',href=True):
        href=a['href']
        if href.startswith('/') and not href.startswith('//'):
            p=href.split('#')[0].split('?')[0]
            if p and p not in paths and not p.startswith('/assets/'):
                errs.append(f'{f}: broken internal link {href}')
    for im in s.find_all('img'):
        if not im.get('alt') and im.get('alt')!='': errs.append(f'{f}: image missing alt {im.get("src")}')
        src=im.get('src','')
        clean_src=src.split('#')[0].split('?')[0]
        if clean_src.startswith('/assets/'):
            asset=DIST/clean_src.lstrip('/')
            if not asset.exists(): errs.append(f'{f}: missing asset {src}')

    article=s.select_one('.article-layout')
    if article:
        article_pages += 1
        related=article.select_one('.related-block')
        if not related:
            errs.append(f'{f}: missing Related guides block')
        else:
            related_blocks += 1
            related_links=related.select('.link-card a[href^="/"]')
            if len(related_links)<2: errs.append(f'{f}: Related guides has fewer than 2 internal cards')

        body=s.select_one('.article-body')
        page_has_refs=False
        if body:
            for heading in body.find_all(['h2','h3']):
                label=heading.get_text(' ',strip=True).lower()
                if not (label=='references' or label.startswith('references ') or label in {'sources','sources & references','sources and references'}):
                    continue
                page_has_refs=True
                level=int(heading.name[1])
                node=heading.next_sibling
                while node is not None:
                    nxt=node.next_sibling
                    if getattr(node,'name',None) in {'h2','h3'} and int(node.name[1])<=level:
                        break
                    if getattr(node,'find_all',None):
                        links=[]
                        if getattr(node,'name',None)=='a': links.append(node)
                        links.extend(node.find_all('a',href=True))
                        for a in links:
                            href=a.get('href','')
                            if href.startswith(('http://','https://','//')):
                                errs.append(f'{f}: live external link inside References: {href}')
                    node=nxt
        if page_has_refs: reference_pages += 1
# hero inventory: one unique 1600x900 WEBP hero per article
heroes=list((DIST/'assets/images/heroes').glob('*.webp'))
expected_heroes=len(source_articles)
if len(heroes)!=expected_heroes: errs.append(f'Hero count expected {expected_heroes}, found {len(heroes)}')
for p in heroes:
    im=Image.open(p)
    if im.size!=(1600,900): errs.append(f'{p}: dimensions {im.size}')
    if p.name in {'out-020-dibamus-irregularis-hero.webp','out-021-scincella-verecunda-hero.webp'} and p.stat().st_size < 50000:
        errs.append(f'{p}: suspiciously small hero file, possible corruption')
# banned artifacts
for f in html:
    txt=f.read_text(encoding='utf-8')
    for bad in ['notebook.google.com','[SOURCE NEEDED BEFORE PUBLICATION]','file://','C:\\','D:\\']:
        if bad.lower() in txt.lower(): errs.append(f'{f}: banned artifact {bad}')
print('QA', 'PASS' if not errs else 'FAIL')
print('Article pages:',article_pages,'Related blocks:',related_blocks,'Reference sections:',reference_pages)
if errs:
    for e in errs[:200]: print('-',e)
    sys.exit(1)
print('HTML pages:',len(html),'Heroes:',len(heroes),'Internal link/assets checks: clean')
