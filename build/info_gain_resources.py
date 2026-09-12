from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from bs4 import BeautifulSoup

SITE_URL = 'https://skinkpedia.online'
RESOURCE_DATE = '2026-09-12'
DOWNLOAD_DIR = Path('assets/downloads')
DATA_DIR = Path('assets/data')

PDF_FILES = [
    'skink-care-quick-start.pdf',
    'blue-tongue-skink-setup-checklist.pdf',
    'pet-skink-species-comparison-matrix.pdf',
    'skink-health-triage-sheet.pdf',
]
DATA_FILES = [
    'skink-species-decision-dataset.csv',
    'skink-care-decision-framework.csv',
]

CSS = '''
.information-gain-block{margin:38px 0;padding:24px;border:1px solid var(--border);border-radius:16px;background:#fff;box-shadow:0 12px 30px rgba(32,40,35,.06)}
.information-gain-block h2{margin-top:0}.resource-links{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:18px 0 8px;padding:0;list-style:none}.resource-links a{display:block;padding:12px 14px;border:1px solid var(--border);border-radius:12px;background:var(--ivory-50);font-weight:750;text-decoration:none}.mini-tool{margin-top:18px;padding:16px;border-radius:14px;background:#f3efe5}.mini-tool label{display:block;font-size:.9rem;font-weight:750;margin-top:8px}.mini-tool input{width:100%;max-width:260px;padding:9px;border:1px solid var(--border);border-radius:8px}.mini-tool output{display:block;margin-top:12px;font-weight:800;color:var(--forest-900)}
.resource-hub-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:26px 0}.resource-card{padding:20px;border:1px solid var(--border);border-radius:14px;background:#fff}.resource-card h2,.resource-card h3{margin-top:0}.resource-card ul{margin-bottom:0}.resource-note{padding:16px 18px;border-left:4px solid var(--forest-700);background:var(--success-bg);border-radius:0 12px 12px 0}.dataset-table td:first-child{font-weight:750;color:var(--forest-900)}
@media(max-width:760px){.resource-links,.resource-hub-grid{grid-template-columns:1fr}.information-gain-block{padding:18px}}
'''.strip()

HTML_BLOCKS = {
    'pet-skinks/index.html': ('pet-skink-comparison-resources', '''
<section class="information-gain-block" id="pet-skink-comparison-resources">
<h2>Pet skink comparison matrix</h2>
<p>This matrix separates keeper fit, enclosure style, visibility and handling expectations so a buyer does not choose a skink from appearance alone.</p>
<table><thead><tr><th>Species/group</th><th>Best fit</th><th>Main care focus</th><th>Avoid if</th></tr></thead><tbody>
<tr><td>Blue-tongued skinks</td><td>Prepared beginner to intermediate keeper</td><td>Large terrestrial space, diet variety, heat/UVB and locality-aware humidity</td><td>You cannot support long-term space, cost or species-specific humidity</td></tr>
<tr><td>Red-eyed crocodile skink</td><td>Observation-focused intermediate keeper</td><td>Humid cover, quiet enclosure and minimal handling</td><td>You want frequent interaction</td></tr>
<tr><td>Fire skink</td><td>Keeper who enjoys burrowing behavior</td><td>Deep substrate, humidity and secure hides</td><td>You need a constantly visible animal</td></tr>
<tr><td>Emerald tree skink</td><td>Active-display keeper with vertical space</td><td>Height, branches, escape prevention and social planning</td><td>You only have a short terrestrial tank</td></tr>
<tr><td>Sandfish skink</td><td>Specialist burrowing-interest keeper</td><td>Loose sand, heat gradient and dry setup control</td><td>You want a handling-focused pet</td></tr>
</tbody></table>
<ul class="resource-links"><li><a href="/assets/downloads/pet-skink-species-comparison-matrix.pdf">Download species comparison PDF</a></li><li><a href="/assets/data/skink-species-decision-dataset.csv">Download species decision dataset CSV</a></li><li><a href="/resources/">Open all Skinkpedia resources</a></li></ul>
</section>
'''),
    'skink-care/index.html': ('skink-care-decision-framework', '''
<section class="information-gain-block" id="skink-care-decision-framework">
<h2>Skink care decision framework</h2>
<p>Use this framework before applying any care number. The safest decision starts with species identity, then checks enclosure, heat, humidity, diet and health escalation as one system.</p>
<table><thead><tr><th>Decision area</th><th>Question</th><th>Safer action</th><th>Risk if ignored</th></tr></thead><tbody>
<tr><td>Species ID</td><td>Do you know the exact species or group?</td><td>Do not buy from a generic skink list until the species is known.</td><td>Wrong humidity, temperature, substrate or enclosure size.</td></tr>
<tr><td>Enclosure</td><td>Can the animal thermoregulate and hide?</td><td>Provide warm/cool zones, multiple hides and species-suitable substrate.</td><td>Stress, escape, overheating or poor feeding.</td></tr>
<tr><td>Humidity</td><td>Is moisture matched to species/locality?</td><td>Use the species range and track shed quality.</td><td>Respiratory or shedding problems.</td></tr>
<tr><td>Health triage</td><td>Are there breathing, injury or rapid weight-loss signs?</td><td>Treat as veterinary escalation, not web diagnosis.</td><td>Delayed care for serious illness.</td></tr>
</tbody></table>
<ul class="resource-links"><li><a href="/assets/downloads/skink-care-quick-start.pdf">Download skink care quick-start PDF</a></li><li><a href="/assets/data/skink-care-decision-framework.csv">Download care decision framework CSV</a></li><li><a href="/resources/">Open all Skinkpedia resources</a></li></ul>
</section>
'''),
    'skink-care/health/index.html': ('skink-health-triage-framework', '''
<section class="information-gain-block" id="skink-health-triage-framework">
<h2>Health triage checklist</h2>
<p>This checklist separates urgent signs from husbandry review signs. It is for escalation and record-keeping, not home diagnosis.</p>
<table><thead><tr><th>Sign</th><th>Check first</th><th>Escalate when</th></tr></thead><tbody>
<tr><td>Open-mouth breathing, wheezing, bubbles or severe lethargy</td><td>Temperature, ventilation, humidity and recent stress</td><td>Prompt reptile-veterinary contact</td></tr>
<tr><td>Swelling, tremors, soft jaw or poor limb use</td><td>Diet, UVB, heat and injury risk</td><td>Veterinary assessment rather than supplement guessing</td></tr>
<tr><td>Retained shed on toes or tail tip</td><td>Species humidity, hydration and rough surfaces</td><td>Tight, dark, damaged or persistent tissue</td></tr>
<tr><td>Appetite loss</td><td>Heat, recent changes, food type and weight trend</td><td>Persistent loss with weight decline or weakness</td></tr>
</tbody></table>
<ul class="resource-links"><li><a href="/assets/downloads/skink-health-triage-sheet.pdf">Download health triage PDF</a></li><li><a href="/resources/">Open all Skinkpedia resources</a></li></ul>
</section>
'''),
    'skink-care/supplies-checklist/index.html': ('skink-printable-checklists-and-tool', '''
<section class="information-gain-block" id="skink-printable-checklists-and-tool">
<h2>Printable checklists, datasets and setup tool</h2>
<p>These resources turn the supplies guide into a practical pre-purchase workflow: compare the species, estimate substrate volume, then print the setup sheet before buying the animal.</p>
<ul class="resource-links"><li><a href="/assets/downloads/skink-care-quick-start.pdf">Skink care quick-start PDF</a></li><li><a href="/assets/downloads/blue-tongue-skink-setup-checklist.pdf">Blue-tongue setup checklist PDF</a></li><li><a href="/assets/downloads/pet-skink-species-comparison-matrix.pdf">Pet skink comparison matrix PDF</a></li><li><a href="/assets/data/skink-species-decision-dataset.csv">Species decision dataset CSV</a></li><li><a href="/resources/">Open all Skinkpedia resources</a></li></ul>
<div class="mini-tool" data-tool="substrate-estimator"><h3>Substrate volume estimator</h3><p>Enter inside floor length, width and planned substrate depth. The result is an estimate only; bag yield varies by material and compaction.</p><label>Length in inches <input id="substrate-length" type="number" min="0" step="0.1"></label><label>Width in inches <input id="substrate-width" type="number" min="0" step="0.1"></label><label>Depth in inches <input id="substrate-depth" type="number" min="0" step="0.1"></label><output id="substrate-result">Enter values to estimate volume.</output></div>
</section>
'''),
    'pet-skinks/blue-tongue-skink/types/index.html': ('blue-tongue-type-comparison-dataset', '''
<section class="information-gain-block" id="blue-tongue-type-comparison-dataset">
<h2>Blue-tongue type comparison dataset</h2>
<p>Use this table to keep taxonomy, trade labels and husbandry caution separate. A locality or morph label is not the same as a formally recognized species.</p>
<table><thead><tr><th>Name used by keepers</th><th>Taxonomic level</th><th>Care implication</th><th>Buyer check</th></tr></thead><tbody>
<tr><td>Northern blue-tongue</td><td>Subspecies of <em>Tiliqua scincoides</em></td><td>Common captive-care sources exist, but values still need measured setup verification.</td><td>Ask for captive-bred status and parentage/source history.</td></tr>
<tr><td>Eastern blue-tongue</td><td>Subspecies of <em>Tiliqua scincoides</em></td><td>Do not copy Indonesian humidity assumptions into an Australian form.</td><td>Confirm subspecies rather than relying on appearance alone.</td></tr>
<tr><td>Merauke</td><td>Usually associated with <em>Tiliqua gigas evanescens</em></td><td>Humidity and origin discussion differs from many Australian blue-tongues.</td><td>Ask for origin documentation and health/acclimation history.</td></tr>
<tr><td>Halmahera</td><td>Locality/trade label</td><td>Do not treat the name as a separate recognized species.</td><td>Verify what the seller means by the label.</td></tr>
<tr><td>Shingleback</td><td>Distinct species, <em>Tiliqua rugosa</em></td><td>Social, legal and sourcing context need dedicated review.</td><td>Confirm legality and avoid generic blue-tongue assumptions.</td></tr>
</tbody></table>
<ul class="resource-links"><li><a href="/assets/downloads/blue-tongue-skink-setup-checklist.pdf">Download blue-tongue setup checklist PDF</a></li><li><a href="/assets/data/skink-species-decision-dataset.csv">Download comparison dataset CSV</a></li><li><a href="/resources/">Open all Skinkpedia resources</a></li></ul>
</section>
'''),
}

SUBSTRATE_SCRIPT = '''
<script id="substrate-estimator-script">
(function(){
  const ids=['substrate-length','substrate-width','substrate-depth'];
  const out=document.getElementById('substrate-result');
  if(!out) return;
  function calc(){
    const vals=ids.map(id=>parseFloat((document.getElementById(id)||{}).value));
    if(vals.some(v=>!isFinite(v)||v<=0)){out.textContent='Enter values to estimate volume.';return;}
    const cubicIn=vals[0]*vals[1]*vals[2];
    const liters=cubicIn*0.0163871;
    out.textContent='Estimated substrate volume: '+cubicIn.toFixed(0)+' cubic inches / '+liters.toFixed(1)+' liters.';
  }
  ids.forEach(id=>{const el=document.getElementById(id); if(el) el.addEventListener('input',calc);});
})();
</script>
'''

RESOURCE_TITLE = 'Resources: Printable Skink Care Sheets, Checklists & Datasets'
RESOURCE_DESCRIPTION = "Download Skinkpedia's printable skink care sheets, species comparison PDFs, health triage checklist, CSV datasets and setup tools."
RESOURCE_MAIN_HTML = '''
<div class="container trust-page resources-page">
  <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><span aria-current="page">Resources</span></nav>
  <article class="reading-width">
    <h1>Skinkpedia Resources</h1>
    <p class="byline article-meta-line" aria-label="Page credits and dates">By <a href="/authors/farrukh-abdullah/">Farrukh Abdullah</a> · Reviewed by <a href="/editors/moniqua-nelson-tunley/">Moniqua Nelson-Tunley</a> · Published <time datetime="2026-09-12">September 12, 2026</time> · Updated <time datetime="2026-09-12">September 12, 2026</time></p>
    <p class="resource-note">Use these printable sheets, comparison matrices, decision datasets and setup tools alongside the full Skinkpedia articles. They are planning aids, not substitutes for species-specific husbandry or veterinary advice.</p>
    <div class="resource-hub-grid">
      <section class="resource-card"><h2>Printable PDFs</h2><ul><li><a href="/assets/downloads/skink-care-quick-start.pdf">Skink care quick-start sheet</a></li><li><a href="/assets/downloads/blue-tongue-skink-setup-checklist.pdf">Blue-tongue skink setup checklist</a></li><li><a href="/assets/downloads/pet-skink-species-comparison-matrix.pdf">Pet skink species comparison matrix</a></li><li><a href="/assets/downloads/skink-health-triage-sheet.pdf">Skink health triage sheet</a></li></ul></section>
      <section class="resource-card"><h2>CSV datasets</h2><ul><li><a href="/assets/data/skink-species-decision-dataset.csv">Skink species decision dataset</a></li><li><a href="/assets/data/skink-care-decision-framework.csv">Skink care decision framework dataset</a></li><li><a href="/assets/data/skinkpedia-resource-manifest.json">Resource manifest</a></li></ul></section>
      <section class="resource-card"><h2>Comparison frameworks</h2><ul><li><a href="/pet-skinks/#pet-skink-comparison-resources">Pet skink comparison matrix</a></li><li><a href="/pet-skinks/blue-tongue-skink/types/#blue-tongue-type-comparison-dataset">Blue-tongue type comparison dataset</a></li><li><a href="/skink-care/#skink-care-decision-framework">Skink care decision framework</a></li></ul></section>
      <section class="resource-card"><h2>Tools and triage aids</h2><ul><li><a href="/skink-care/supplies-checklist/#skink-printable-checklists-and-tool">Substrate volume estimator</a></li><li><a href="/skink-care/health/#skink-health-triage-framework">Health triage checklist</a></li><li><a href="/skink-care/supplies-checklist/">Supplies checklist guide</a></li></ul></section>
    </div>
    <h2>How to use these resources</h2>
    <table class="dataset-table"><thead><tr><th>Resource type</th><th>Best use</th><th>Important limit</th></tr></thead><tbody><tr><td>PDF sheets</td><td>Print before setup, buying, or a veterinary visit.</td><td>They summarize planning steps but do not replace the full species guide.</td></tr><tr><td>CSV datasets</td><td>Compare keeper fit, diet profile, enclosure emphasis and care decisions.</td><td>They are simplified planning data, not exhaustive biological datasets.</td></tr><tr><td>Substrate estimator</td><td>Estimate substrate volume from enclosure floor area and planned depth.</td><td>Bag yield changes with material, moisture and compaction.</td></tr></tbody></table>
  </article>
</div>
'''


def ensure_css(soup: BeautifulSoup) -> None:
    head = soup.find('head')
    if not head or soup.find('link', attrs={'href': '/assets/css/information-gain.css?v=1'}):
        return
    link = soup.new_tag('link', rel='stylesheet', href='/assets/css/information-gain.css?v=1')
    head.append(link)


def inject_toc(soup: BeautifulSoup, block_id: str, label: str) -> None:
    toc = soup.select_one('.toc ol')
    if not toc or toc.find('a', href='#' + block_id):
        return
    li = soup.new_tag('li')
    li['class'] = 'toc-level-2'
    a = soup.new_tag('a', href='#' + block_id)
    a.string = label
    li.append(a)
    toc.append(li)


def inject_block(html_path: Path, block_id: str, html: str) -> bool:
    if not html_path.exists():
        return False
    soup = BeautifulSoup(html_path.read_text(encoding='utf-8'), 'html.parser')
    if soup.find(id=block_id):
        return True
    body = soup.select_one('.article-body')
    if not body:
        return False
    fragment = BeautifulSoup(html, 'html.parser')
    target = None
    for h in body.find_all(['h2', 'h3']):
        if h.get_text(' ', strip=True).lower().startswith('frequently asked questions'):
            target = h
            break
    if target:
        for child in list(fragment.contents):
            target.insert_before(child)
    else:
        for child in list(fragment.contents):
            body.append(child)
    ensure_css(soup)
    heading = soup.find(id=block_id).find(['h2', 'h3']) if soup.find(id=block_id) else None
    inject_toc(soup, block_id, heading.get_text(' ', strip=True) if heading else 'Resources')
    if block_id == 'skink-printable-checklists-and-tool' and not soup.find(id='substrate-estimator-script'):
        script = BeautifulSoup(SUBSTRATE_SCRIPT, 'html.parser')
        if soup.body:
            soup.body.append(script)
    html_path.write_text(str(soup), encoding='utf-8')
    return True


def set_meta(soup: BeautifulSoup, attr: str, key: str, value: str) -> None:
    tag = soup.find('meta', attrs={attr: key})
    if tag:
        tag['content'] = value


def resources_schema() -> dict:
    canon = SITE_URL + '/resources/'
    return {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'Organization', '@id': SITE_URL + '/#organization', 'name': 'Skinkpedia', 'url': SITE_URL + '/', 'description': 'Independent educational guides to skink care, identification and natural history.'},
            {'@type': 'WebSite', '@id': SITE_URL + '/#website', 'url': SITE_URL + '/', 'name': 'Skinkpedia', 'publisher': {'@id': SITE_URL + '/#organization'}, 'inLanguage': 'en'},
            {'@type': 'WebPage', '@id': canon + '#webpage', 'url': canon, 'name': RESOURCE_TITLE, 'description': RESOURCE_DESCRIPTION, 'isPartOf': {'@id': SITE_URL + '/#website'}, 'breadcrumb': {'@id': canon + '#breadcrumb'}, 'datePublished': RESOURCE_DATE, 'dateModified': RESOURCE_DATE, 'inLanguage': 'en', 'about': {'@type': 'Thing', 'name': 'Skink care resources'}},
            {'@type': 'BreadcrumbList', '@id': canon + '#breadcrumb', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE_URL + '/'}, {'@type': 'ListItem', 'position': 2, 'name': 'Resources', 'item': canon}]},
        ],
    }


def create_resources_page(dist: Path) -> bool:
    source = dist / 'index.html'
    if not source.exists():
        return False
    soup = BeautifulSoup(source.read_text(encoding='utf-8'), 'html.parser')
    if soup.title:
        soup.title.string = RESOURCE_TITLE + ' | Skinkpedia'
    canon = SITE_URL + '/resources/'
    desc = RESOURCE_DESCRIPTION
    canonical = soup.find('link', rel='canonical')
    if canonical:
        canonical['href'] = canon
    set_meta(soup, 'name', 'description', desc)
    set_meta(soup, 'property', 'og:type', 'website')
    set_meta(soup, 'property', 'og:title', RESOURCE_TITLE + ' | Skinkpedia')
    set_meta(soup, 'property', 'og:description', desc)
    set_meta(soup, 'property', 'og:url', canon)
    set_meta(soup, 'name', 'twitter:title', RESOURCE_TITLE + ' | Skinkpedia')
    set_meta(soup, 'name', 'twitter:description', desc)
    script = soup.find('script', attrs={'type': 'application/ld+json'})
    if script:
        script.string = json.dumps(resources_schema(), ensure_ascii=False)
    main = soup.find('main', id='main-content')
    if not main:
        return False
    main.clear()
    fragment = BeautifulSoup(RESOURCE_MAIN_HTML, 'html.parser')
    for child in list(fragment.contents):
        main.append(child)
    ensure_css(soup)
    out = dist / 'resources' / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(str(soup), encoding='utf-8')
    return True


def update_sitemap_for_resources(dist: Path) -> None:
    sm = dist / 'sitemap.xml'
    if not sm.exists():
        return
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    tree = ET.parse(sm)
    root = tree.getroot()
    locs = {el.text for el in root.findall(f'{{{ns}}}url/{{{ns}}}loc')}
    target = SITE_URL + '/resources/'
    if target not in locs:
        url = ET.SubElement(root, f'{{{ns}}}url')
        loc = ET.SubElement(url, f'{{{ns}}}loc')
        loc.text = target
        lastmod = ET.SubElement(url, f'{{{ns}}}lastmod')
        lastmod.text = RESOURCE_DATE
    tree.write(sm, encoding='utf-8', xml_declaration=True)


def validate_static_resources(dist: Path) -> list[str]:
    missing = []
    for filename in PDF_FILES:
        path = dist / DOWNLOAD_DIR / filename
        if not path.exists() or path.read_bytes()[:4] != b'%PDF':
            missing.append(str(DOWNLOAD_DIR / filename))
    for filename in DATA_FILES:
        path = dist / DATA_DIR / filename
        if not path.exists() or path.stat().st_size < 100:
            missing.append(str(DATA_DIR / filename))
    return missing


def apply_info_gain_resources(dist: Path | None = None) -> dict:
    dist = Path(dist) if dist else Path(__file__).resolve().parents[1] / 'dist'
    (dist / 'assets/css').mkdir(parents=True, exist_ok=True)
    (dist / 'assets/css/information-gain.css').write_text(CSS + '\n', encoding='utf-8')

    missing_resources = validate_static_resources(dist)
    if missing_resources:
        raise FileNotFoundError('missing or invalid static information-gain resources: ' + ', '.join(missing_resources))

    injected = []
    missing_pages = []
    for rel, (block_id, html) in HTML_BLOCKS.items():
        if inject_block(dist / rel, block_id, html):
            injected.append(rel)
        else:
            missing_pages.append(rel)

    resources_page_created = create_resources_page(dist)
    update_sitemap_for_resources(dist)

    manifest = {
        'pdfs': sorted(PDF_FILES),
        'datasets': sorted(DATA_FILES),
        'static_resources': [str(DOWNLOAD_DIR / f) for f in sorted(PDF_FILES)] + [str(DATA_DIR / f) for f in sorted(DATA_FILES)],
        'resource_page': '/resources/' if resources_page_created else None,
        'injected_pages': injected,
        'missing_pages': missing_pages,
    }
    (dist / DATA_DIR).mkdir(parents=True, exist_ok=True)
    (dist / DATA_DIR / 'skinkpedia-resource-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Information gain resources validated', len(PDF_FILES), 'PDFs,', len(DATA_FILES), 'datasets,', len(injected), 'pages enriched, resources page:', bool(resources_page_created))
    return manifest


if __name__ == '__main__':
    apply_info_gain_resources()
