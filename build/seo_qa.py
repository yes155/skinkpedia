from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urlparse
import json, re, sys, xml.etree.ElementTree as ET
from config import SITE_URL

ROOT=Path(__file__).resolve().parents[1]; DIST=ROOT/'dist'
errors=[]; warnings=[]; rows=[]
resource_manifest={}

try:
    from info_gain_resources import apply_info_gain_resources
    resource_manifest=apply_info_gain_resources(DIST)
except Exception as e:
    errors.append(f'information gain resource preparation failed: {e}')

try:
    from entity_graph import enrich_dist_entity_graph
    enrich_dist_entity_graph(DIST)
except Exception as e:
    errors.append(f'entity graph enrichment failed: {e}')

index_files=list(DIST.rglob('index.html'))
canonicals=[]; titles=[]; descs=[]
article_schema=0; recipe_schema=0; breadcrumb_schema=0; profile_schema=0

TRUST_PAGE_PATHS={
    '/about/',
    '/editorial-policy/',
    '/corrections-policy/',
    '/sources-research-methodology/',
    '/contact/',
    '/privacy/',
    '/affiliate-disclosure/',
    '/resources/',
}
PROFILE_PREFIXES=('/authors/','/editors/')
RECIPE_PATHS={'/extras/cullen-skink-recipe/'}
DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}$')


def node_types(node):
    t=node.get('@type')
    return t if isinstance(t,list) else [t]


def first_node(graph, typename):
    for node in graph:
        if isinstance(node,dict) and typename in node_types(node):
            return node
    return None


def has_dates(node):
    return bool(isinstance(node,dict) and node.get('datePublished') and node.get('dateModified'))


def has_entity_link(value):
    if isinstance(value, dict):
        same=value.get('sameAs') or value.get('url') or value.get('identifier')
        if same:
            return True
        return any(has_entity_link(v) for v in value.values())
    if isinstance(value, list):
        return any(has_entity_link(v) for v in value)
    return False


for f in index_files:
    s=BeautifulSoup(f.read_text(encoding='utf-8'),'html.parser')
    title=s.title.get_text(' ',strip=True) if s.title else ''
    desc=(s.find('meta',attrs={'name':'description'}) or {}).get('content','') if s.find('meta',attrs={'name':'description'}) else ''
    can=(s.find('link',rel='canonical') or {}).get('href','') if s.find('link',rel='canonical') else ''
    canonical_path=urlparse(can).path if can else ''
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
            types += node_types(node)
        article_schema += types.count('Article')
        recipe_schema += types.count('Recipe')
        breadcrumb_schema += types.count('BreadcrumbList')
        profile_schema += types.count('ProfilePage')
        if can!=SITE_URL+'/' and 'BreadcrumbList' not in types: errors.append(f'{f}: missing BreadcrumbList schema')

        is_home = can == SITE_URL+'/'
        is_trust_page = canonical_path in TRUST_PAGE_PATHS
        is_profile_page = canonical_path.startswith(PROFILE_PREFIXES)
        is_recipe_page = canonical_path in RECIPE_PATHS

        if not is_home and not any(has_dates(node) for node in graph if isinstance(node,dict)):
            errors.append(f'{f}: missing datePublished/dateModified schema')

        if is_recipe_page:
            recipe=first_node(graph,'Recipe')
            if not recipe: errors.append(f'{f}: recipe page missing Recipe schema')
            else:
                for field in ['author','reviewedBy','datePublished','dateModified']:
                    if not recipe.get(field): errors.append(f'{f}: Recipe schema missing {field}')
                if not recipe.get('about') or not has_entity_link(recipe.get('about')):
                    errors.append(f'{f}: Recipe schema missing linked about entity')
            if 'Article' in types: warnings.append(f'{f}: recipe page also has Article schema')
        elif is_profile_page:
            profile=first_node(graph,'ProfilePage'); person=first_node(graph,'Person')
            if not profile: errors.append(f'{f}: profile page missing ProfilePage schema')
            if not person: errors.append(f'{f}: profile page missing Person schema')
            else:
                for field in ['image','sameAs','jobTitle']:
                    if not person.get(field): errors.append(f'{f}: Person schema missing {field}')
            if 'Article' in types: warnings.append(f'{f}: profile page also has Article schema')
        elif not is_home and not is_trust_page:
            article=first_node(graph,'Article')
            if not article: errors.append(f'{f}: article page missing Article schema')
            else:
                for field in ['author','reviewedBy','datePublished','dateModified']:
                    if not article.get(field): errors.append(f'{f}: Article schema missing {field}')
                if not article.get('about') or not has_entity_link(article.get('about')):
                    errors.append(f'{f}: Article schema missing linked about entity')
    rows.append((f,can,title,desc))

for value,n in Counter(titles).items():
    if n>1: errors.append(f'duplicate title: {value!r} x{n}')
for value,n in Counter(descs).items():
    if n>1: errors.append(f'duplicate description: {value!r} x{n}')
for value,n in Counter(canonicals).items():
    if n>1: errors.append(f'duplicate canonical: {value!r} x{n}')

sm=DIST/'sitemap.xml'
try:
    root=ET.parse(sm).getroot(); ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    locs=[e.text for e in root.findall('s:url/s:loc',ns)]
    expected_urls=len(canonicals)
    if len(locs)!=expected_urls: errors.append(f'sitemap expected {expected_urls} URLs, found {len(locs)}')
    if len(locs)!=len(set(locs)): errors.append('sitemap contains duplicate URLs')
    if set(locs)!=set(canonicals): errors.append('sitemap URLs do not exactly match indexable canonicals')
    for u in root.findall('s:url', ns):
        loc = u.find('s:loc', ns)
        lastmod = u.find('s:lastmod', ns)
        if lastmod is None or not lastmod.text:
            errors.append(f'sitemap URL missing lastmod: {loc.text if loc is not None else "unknown"}')
        elif not DATE_RE.match(lastmod.text.strip()):
            errors.append(f'sitemap URL invalid lastmod: {loc.text if loc is not None else "unknown"} -> {lastmod.text}')
except Exception as e: errors.append(f'invalid sitemap: {e}')
robots=(DIST/'robots.txt').read_text(encoding='utf-8')
if f'Sitemap: {SITE_URL}/sitemap.xml' not in robots: errors.append('robots.txt sitemap mismatch')
s404=BeautifulSoup((DIST/'404.html').read_text(encoding='utf-8'),'html.parser')
r404=s404.find('meta',attrs={'name':'robots'})
if not r404 or 'noindex' not in r404.get('content',''): errors.append('404 missing noindex')
if not (DIST/'llms.txt').exists(): warnings.append('llms.txt missing')
if not (DIST/'entity-graph.json').exists(): errors.append('entity-graph.json missing')
else:
    try:
        entity_manifest=json.loads((DIST/'entity-graph.json').read_text(encoding='utf-8'))
        if len(entity_manifest.get('pages',[])) != len(index_files):
            errors.append('entity-graph.json page count does not match indexable pages')
    except Exception as e:
        errors.append(f'entity-graph.json invalid: {e}')

required_resources=[
    'assets/downloads/skink-care-quick-start.pdf',
    'assets/downloads/blue-tongue-skink-setup-checklist.pdf',
    'assets/downloads/pet-skink-species-comparison-matrix.pdf',
    'assets/downloads/skink-health-triage-sheet.pdf',
    'assets/data/skink-species-decision-dataset.csv',
    'assets/data/skink-care-decision-framework.csv',
    'assets/data/skinkpedia-resource-manifest.json',
]
for rel in required_resources:
    p=DIST/rel
    if not p.exists():
        errors.append(f'missing information-gain resource: {rel}')
    elif p.suffix == '.pdf':
        data=p.read_bytes()[:4]
        if data != b'%PDF': errors.append(f'information-gain PDF is invalid: {rel}')
        if p.stat().st_size < 2500: errors.append(f'information-gain PDF suspiciously small: {rel}')
    elif p.stat().st_size < 100:
        errors.append(f'information-gain data file suspiciously small: {rel}')
if not (DIST/'resources'/'index.html').exists():
    errors.append('resources page missing: /resources/')
if resource_manifest.get('missing_pages'):
    errors.append('information-gain enrichment missing pages: '+', '.join(resource_manifest.get('missing_pages',[])))
if len(resource_manifest.get('injected_pages',[])) < 5:
    errors.append('information-gain enrichment did not reach all priority pages')
if resource_manifest.get('resource_page') != '/resources/':
    errors.append('information-gain resources page was not generated')

print('SEO QA', 'PASS' if not errors else 'FAIL')
print('Indexable pages:',len(index_files),'Article schema:',article_schema,'Recipe:',recipe_schema,'Breadcrumb:',breadcrumb_schema,'ProfilePage:',profile_schema)
print('Titles >65:',sum(len(x)>65 for x in titles),'Descriptions <105:',sum(len(x)<105 for x in descs),'Descriptions >165:',sum(len(x)>165 for x in descs))
print('Information gain resources:',len(resource_manifest.get('pdfs',[])),'PDFs,',len(resource_manifest.get('datasets',[])),'datasets,',len(resource_manifest.get('injected_pages',[])),'pages enriched, resource page:',resource_manifest.get('resource_page'))
if warnings:
    print('WARNINGS:',len(warnings))
    for w in warnings[:80]: print('-',w)
if errors:
    print('ERRORS:',len(errors))
    for e in errors[:120]: print('-',e)
    sys.exit(1)
