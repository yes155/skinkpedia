from __future__ import annotations

import copy
import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / 'data' / 'entity_registry.json'
SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'


ENTITY_RULES = [
    (('cullen skink',), 'cullen_skink'),
    (('dibamus irregularis',), 'dibamus_irregularis'),
    (('scincella verecunda',), 'scincella_verecunda'),
    (('red-eyed crocodile skink', 'red eyed crocodile skink', 'tribolonotus gracilis'), 'tribolonotus_gracilis'),
    (('shingleback', 'tiliqua rugosa'), 'tiliqua_rugosa'),
    (('tiliqua scincoides', 'eastern blue-tongued'), 'tiliqua_scincoides'),
    (('blue-tongue', 'blue tongued', 'blue-tongued'), 'tiliqua'),
    (('five-lined skink', 'five lined skink', 'plestiodon fasciatus'), 'plestiodon_fasciatus'),
    (('florida sand skink', 'plestiodon reynoldsi'), 'plestiodon_reynoldsi'),
    (('sandfish', 'scincus scincus'), 'scincus_scincus'),
    (('monkey-tailed', 'monkey tailed', 'solomon islands skink', 'corucia zebrata'), 'corucia_zebrata'),
    (('gidgee', "stokes's skink", 'egernia stokesii'), 'egernia_stokesii'),
    (('ocellated skink', 'chalcides ocellatus'), 'chalcides_ocellatus'),
    (('broad-headed skink', 'broadhead skink', 'plestiodon laticeps'), 'plestiodon_laticeps'),
    (('western skink', 'plestiodon skiltonianus'), 'plestiodon_skiltonianus'),
    (('ground skink', 'scincella lateralis'), 'scincella_lateralis'),
]

CARE_TERMS = ('care', 'enclosure', 'heating', 'uvb', 'humidity', 'diet', 'feeding', 'health', 'supplies', 'cost', 'buying')
WILD_TERMS = ('wild', 'north american', 'identification', 'range', 'poisonous', 'garden', 'house', 'poop', 'reproduction')
CONSERVATION_TERMS = ('conservation', 'protected', 'legal', 'law', 'wildlife')


def load_registry() -> dict:
    entities = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))['entities']
    entities.setdefault('cullen_skink', {
        '@type': 'Thing',
        'name': 'Cullen skink',
        'alternateName': 'Scottish smoked haddock soup',
        'sameAs': ['https://www.wikidata.org/wiki/Q613665', 'https://en.wikipedia.org/wiki/Cullen_skink'],
        'identifier': [{'@type': 'PropertyValue', 'propertyID': 'Wikidata', 'value': 'Q613665'}]
    })
    return entities


def clone_entity(entities: dict, key: str) -> dict:
    entity = copy.deepcopy(entities[key])
    entity['@id'] = '#entity-' + key.replace('_', '-')
    return entity


def select_primary_entity(text: str) -> str:
    haystack = text.lower()
    for needles, key in ENTITY_RULES:
        if any(n in haystack for n in needles):
            return key
    return 'scincidae'


def select_mentions(text: str, primary: str) -> list[str]:
    haystack = text.lower()
    mentions = ['scincidae']
    if any(term in haystack for term in CARE_TERMS):
        mentions.append('reptile_husbandry')
    if any(term in haystack for term in WILD_TERMS):
        mentions.append('wildlife_identification')
    if any(term in haystack for term in CONSERVATION_TERMS):
        mentions.append('conservation_biology')
    out = []
    for key in mentions:
        if key != primary and key not in out:
            out.append(key)
    return out[:4]


def node_types(node: dict) -> list[str]:
    t = node.get('@type')
    return t if isinstance(t, list) else [t]


def find_nodes(graph: list, typename: str) -> list[dict]:
    return [node for node in graph if isinstance(node, dict) and typename in node_types(node)]


def page_text(soup: BeautifulSoup, graph: list) -> str:
    pieces = []
    if soup.title:
        pieces.append(soup.title.get_text(' ', strip=True))
    h1 = soup.find('h1')
    if h1:
        pieces.append(h1.get_text(' ', strip=True))
    desc = soup.find('meta', attrs={'name': 'description'})
    if desc and desc.get('content'):
        pieces.append(desc['content'])
    for node in graph:
        if isinstance(node, dict):
            for k in ('name', 'headline', 'description'):
                if isinstance(node.get(k), str):
                    pieces.append(node[k])
    return ' '.join(pieces)


def page_kind(canonical: str) -> str:
    path = urlparse(canonical).path
    if path == '/':
        return 'home'
    if path.startswith('/authors/') or path.startswith('/editors/'):
        return 'profile'
    if path in {'/about/', '/editorial-policy/', '/corrections-policy/', '/sources-research-methodology/', '/contact/', '/privacy/', '/affiliate-disclosure/'}:
        return 'trust'
    return 'article'


def extract_modified_date(data: dict) -> str:
    graph = data.get('@graph', []) if isinstance(data, dict) else []
    for typename in ('Article', 'Recipe', 'ProfilePage', 'WebPage'):
        for node in find_nodes(graph, typename):
            value = node.get('dateModified')
            if isinstance(value, str) and re.match(r'^\d{4}-\d{2}-\d{2}', value):
                return value[:10]
    return date.today().isoformat()


def enrich_jsonld(data: dict, soup: BeautifulSoup, entities: dict) -> tuple[dict, str, list[str]]:
    graph = data.get('@graph') if isinstance(data, dict) else None
    if not isinstance(graph, list):
        return data, '', []

    canonical = ''
    for node in graph:
        if isinstance(node, dict) and node.get('url'):
            canonical = node['url']
            break
    link_can = soup.find('link', rel='canonical')
    if link_can and link_can.get('href'):
        canonical = link_can['href']

    kind = page_kind(canonical)
    text = page_text(soup, graph)
    primary_key = select_primary_entity(text)
    mention_keys = select_mentions(text, primary_key)
    primary_entity = clone_entity(entities, primary_key)
    mention_entities = [clone_entity(entities, key) for key in mention_keys if key in entities]

    for website in find_nodes(graph, 'WebSite'):
        website.setdefault('about', clone_entity(entities, 'scincidae'))
        website.setdefault('mentions', [clone_entity(entities, 'reptile_husbandry'), clone_entity(entities, 'wildlife_identification')])

    for org in find_nodes(graph, 'Organization'):
        org.setdefault('knowsAbout', [
            'skinks', 'Scincidae', 'skink care', 'skink identification', 'skink biology', 'reptile husbandry'
        ])

    for node in graph:
        if not isinstance(node, dict):
            continue
        types = node_types(node)
        if any(t in types for t in ('Article', 'Recipe')):
            node['about'] = primary_entity
            if mention_entities:
                node['mentions'] = mention_entities
        elif 'WebPage' in types and kind in {'home', 'trust', 'article'}:
            node.setdefault('about', primary_entity)
            if mention_entities:
                node.setdefault('mentions', mention_entities)
        elif 'ProfilePage' in types:
            node.setdefault('about', {'@type': 'Thing', 'name': 'Editorial expertise and contributor identity'})

    data['@graph'] = graph
    return data, primary_key, mention_keys


def update_sitemap_lastmod(dist: Path, modified_by_url: dict[str, str]) -> None:
    sitemap = dist / 'sitemap.xml'
    if not sitemap.exists():
        return
    ET.register_namespace('', SITEMAP_NS)
    tree = ET.parse(sitemap)
    root = tree.getroot()
    ns = {'s': SITEMAP_NS}
    fallback = date.today().isoformat()
    for url_node in root.findall('s:url', ns):
        loc = url_node.find('s:loc', ns)
        if loc is None or not loc.text:
            continue
        lastmod = url_node.find('s:lastmod', ns)
        if lastmod is None:
            lastmod = ET.SubElement(url_node, f'{{{SITEMAP_NS}}}lastmod')
        lastmod.text = modified_by_url.get(loc.text, fallback)
    tree.write(sitemap, encoding='utf-8', xml_declaration=True)


def append_llms_summary(dist: Path, summary: dict) -> None:
    llms = dist / 'llms.txt'
    if not llms.exists():
        return
    text = llms.read_text(encoding='utf-8')
    marker = '\n## Entity graph\n'
    if marker in text:
        text = text.split(marker, 1)[0].rstrip() + '\n'
    lines = [marker.rstrip(), '', 'Skinkpedia uses structured entity references for major skink taxa, contributor profiles, source methodology and care concepts.']
    for key, count in sorted(summary.items()):
        lines.append(f'- {key}: {count} page(s)')
    lines.extend([
        '',
        'Machine-readable entity output: https://skinkpedia.online/entity-graph.json',
        'Freshness output: sitemap URLs include lastmod values derived from page-level dateModified metadata.'
    ])
    llms.write_text(text.rstrip() + '\n\n' + '\n'.join(lines) + '\n', encoding='utf-8')


def enrich_dist_entity_graph(dist: Path | None = None) -> dict:
    dist = Path(dist) if dist else ROOT / 'dist'
    if not dist.exists():
        return {'pages': 0, 'entities': {}}
    entities = load_registry()
    summary: dict[str, int] = {}
    manifest = []
    modified_by_url: dict[str, str] = {}

    for html_file in sorted(dist.rglob('index.html')):
        soup = BeautifulSoup(html_file.read_text(encoding='utf-8'), 'html.parser')
        script = soup.find('script', attrs={'type': 'application/ld+json'})
        if not script:
            continue
        try:
            data = json.loads(script.string or script.get_text())
        except Exception:
            continue
        data, primary_key, mentions = enrich_jsonld(data, soup, entities)
        if not primary_key:
            continue
        modified = extract_modified_date(data)
        script.string = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        html_file.write_text(str(soup), encoding='utf-8')
        summary[primary_key] = summary.get(primary_key, 0) + 1
        can = soup.find('link', rel='canonical')
        canonical = can.get('href') if can else ''
        if canonical:
            modified_by_url[canonical] = modified
        manifest.append({
            'path': str(html_file.relative_to(dist)).replace('\\', '/'),
            'canonical': canonical,
            'primaryEntity': primary_key,
            'mentions': mentions,
            'dateModified': modified,
        })

    update_sitemap_lastmod(dist, modified_by_url)
    (dist / 'entity-graph.json').write_text(json.dumps({'pages': manifest, 'entityCounts': summary}, ensure_ascii=False, indent=2), encoding='utf-8')
    append_llms_summary(dist, summary)
    print('Entity graph enriched', len(manifest), 'pages')
    print('Sitemap lastmod updated', len(modified_by_url), 'URLs')
    return {'pages': len(manifest), 'entities': summary}


if __name__ == '__main__':
    enrich_dist_entity_graph()
