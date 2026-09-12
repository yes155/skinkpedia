# Skinkpedia Static Site

Static source for the Skinkpedia authority site.

## Local / Cloudflare build

From the repository root:

```bash
pip install -r requirements.txt
python build/build.py
python build/qa.py
python build/seo_qa.py
```

Build output: `dist/`

## Cloudflare Pages / Workers Assets

- **Framework preset:** None / static site
- **Build command:** `pip install -r requirements.txt && python build/build.py && python build/qa.py && python build/seo_qa.py`
- **Build output directory:** `dist`
- **Root directory:** repository root

The QA commands intentionally fail the deployment when hard content, asset, answer-first extraction, static information-gain resources, linking, schema, entity-graph, sitemap, or technical-SEO gates fail.

## Production domain

The current build config uses:

`https://skinkpedia.online`

If the final domain is different, update `SITE_URL` in `build/config.py` before the production build. Do not change the approved article slugs.

## Included

- 55 topical-map articles
- 55 mapped hero images
- 9 trust pages plus generated `/resources/` page
- homepage
- 404 page
- sitemap.xml with canonical URLs and `lastmod`
- robots.txt
- llms.txt
- entity-graph.json
- Article / Recipe / Breadcrumb / Organization / WebSite / WebPage / ProfilePage / Person / Taxon schema
- author and reviewer profile schema with images and sameAs links
- Taxon/entity registry with public knowledge-graph links where exact matches are available
- answer-first / At a glance extraction blocks
- information-gain sections on priority pages
- committed static PDF care sheets and checklists under `public/assets/downloads/`
- committed static CSV decision datasets under `public/assets/data/`
- a substrate volume estimator embedded in the supplies checklist
- automated general QA
- automated answer-first extraction validation
- automated technical SEO QA
- automated entity-graph enrichment and validation
- automated information-gain resource validation and page/block injection

## Final launch workflow

1. Build the static site.
2. Run general QA, including article answer-first extraction checks.
3. Prepare the resources page, comparison tables, care decision frameworks, PDF links, CSV dataset links, and priority resource blocks during SEO QA.
4. Enrich generated HTML with entity graph data during SEO QA.
5. Verify schema, canonicals, sitemap, robots.txt, llms.txt, `entity-graph.json`, dates, linked entities, extraction-ready summaries, static downloads, and information-gain resources.
6. Deploy the `dist/` output.
7. Submit `https://skinkpedia.online/sitemap.xml` in Google Search Console and Bing Webmaster Tools.
