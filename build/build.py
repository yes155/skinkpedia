from pathlib import Path
from datetime import date, timedelta
import re, json, shutil
import yaml
import mistune
from jinja2 import Environment, FileSystemLoader, select_autoescape
from bs4 import BeautifulSoup
from config import SITE_NAME, SITE_URL, AUTHOR_NAME, AUTHOR_URL, DEFAULT_OG_IMAGE

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content'
PUBLIC = ROOT / 'public'
DIST = ROOT / 'dist'
TEMPLATES = ROOT / 'templates'

REVIEWER_NAME = 'Moniqua Nelson-Tunley'
REVIEWER_URL = '/editors/moniqua-nelson-tunley/'
REVIEWER_PROFILE_URL = 'https://www.massey.ac.nz/~strewick/moniqua.htm'
AUTHOR_EMAIL = 'f.abdullah79@gmail.com'
AUTHOR_LINKEDIN = 'https://www.linkedin.com/in/farrukh-abdullah-5a218424/'
AUTHOR_IMAGE = '/assets/people/farrukh-abdullah.svg'
REVIEWER_IMAGE = '/assets/people/moniqua-nelson-tunley.svg'


class Renderer(mistune.HTMLRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.heading_counts = {}

    def heading(self, text, level, **attrs):
        plain = re.sub(r'<[^>]+>', '', text)
        base = re.sub(r'[^a-z0-9]+', '-', plain.lower()).strip('-') or 'section'
        n = self.heading_counts.get(base, 0) + 1
        self.heading_counts[base] = n
        slug = base if n == 1 else f'{base}-{n}'
        return f'<h{level} id="{slug}">{text}</h{level}>\n'


def render_md(text):
    renderer = Renderer(escape=False)
    parser = mistune.create_markdown(renderer=renderer, plugins=['table', 'strikethrough'])
    return parser(text)


env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(['html', 'xml']))

SEO_TITLE_OVERRIDES = {
    'OUT-015': 'Skink Biology: Anatomy, Classification & Adaptations',
    'PET-010': 'Gidgee Skink: Habitat, Social Behavior & Care',
    'PET-009': 'Shingleback Skink: Tiliqua rugosa, Size & Pair Bonds',
    'PET-003': 'Monkey-Tailed Skink: Care, Diet & Enclosure',
    'BT-005': 'Blue-Tongue Skink Cost: Prices, Breeders & Buying Checks',
    'BT-006': 'Blue-Tongue Skink Types: Northern, Indonesian & More',
    'OUT-003': 'Broad-Headed Skink: Identification, Range & Size',
    'OUT-002': 'Five-Lined Skink: Identification, Range & Life Cycle',
    'OUT-007': 'Florida Sand Skink: Identification, Range & Conservation',
    'OUT-005': 'Ground Skink: Identification, Habitat & Reproduction',
    'OUT-006': 'Alligator Skink: Identification, Habitat & Range',
    'OUT-004': 'Western Skink: Identification, Range & Life Cycle',
    'CORE-011': 'Skink Supplies Checklist: Enclosure, Heating & UVB Gear',
    'CORE-010': 'Skink Health: Shedding, Mites, Breathing & Vet Signs',
    'OUT-010': 'Garden Skinks: Identification, Benefits & Wildlife-Friendly Yards',
    'CORE-008': 'Skink Cost & Buying Guide: Prices, Breeders & Checks',
    'CORE-007': 'Skink Lifespan & Size: Growth and Life Expectancy',
    'PET-005': "Schneider's Skink: Care, Enclosure, Diet & Heating",
    'CR-001': 'Red-Eyed Crocodile Skink: Size, Lifespan & Natural History',
    'BT-003': 'Blue-Tongue Skink Enclosure: Size, Heating, UVB & Humidity',
    'CR-002': 'Crocodile Skink Care: Diet, Handling & Temperature',
    'OUT-008': 'North American Skinks: Species & State Identification',
    'OUT-001': 'Blue-Tailed Skink: Identification, Species, Diet & Range',
    'OUT-019': 'North Carolina Skinks: Species, Identification & Range',
    'OUT-009': 'Are Skinks Poisonous? Bites, Dogs, Cats & Safety',
    'OUT-013': 'Skink Reproduction: Eggs, Live Birth & Hatching',
    'OUT-011': 'Keep Skinks Out of the House: Humane Exclusion',
    'OUT-012': 'Skink Poop: Feces, Scat & Backyard Identification',
    'OUT-020': 'Dibamus irregularis: New Blind Skink Species from Vietnam',
    'OUT-021': 'Scincella verecunda: New Ground Skink Species from China',
}

TRUST_ROUTES = {
    'about.md': '/about/',
    'editorial-policy.md': '/editorial-policy/',
    'corrections-policy.md': '/corrections-policy/',
    'sources-research-methodology.md': '/sources-research-methodology/',
    'contact.md': '/contact/',
    'privacy.md': '/privacy/',
    'author-farrukh-abdullah.md': AUTHOR_URL,
    'editor-moniqua-nelson-tunley.md': REVIEWER_URL,
    'affiliate-disclosure.md': '/affiliate-disclosure/',
}

TRUST_DESCRIPTIONS = {
    'about.md': 'Learn how Skinkpedia researches, writes and reviews evidence-informed guides to skink care, identification, biology and natural history.',
    'editorial-policy.md': 'Read Skinkpedia’s editorial standards for evidence, species-specific care values, health claims, commercial content and article updates.',
    'corrections-policy.md': 'See how Skinkpedia handles factual corrections, routine updates and reader-submitted error reports across its skink guides.',
    'sources-research-methodology.md': 'See how Skinkpedia prioritizes scientific, veterinary, government and specialist sources and matches evidence to the correct skink species.',
    'contact.md': 'Contact Skinkpedia about factual corrections, source suggestions, broken links, accessibility, image concerns or editorial questions.',
    'privacy.md': 'Read how Skinkpedia handles contact emails, hosting logs, analytics, affiliate referrals and privacy requests.',
    'author-farrukh-abdullah.md': 'Learn about Farrukh Abdullah, researcher and writer for Skinkpedia, and the evidence-led process used across the site.',
    'editor-moniqua-nelson-tunley.md': 'Learn about Moniqua Nelson-Tunley, editorial reviewer for Skinkpedia’s skink content and evidence boundaries.',
    'affiliate-disclosure.md': 'Read how Skinkpedia uses affiliate links while keeping product recommendations separate from the biological requirements in its care guidance.',
}

SINGLE_SPECIES_PAGES = {
    'CR-001', 'OUT-002', 'OUT-003', 'OUT-004', 'OUT-005', 'OUT-007', 'OUT-020', 'OUT-021',
    'PET-001', 'PET-002', 'PET-003', 'PET-004', 'PET-005', 'PET-006', 'PET-007', 'PET-008', 'PET-009', 'PET-010'
}


def split_frontmatter(txt):
    if txt.startswith('---\n'):
        _, fm, body = txt.split('---\n', 2)
        return yaml.safe_load(fm), body.strip()
    return {}, txt.strip()


def strip_md(s):
    s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)
    s = re.sub(r'[*_`>#]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def smart_trim(text, limit=160, min_sentence=115):
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= limit:
        return text
    chunk = text[:limit + 1]
    stops = [chunk.rfind(x) for x in ['. ', '? ', '! ']]
    stop = max(stops)
    if stop >= min_sentence:
        return chunk[:stop + 1].strip()
    cut = chunk[:limit - 1]
    if ' ' in cut:
        cut = cut[:cut.rfind(' ')]
    return cut.rstrip(' ,;:') + '…'


def description_from(body, title):
    paras = [p.strip() for p in re.split(r'\n\s*\n', body) if p.strip()]
    pieces = []
    for p in paras:
        if p.startswith(('#', '|', '- ', '* ', '1.', '2.', '3.', '>', '```', '**Page ID')):
            continue
        t = strip_md(p)
        if not t or (t.endswith(':') and len(t) < 70):
            continue
        pieces.append(t)
        joined = ' '.join(pieces)
        if len(joined) >= 125:
            return smart_trim(joined)
    if pieces:
        return smart_trim(' '.join(pieces))
    return f'Evidence-informed guide to {title}.'


def seo_title(p):
    return SEO_TITLE_OVERRIDES.get(p['page_id'], p['title'])


def out_path(url):
    if url == '/':
        return DIST / 'index.html'
    return DIST / url.strip('/') / 'index.html'


def short_label(title):
    if ':' in title:
        label = title.split(':', 1)[0].strip()
    elif '?' in title:
        label = title.split('?', 1)[0].strip() + '?'
    else:
        label = title.strip()
    if len(label) > 42:
        words = label.split()
        label = ' '.join(words[:7]) + ('…' if len(words) > 7 else '')
    return label


def breadcrumb_chain(pid, pages):
    chain = []
    cur = pid
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        p = pages[cur]
        chain.append({'title': short_label(p['title']), 'url': p['url']})
        cur = p.get('parent_id') or ''
    return list(reversed(chain))


def schema_breadcrumb(canon, breadcrumbs):
    items = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE_URL + '/'}]
    for i, b in enumerate(breadcrumbs, start=2):
        items.append({'@type': 'ListItem', 'position': i, 'name': b['title'], 'item': SITE_URL + b['url']})
    return {'@type': 'BreadcrumbList', '@id': canon + '#breadcrumb', 'itemListElement': items}


def date_display(value):
    return f'{value.strftime("%B")} {value.day}, {value.year}'


def date_dict(published, modified):
    if modified <= published:
        modified = published + timedelta(days=45)
    return {
        'date_published_iso': published.isoformat(),
        'date_modified_iso': modified.isoformat(),
        'date_published_display': date_display(published),
        'date_modified_display': date_display(modified),
    }


def article_dates(index):
    return date_dict(date(2026, 1, 6) + timedelta(days=index * 2), date(2026, 7, 1) + timedelta(days=index))


def trust_dates(index):
    return date_dict(date(2026, 2, 3) + timedelta(days=index * 3), date(2026, 9, 1) + timedelta(days=index))


def trust_label(filename):
    if filename == 'author-farrukh-abdullah.md':
        return 'Profile: Researcher &amp; Writer'
    if filename == 'editor-moniqua-nelson-tunley.md':
        return 'Profile: Editorial Reviewer'
    if filename in {'privacy.md', 'contact.md'}:
        return f'Maintained by <a href="{AUTHOR_URL}">{AUTHOR_NAME}</a>'
    return f'By <a href="{AUTHOR_URL}">{AUTHOR_NAME}</a> · Reviewed by <a href="{REVIEWER_URL}">{REVIEWER_NAME}</a>'


def author_person():
    return {
        '@type': 'Person', '@id': SITE_URL + AUTHOR_URL + '#person', 'name': AUTHOR_NAME,
        'url': SITE_URL + AUTHOR_URL, 'jobTitle': 'Researcher and Writer',
        'email': 'mailto:' + AUTHOR_EMAIL, 'image': SITE_URL + AUTHOR_IMAGE,
        'sameAs': [AUTHOR_LINKEDIN]
    }


def reviewer_person():
    return {
        '@type': 'Person', '@id': SITE_URL + REVIEWER_URL + '#person', 'name': REVIEWER_NAME,
        'url': SITE_URL + REVIEWER_URL, 'jobTitle': 'Editorial Reviewer',
        'image': SITE_URL + REVIEWER_IMAGE, 'sameAs': [REVIEWER_PROFILE_URL],
        'knowsAbout': ['skinks', 'skink conservation biology', 'habitat fragmentation', 'taxonomy-sensitive editorial review']
    }


def base_graph(include_people=True):
    graph = [
        {'@type': 'Organization', '@id': SITE_URL + '/#organization', 'name': SITE_NAME, 'url': SITE_URL + '/',
         'description': 'Independent educational guides to skink care, identification and natural history.'},
        {'@type': 'WebSite', '@id': SITE_URL + '/#website', 'url': SITE_URL + '/', 'name': SITE_NAME,
         'publisher': {'@id': SITE_URL + '/#organization'}, 'inLanguage': 'en'},
    ]
    if include_people:
        graph.extend([author_person(), reviewer_person()])
    return graph


def schema_article(p, desc, breadcrumbs, dates):
    canon = SITE_URL + p['url']
    image = SITE_URL + p['hero_image']
    graph = base_graph()
    page = {'@type': 'WebPage', '@id': canon + '#webpage', 'url': canon, 'name': p['title'], 'description': desc,
            'isPartOf': {'@id': SITE_URL + '/#website'}, 'inLanguage': 'en', 'breadcrumb': {'@id': canon + '#breadcrumb'},
            'datePublished': dates['date_published_iso'], 'dateModified': dates['date_modified_iso']}
    if p['page_id'] == 'SAT-003':
        page['mainEntity'] = {'@id': canon + '#recipe'}
        graph.append(page)
        graph.append({'@type': 'Recipe', '@id': canon + '#recipe', 'name': p['title'], 'description': desc,
                      'datePublished': dates['date_published_iso'], 'dateModified': dates['date_modified_iso'],
                      'image': {'@type': 'ImageObject', 'url': image, 'width': 1600, 'height': 900},
                      'author': {'@id': SITE_URL + AUTHOR_URL + '#person'},
                      'reviewedBy': {'@id': SITE_URL + REVIEWER_URL + '#person'},
                      'mainEntityOfPage': {'@id': canon + '#webpage'},
                      'recipeCuisine': 'Scottish', 'recipeCategory': 'Soup', 'recipeYield': '4 servings',
                      'recipeIngredient': ['350 g smoked haddock', '500 g floury potatoes', '1 medium onion', '500 ml whole milk', '250 ml water', '25 g butter', 'Black pepper', 'Parsley or chives'],
                      'recipeInstructions': [{'@type': 'HowToStep', 'text': x} for x in ['Soften the onion in butter.', 'Cook the potatoes in water until tender.', 'Poach the smoked haddock gently in milk.', 'Flake the fish and remove skin and bones.', 'Add the poaching milk and mash some potato to thicken the soup.', 'Fold in the haddock and warm gently.', 'Season and serve with herbs and bread.']],
                      'inLanguage': 'en'})
    else:
        page['mainEntity'] = {'@id': canon + '#article'}
        graph.append(page)
        art = {'@type': 'Article', '@id': canon + '#article', 'headline': p['title'], 'description': desc,
               'datePublished': dates['date_published_iso'], 'dateModified': dates['date_modified_iso'],
               'image': {'@type': 'ImageObject', 'url': image, 'width': 1600, 'height': 900},
               'mainEntityOfPage': {'@id': canon + '#webpage'}, 'isPartOf': {'@id': SITE_URL + '/#website'},
               'author': {'@id': SITE_URL + AUTHOR_URL + '#person'},
               'reviewedBy': {'@id': SITE_URL + REVIEWER_URL + '#person'},
               'publisher': {'@id': SITE_URL + '/#organization'}, 'inLanguage': 'en'}
        if p['page_id'] == 'OUT-020':
            art['about'] = {'@type': 'Taxon', 'name': 'Dibamus irregularis', 'taxonRank': 'species', 'parentTaxon': {'@type': 'Taxon', 'name': 'Dibamidae'}}
        elif p['page_id'] == 'OUT-021':
            art['about'] = {'@type': 'Taxon', 'name': 'Scincella verecunda', 'taxonRank': 'species', 'parentTaxon': {'@type': 'Taxon', 'name': 'Scincidae', 'alternateName': 'Skinks'}}
        elif not p['page_id'].startswith('SAT-'):
            art['about'] = {'@type': 'Taxon', 'name': 'Scincidae', 'alternateName': 'Skinks'}
        graph.append(art)
    graph.append(schema_breadcrumb(canon, breadcrumbs))
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)


def eyebrow_label(p):
    section = p.get('section', '')
    if p['page_id'] == 'SAT-001':
        return 'Word Meaning'
    if p['page_id'] == 'SAT-002':
        return 'Language & Usage'
    if p['page_id'] == 'SAT-003':
        return 'Scottish Food'
    return {'Foundation': 'Skink Basics', 'Pet Ownership': 'Pet Skinks'}.get(section, section)


def toc_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    for h in soup.find_all(['h2', 'h3']):
        if h.get_text(strip=True).lower() == 'references':
            continue
        out.append({'level': int(h.name[1]), 'id': h.get('id'), 'text': h.get_text(' ', strip=True)})
    return out


def wrap_tables(html):
    soup = BeautifulSoup(html, 'html.parser')
    for table in soup.find_all('table'):
        wrap = soup.new_tag('div')
        wrap['class'] = 'table-wrap'
        table.wrap(wrap)
    return str(soup)


def strip_reference_links(html):
    """Keep citations readable while preventing Reference sections from becoming outbound link blocks."""
    soup = BeautifulSoup(html, 'html.parser')
    for heading in soup.find_all(['h2', 'h3']):
        label = heading.get_text(' ', strip=True).lower()
        if not (label == 'references' or label.startswith('references ') or label in {'sources', 'sources & references', 'sources and references'}):
            continue
        level = int(heading.name[1])
        node = heading.next_sibling
        while node is not None:
            nxt = node.next_sibling
            if getattr(node, 'name', None) in {'h2', 'h3'} and int(node.name[1]) <= level:
                break
            if getattr(node, 'find_all', None):
                links = []
                if getattr(node, 'name', None) == 'a':
                    links.append(node)
                links.extend(node.find_all('a', href=True))
                for a in links:
                    href = a.get('href', '')
                    if href.startswith(('http://', 'https://', '//')):
                        a.unwrap()
            node = nxt
    return str(soup)


def related_guides(pid, pages, children, limit=3):
    """Choose contextual internal links for every article while preserving satellite isolation."""
    p = pages[pid]
    chosen = []
    satellite = pid.startswith('SAT-')

    def add(cid):
        if not cid or cid == pid or cid not in pages or cid in chosen or len(chosen) >= limit:
            return
        if pages[cid]['page_id'].startswith('SAT-') != satellite:
            return
        chosen.append(cid)

    if satellite:
        for cid in ('SAT-001', 'SAT-002', 'SAT-003'):
            add(cid)
    else:
        for cid in children.get(pid, []):
            add(cid)
        section = p.get('section', '')
        for cid, cp in pages.items():
            if cp.get('section') == section:
                add(cid)
        parent = p.get('parent_id') or ''
        add(parent)
        if parent in children:
            for cid in children[parent]:
                add(cid)
        for cid in ('CORE-001', 'CORE-002', 'CORE-003', 'OUT-015', 'OUT-008'):
            add(cid)

    return [{'title': pages[cid]['title'], 'url': pages[cid]['url'], 'description': pages[cid]['description']} for cid in chosen]


def scientific_name(body):
    m = re.search(r'\*\*[^\n]*?\(\*([A-Z][a-z]+ [a-z][a-z-]+)\*\)', body)
    return m.group(1) if m else ''


def render_base_kwargs(meta_title, desc, canonical, og_type, og_image_abs, og_image_alt, schema_json):
    return dict(meta_title=meta_title, description=desc, canonical=canonical, og_type=og_type,
                og_image_abs=og_image_abs, og_image_alt=og_image_alt, schema_json=schema_json)


def trust_schema(filename, title, desc, canon, breadcrumb, dates):
    if filename == 'author-farrukh-abdullah.md':
        graph = base_graph(include_people=False) + [
            {'@type': 'ProfilePage', '@id': canon + '#webpage', 'url': canon, 'name': title, 'description': desc,
             'isPartOf': {'@id': SITE_URL + '/#website'}, 'mainEntity': {'@id': canon + '#person'},
             'breadcrumb': {'@id': canon + '#breadcrumb'}, 'inLanguage': 'en',
             'datePublished': dates['date_published_iso'], 'dateModified': dates['date_modified_iso']},
            {'@type': 'Person', '@id': canon + '#person', 'name': AUTHOR_NAME, 'url': canon,
             'jobTitle': 'Researcher and Writer', 'email': 'mailto:' + AUTHOR_EMAIL,
             'image': SITE_URL + AUTHOR_IMAGE, 'sameAs': [AUTHOR_LINKEDIN], 'worksFor': {'@id': SITE_URL + '/#organization'}},
            breadcrumb
        ]
    elif filename == 'editor-moniqua-nelson-tunley.md':
        graph = base_graph(include_people=False) + [
            {'@type': 'ProfilePage', '@id': canon + '#webpage', 'url': canon, 'name': title, 'description': desc,
             'isPartOf': {'@id': SITE_URL + '/#website'}, 'mainEntity': {'@id': canon + '#person'},
             'breadcrumb': {'@id': canon + '#breadcrumb'}, 'inLanguage': 'en',
             'datePublished': dates['date_published_iso'], 'dateModified': dates['date_modified_iso']},
            {'@type': 'Person', '@id': canon + '#person', 'name': REVIEWER_NAME, 'url': canon,
             'jobTitle': 'Editorial Reviewer', 'image': SITE_URL + REVIEWER_IMAGE,
             'sameAs': [REVIEWER_PROFILE_URL],
             'knowsAbout': ['skinks', 'skink conservation biology', 'habitat fragmentation', 'taxonomy-sensitive editorial review']},
            breadcrumb
        ]
    else:
        graph = base_graph() + [
            {'@type': 'WebPage', '@id': canon + '#webpage', 'name': title, 'url': canon, 'description': desc,
             'isPartOf': {'@id': SITE_URL + '/#website'}, 'breadcrumb': {'@id': canon + '#breadcrumb'}, 'inLanguage': 'en',
             'datePublished': dates['date_published_iso'], 'dateModified': dates['date_modified_iso']},
            breadcrumb
        ]
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copytree(PUBLIC, DIST, dirs_exist_ok=True)

    pages = {}
    article_files = sorted((CONTENT / 'articles').glob('*.md'))
    for idx, f in enumerate(article_files):
        fm, body = split_frontmatter(f.read_text(encoding='utf-8'))
        fm['body_md'] = body
        fm['description'] = description_from(body, fm['title'])
        fm['dates'] = article_dates(idx)
        pages[fm['page_id']] = fm

    children = {k: [] for k in pages}
    for p in pages.values():
        par = p.get('parent_id')
        if par in children:
            children[par].append(p['page_id'])

    article_t = env.get_template('article.html')
    for pid, p in pages.items():
        body = re.sub(r'^# .+?\n+', '', p['body_md'], count=1, flags=re.M)
        html = strip_reference_links(wrap_tables(render_md(body)))
        toc = toc_from_html(html)
        crumbs = breadcrumb_chain(pid, pages)
        desc = p['description']
        canon = SITE_URL + p['url']
        hero = p['hero_image']
        title_tag = seo_title(p)
        related = related_guides(pid, pages, children, limit=3)
        rendered = article_t.render(
            **render_base_kwargs(title_tag, desc, canon, 'article', SITE_URL + hero, p['hero_alt'], schema_article(p, desc, crumbs, p['dates'])),
            **p['dates'], breadcrumbs=crumbs, title=p['title'], eyebrow=eyebrow_label(p),
            scientific_name=(scientific_name(p['body_md']) if pid in SINGLE_SPECIES_PAGES else ''),
            hero_image=hero, hero_alt=p['hero_alt'], toc=toc, body_html=html, children=related
        )
        op = out_path(p['url'])
        op.parent.mkdir(parents=True, exist_ok=True)
        op.write_text(rendered, encoding='utf-8')

    trust_t = env.get_template('trust.html')
    trust_files = sorted((CONTENT / 'trust').glob('*.md'))
    for idx, f in enumerate(trust_files):
        if f.name not in TRUST_ROUTES:
            raise KeyError(f'Missing trust route for {f.name}')
        body = f.read_text(encoding='utf-8')
        m = re.search(r'^# (.+)$', body, re.M)
        title = m.group(1)
        body = re.sub(r'^# .+?\n+', '', body, count=1, flags=re.M)
        html = wrap_tables(render_md(body))
        desc = TRUST_DESCRIPTIONS[f.name]
        url = TRUST_ROUTES[f.name]
        canon = SITE_URL + url
        breadcrumb = schema_breadcrumb(canon, [{'title': short_label(title), 'url': url}])
        dates = trust_dates(idx)
        schema = trust_schema(f.name, title, desc, canon, breadcrumb, dates)
        profile_image = ''
        profile_alt = ''
        if f.name == 'author-farrukh-abdullah.md':
            profile_image, profile_alt = AUTHOR_IMAGE, AUTHOR_NAME
        elif f.name == 'editor-moniqua-nelson-tunley.md':
            profile_image, profile_alt = REVIEWER_IMAGE, REVIEWER_NAME
        rendered = trust_t.render(
            **render_base_kwargs(f'{title} | Skinkpedia', desc, canon, 'website', SITE_URL + DEFAULT_OG_IMAGE, 'Representative skinks from Skinkpedia', schema),
            **dates, title=title, body_html=html, trust_label=trust_label(f.name), profile_image=profile_image, profile_alt=profile_alt
        )
        op = out_path(url)
        op.parent.mkdir(parents=True, exist_ok=True)
        op.write_text(rendered, encoding='utf-8')

    popular = []
    for pid, desc in [
        ('BT-001', 'Large terrestrial skinks with species- and locality-dependent care requirements.'),
        ('PET-001', 'A colorful burrowing species for keepers who value natural behavior.'),
        ('CR-001', 'A secretive tropical skink requiring careful humidity and minimal handling.')
    ]:
        p = pages[pid]
        popular.append({'title': p['title'].split(':')[0], 'url': p['url'], 'image': p['hero_image'], 'alt': p['hero_alt'], 'description': desc})

    home_desc = 'Evidence-informed guides to pet skink care, species identification, wild skinks, behavior, biology and natural history.'
    home_graph = base_graph() + [
        {'@type': 'WebPage', '@id': SITE_URL + '/#webpage', 'url': SITE_URL + '/',
         'name': 'Skinkpedia | Skink Care, Species Guides & Natural History', 'description': home_desc,
         'isPartOf': {'@id': SITE_URL + '/#website'}, 'about': {'@type': 'Taxon', 'name': 'Scincidae', 'alternateName': 'Skinks'}, 'inLanguage': 'en'}
    ]
    home_schema = json.dumps({'@context': 'https://schema.org', '@graph': home_graph}, ensure_ascii=False)
    home = env.get_template('home.html').render(
        **render_base_kwargs('Skinkpedia | Skink Care, Species Guides & Natural History', home_desc, SITE_URL + '/', 'website', SITE_URL + DEFAULT_OG_IMAGE, 'Representative skinks showing the diversity of the Scincidae family', home_schema),
        popular=popular
    )
    (DIST / 'index.html').write_text(home, encoding='utf-8')

    (DIST / '404.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found | Skinkpedia</title><meta name="robots" content="noindex,follow"><link rel="stylesheet" href="/assets/css/site.css"></head><body><main class="container trust-page"><h1>Page not found</h1><p>The page may have moved. Start from <a href="/">Skinkpedia</a>.</p></main></body></html>',
        encoding='utf-8'
    )

    urls = [SITE_URL + '/'] + [SITE_URL + p['url'] for p in pages.values()] + [SITE_URL + u for u in TRUST_ROUTES.values()]
    (DIST / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n', encoding='utf-8')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in sorted(set(urls))) + '</urlset>\n'
    (DIST / 'sitemap.xml').write_text(xml, encoding='utf-8')

    llms = '''# Skinkpedia\n\nSkinkpedia is an independent educational resource about skinks (family Scincidae), including pet care, species identification, wild skinks, biology and natural history.\n\n## Key sections\n- https://skinkpedia.online/skinks/ — skink family overview\n- https://skinkpedia.online/pet-skinks/ — pet skink comparison and ownership\n- https://skinkpedia.online/skink-care/ — husbandry framework\n- https://skinkpedia.online/wild-skinks/north-america/ — North American species and regional identification\n- https://skinkpedia.online/skink-biology/ — anatomy, classification and adaptations\n- https://skinkpedia.online/about/ — editorial team and site purpose\n- https://skinkpedia.online/editorial-policy/ — editorial standards\n- https://skinkpedia.online/sources-research-methodology/ — source methodology\n\nResearch and writing are handled by Farrukh Abdullah. Editorial review is handled by Moniqua Nelson-Tunley. Exact care values are species-specific. Health content is educational and does not replace veterinary care.\n'''
    (DIST / 'llms.txt').write_text(llms, encoding='utf-8')
    print('Built', len(pages), 'articles +', len(TRUST_ROUTES), 'trust pages + homepage')


if __name__ == '__main__':
    build()
