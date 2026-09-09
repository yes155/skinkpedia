from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import re, sys
ROOT=Path(__file__).resolve().parents[1]; DIST=ROOT/'dist'
html=list(DIST.rglob('*.html'))
errs=[]
# expected: home + 53 + 7 trust + 404
if len(html)!=62: errs.append(f'HTML file count expected 62, found {len(html)}')
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
        if src.startswith('/assets/'):
            asset=DIST/src.lstrip('/')
            if not asset.exists(): errs.append(f'{f}: missing asset {src}')
# hero inventory
heroes=list((DIST/'assets/images/heroes').glob('*.webp'))
if len(heroes)!=53: errs.append(f'Hero count expected 53, found {len(heroes)}')
for p in heroes:
    im=Image.open(p)
    if im.size!=(1600,900): errs.append(f'{p}: dimensions {im.size}')
# banned artifacts
for f in html:
    txt=f.read_text(encoding='utf-8')
    for bad in ['notebook.google.com','[SOURCE NEEDED BEFORE PUBLICATION]','file://','C:\\','D:\\']:
        if bad.lower() in txt.lower(): errs.append(f'{f}: banned artifact {bad}')
print('QA', 'PASS' if not errs else 'FAIL')
if errs:
    for e in errs[:200]: print('-',e)
    sys.exit(1)
print('HTML pages:',len(html),'Heroes:',len(heroes),'Internal link/assets checks: clean')
