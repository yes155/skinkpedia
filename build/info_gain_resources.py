from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DOWNLOAD_DIR = Path('assets/downloads')
DATA_DIR = Path('assets/data')

SPECIES_DATASET = [
    ['species_group','example_taxon','typical_keeper_fit','visibility','handling_fit','enclosure_emphasis','humidity_profile','diet_profile','primary_risk','choose_if','avoid_if'],
    ['Blue-tongued skinks','Tiliqua spp.','Beginner-intermediate with preparation','High','Moderate to good with captive-bred individuals','Large terrestrial floor space with heat and UVB','Locality dependent','Omnivorous varied diet','Assuming all blue-tongues use one humidity profile','You want a visible terrestrial skink with long-term commitment','You cannot provide space, cost or species-specific humidity'],
    ['Red-eyed crocodile skink','Tribolonotus gracilis','Intermediate','Low to moderate','Low','Humid planted enclosure with heavy cover','Higher humidity','Invertebrate-focused','Overhandling and exposed dry setup','You want a display animal and can keep it quiet','You want frequent handling'],
    ['Fire skink','Lepidothyris fernandi','Intermediate','Moderate','Low to moderate','Deep substrate with secure hides and humidity','Moderate to higher humidity','Invertebrate-focused with variety','Dry shallow enclosure','You value burrowing behavior and color','You need a constantly visible pet'],
    ['Emerald tree skink','Lamprolepis smaragdina','Intermediate-advanced','High','Limited; escape risk','Vertical enclosure with branches, plants and secure ventilation','Moderate to higher humidity','Invertebrate plus plant/fruit items where species guidance supports them','Escape and social setup mistakes','You want active arboreal behavior','You only have a short terrestrial tank'],
    ['Sandfish skink','Scincus scincus','Intermediate specialist','Low','Low','Desert-style sand burrowing setup with heat gradient','Lower humidity','Small invertebrates','Wrong substrate or damp setup','You want specialist burrowing natural history','You want a handling-focused pet'],
    ['Shingleback skink','Tiliqua rugosa','Intermediate; legality/origin sensitive','High','Moderate with appropriate individual','Terrestrial dry setup with strong species-specific constraints','Drier profile','More herbivorous tendency than many blue-tongues','Illegal/unsuitable sourcing or generic blue-tongue care','You can verify legality and source','You cannot confirm source or legal status'],
]

CARE_FRAMEWORK = [
    ['decision_area','question','safe_default','next_action','risk_if_ignored'],
    ['Species ID','Do you know the exact species or species group?','Do not buy equipment from a generic skink list until the species is known.','Use the species guide and confirm legal/source status.','Wrong humidity, temperature, substrate or enclosure size.'],
    ['Enclosure','Can the animal thermoregulate and hide?','Provide warm/cool zones, multiple hides, secure lid and species-suitable substrate.','Test for several days before arrival.','Stress, escape, overheating or chronic poor feeding.'],
    ['Heating and UVB','Are temperatures measured at basking surface and cool end?','Use thermostat control and measured distances for heat and UVB.','Log readings before feeding/handling decisions.','Burns, metabolic issues or poor digestion.'],
    ['Humidity','Is humidity matched to locality/species rather than family name?','Use the species-specific range and provide shed support.','Track shed quality and adjust gradually.','Respiratory or shedding problems.'],
    ['Diet','Is the diet appropriate for age and species ecology?','Offer a varied diet suited to omnivore, insectivore or herbivore tendencies.','Record foods accepted and weight trend.','Obesity, malnutrition or feeding refusal.'],
    ['Health triage','Is there breathing trouble, injury, severe lethargy or rapid weight loss?','Treat as a veterinary escalation, not a web-diagnosis problem.','Contact an experienced reptile veterinarian.','Delayed care for serious illness.'],
]

PDF_SHEETS = {
    'skink-care-quick-start.pdf': {
        'title': 'Skink Care Quick-Start Sheet',
        'intro': 'A one-page launch checklist for setting up skink care without treating every skink species as the same animal.',
        'sections': [
            ('Species-first setup rule', [
                ['Decision','Safe launch action','Why it matters'],
                ['Identify the species before buying equipment.','Match enclosure size, humidity, substrate and basking setup to the exact species guide.','Blue-tongued, crocodile, fire, sandfish and emerald tree skinks do not use the same care profile.'],
                ['Choose captive-bred animals where legal and available.','Ask for feeding records, health history and origin details before purchase.','This reduces welfare risk and avoids illegal or unsustainable wildlife trade.'],
                ['Build the enclosure before the animal arrives.','Test heat, UVB, hiding places and humidity for several days first.','Most early health problems start from rushed setup decisions.'],
            ]),
            ('Daily and weekly checks', [
                ['Frequency','Check','Action'],
                ['Daily','Temperature gradient, water, appetite, behavior and secure lid.','Correct unsafe readings before handling or feeding changes.'],
                ['2-3 times weekly','Substrate moisture, shedding progress, waste and hides.','Spot clean and adjust humidity within the species-appropriate range.'],
                ['Weekly','Deep spot-clean, weigh if relevant and review feeding response.','Record unusual signs instead of guessing from memory.'],
            ]),
        ],
    },
    'blue-tongue-skink-setup-checklist.pdf': {
        'title': 'Blue-Tongue Skink Setup Checklist',
        'intro': 'A practical shopping and setup sheet for blue-tongued skinks, with a species/locality warning for humidity and seasonal behavior.',
        'sections': [
            ('Before purchase', [
                ['Item','Ready?','Notes'],
                ['Species/locality identified','Yes / No','Northern, Eastern, Indonesian, Merauke and shingleback-type skinks can differ in humidity, origin and behavior.'],
                ['Captive-bred source checked','Yes / No','Ask for feeding history, age, weight, shedding history and recent photos.'],
                ['Veterinary option found','Yes / No','Find an exotic/reptile veterinarian before an urgent problem appears.'],
            ]),
            ('Core equipment', [
                ['System','Minimum function','Mistake to avoid'],
                ['Enclosure','Secure terrestrial enclosure with enough floor area and hides.','Buying the animal first and upgrading later.'],
                ['Heating','Thermostat-controlled gradient with basking end and cool retreat.','Heating the whole enclosure evenly.'],
                ['Lighting/UVB','Species-appropriate UVB and photoperiod.','Using UVB without measuring distance or obstruction.'],
                ['Substrate','Safe, clean substrate suited to humidity and digging needs.','Loose risky substrate for a weak, tiny or newly arrived skink.'],
            ]),
        ],
    },
    'pet-skink-species-comparison-matrix.pdf': {
        'title': 'Pet Skink Species Comparison Matrix',
        'intro': 'A decision matrix for matching common pet skink groups to keeper goals, risk tolerance and enclosure style.',
        'sections': [
            ('Comparison matrix', [
                ['Species/group','Keeper fit','Main care focus','Choose if','Avoid if'],
                ['Blue-tongued skinks','Beginner to intermediate with preparation.','Floor space, diet variety, heat/UVB and locality-aware humidity.','You want a visible terrestrial skink.','You cannot provide space, cost or species-specific humidity.'],
                ['Red-eyed crocodile skink','Intermediate.','Humidity, cover, low handling and quiet enclosure.','You want a display animal.','You want frequent handling.'],
                ['Fire skink','Intermediate.','Deep substrate, humidity and secure hides.','You want burrowing behavior and color.','You need a constantly visible pet.'],
                ['Emerald tree skink','Intermediate to advanced.','Vertical space, social planning, humidity and escape prevention.','You want active arboreal behavior.','You only have a short terrestrial enclosure.'],
                ['Sandfish skink','Intermediate specialist.','Loose sand, heat gradient and low-humidity desert setup.','You want burrowing behavior.','You want a handling-focused pet.'],
            ]),
        ],
    },
    'skink-health-triage-sheet.pdf': {
        'title': 'Skink Health Triage Sheet',
        'intro': 'A cautious owner-facing checklist that separates emergency signs from husbandry review signs. It is not a diagnosis sheet.',
        'sections': [
            ('Urgent signs', [
                ['Sign','Possible concern','Action'],
                ['Open-mouth breathing, wheezing, bubbles or severe lethargy.','Respiratory or systemic illness.','Contact an experienced reptile veterinarian promptly.'],
                ['Swollen limbs, tremors, soft jaw or inability to use limbs.','Metabolic, injury or infection concerns.','Seek veterinary assessment.'],
                ['Bleeding, burns, prolapse or severe bite wounds.','Trauma or tissue damage.','Treat as urgent.'],
                ['Rapid weight loss or long refusal to eat with weakness.','Illness, parasites, stress or husbandry failure.','Check setup and arrange vet help.'],
            ]),
            ('Owner log', [
                ['Record','Why'],
                ['Weight trend','More useful than guessing body condition from one photo.'],
                ['Temperature and humidity readings','Most care corrections start with measured environment.'],
                ['Food offered/eaten','Helps separate preference, stress and illness patterns.'],
                ['Photos of shed, stool or lesion','Useful for a veterinarian and for tracking change over time.'],
            ]),
        ],
    },
}

CSS = '''
.information-gain-block{margin:38px 0;padding:24px;border:1px solid var(--border);border-radius:16px;background:#fff;box-shadow:0 12px 30px rgba(32,40,35,.06)}
.information-gain-block h2{margin-top:0}.resource-links{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:18px 0 8px;padding:0;list-style:none}.resource-links a{display:block;padding:12px 14px;border:1px solid var(--border);border-radius:12px;background:var(--ivory-50);font-weight:750;text-decoration:none}.mini-tool{margin-top:18px;padding:16px;border-radius:14px;background:#f3efe5}.mini-tool label{display:block;font-size:.9rem;font-weight:750;margin-top:8px}.mini-tool input{width:100%;max-width:260px;padding:9px;border:1px solid var(--border);border-radius:8px}.mini-tool output{display:block;margin-top:12px;font-weight:800;color:var(--forest-900)}
@media(max-width:640px){.resource-links{grid-template-columns:1fr}.information-gain-block{padding:18px}}
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
<ul class="resource-links"><li><a href="/assets/downloads/pet-skink-species-comparison-matrix.pdf">Download species comparison PDF</a></li><li><a href="/assets/data/skink-species-decision-dataset.csv">Download species decision dataset CSV</a></li></ul>
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
<ul class="resource-links"><li><a href="/assets/downloads/skink-care-quick-start.pdf">Download skink care quick-start PDF</a></li><li><a href="/assets/data/skink-care-decision-framework.csv">Download care decision framework CSV</a></li></ul>
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
<ul class="resource-links"><li><a href="/assets/downloads/skink-health-triage-sheet.pdf">Download health triage PDF</a></li></ul>
</section>
'''),
    'skink-care/supplies-checklist/index.html': ('skink-printable-checklists-and-tool', '''
<section class="information-gain-block" id="skink-printable-checklists-and-tool">
<h2>Printable checklists, datasets and setup tool</h2>
<p>These resources turn the supplies guide into a practical pre-purchase workflow: compare the species, estimate substrate volume, then print the setup sheet before buying the animal.</p>
<ul class="resource-links"><li><a href="/assets/downloads/skink-care-quick-start.pdf">Skink care quick-start PDF</a></li><li><a href="/assets/downloads/blue-tongue-skink-setup-checklist.pdf">Blue-tongue setup checklist PDF</a></li><li><a href="/assets/downloads/pet-skink-species-comparison-matrix.pdf">Pet skink comparison matrix PDF</a></li><li><a href="/assets/data/skink-species-decision-dataset.csv">Species decision dataset CSV</a></li></ul>
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
<ul class="resource-links"><li><a href="/assets/downloads/blue-tongue-skink-setup-checklist.pdf">Download blue-tongue setup checklist PDF</a></li><li><a href="/assets/data/skink-species-decision-dataset.csv">Download comparison dataset CSV</a></li></ul>
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


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(rows)


def paragraph(text: str, style_name: str, styles):
    return Paragraph(str(text), styles[style_name])


def make_table(rows, styles):
    wrapped = [[paragraph(cell, 'Header' if r == 0 else 'Small', styles) for cell in row] for r, row in enumerate(rows)]
    widths = [(7.4 * inch) / len(rows[0]) for _ in rows[0]]
    table = Table(wrapped, colWidths=widths, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#173D32')),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D9DED8')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAF8F2')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def write_pdf(path: Path, spec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title2', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#173D32'), alignment=0))
    styles.add(ParagraphStyle(name='H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=colors.HexColor('#28604E'), spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='Body2', parent=styles['BodyText'], fontSize=9.3, leading=12, textColor=colors.HexColor('#202823')))
    styles.add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontSize=8, leading=10, textColor=colors.HexColor('#5C665F')))
    styles.add(ParagraphStyle(name='Header', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=7.6, leading=9.2, textColor=colors.white))
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=0.55*inch, leftMargin=0.55*inch, topMargin=0.52*inch, bottomMargin=0.5*inch)
    story = [paragraph('Skinkpedia', 'Small', styles), paragraph(spec['title'], 'Title2', styles), paragraph(spec['intro'], 'Body2', styles), Spacer(1, 8)]
    for heading, rows in spec['sections']:
        story.append(paragraph(heading, 'H2', styles))
        story.append(make_table(rows, styles))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 10))
    story.append(paragraph('Educational use only. Exact temperature, humidity, diet and enclosure values depend on species, age, origin and health status. Use the full Skinkpedia species guide and consult an experienced reptile veterinarian for illness or emergency signs. skinkpedia.online', 'Small', styles))
    doc.build(story)


def ensure_css(soup: BeautifulSoup) -> None:
    head = soup.find('head')
    if not head or soup.find('link', attrs={'href': '/assets/css/information-gain.css'}):
        return
    link = soup.new_tag('link', rel='stylesheet', href='/assets/css/information-gain.css')
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
    label = soup.find(id=block_id).find(['h2', 'h3']).get_text(' ', strip=True) if soup.find(id=block_id) else 'Resources'
    inject_toc(soup, block_id, label)
    if block_id == 'skink-printable-checklists-and-tool' and not soup.find(id='substrate-estimator-script'):
        script = BeautifulSoup(SUBSTRATE_SCRIPT, 'html.parser')
        if soup.body:
            soup.body.append(script)
    html_path.write_text(str(soup), encoding='utf-8')
    return True


def apply_info_gain_resources(dist: Path | None = None) -> dict:
    dist = Path(dist) if dist else Path(__file__).resolve().parents[1] / 'dist'
    (dist / DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    (dist / DATA_DIR).mkdir(parents=True, exist_ok=True)
    (dist / 'assets/css').mkdir(parents=True, exist_ok=True)
    (dist / 'assets/css/information-gain.css').write_text(CSS + '\n', encoding='utf-8')

    write_csv(dist / DATA_DIR / 'skink-species-decision-dataset.csv', SPECIES_DATASET)
    write_csv(dist / DATA_DIR / 'skink-care-decision-framework.csv', CARE_FRAMEWORK)
    for filename, spec in PDF_SHEETS.items():
        write_pdf(dist / DOWNLOAD_DIR / filename, spec)

    injected = []
    missing = []
    for rel, (block_id, html) in HTML_BLOCKS.items():
        if inject_block(dist / rel, block_id, html):
            injected.append(rel)
        else:
            missing.append(rel)

    manifest = {
        'pdfs': sorted(PDF_SHEETS.keys()),
        'datasets': ['skink-care-decision-framework.csv', 'skink-species-decision-dataset.csv'],
        'injected_pages': injected,
        'missing_pages': missing,
    }
    (dist / DATA_DIR / 'skinkpedia-resource-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Information gain resources generated', len(PDF_SHEETS), 'PDFs,', len(injected), 'pages enriched')
    return manifest


if __name__ == '__main__':
    apply_info_gain_resources()
