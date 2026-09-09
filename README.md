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

## Cloudflare Pages

- **Framework preset:** None / static site
- **Build command:** `pip install -r requirements.txt && python build/build.py && python build/qa.py && python build/seo_qa.py`
- **Build output directory:** `dist`
- **Root directory:** repository root

The QA commands intentionally fail the deployment when hard content, asset, linking or technical-SEO gates fail.

## Production domain

The current build config uses:

`https://skinkpedia.online`

If the final domain is different, update `SITE_URL` in `build/config.py` before the production build. Do not change the approved article slugs.

## Included

- 53 topical-map articles
- 53 mapped hero images
- 7 trust pages
- homepage
- 404 page
- sitemap.xml
- robots.txt
- llms.txt
- Article / Recipe / Breadcrumb / Organization / Person schema
- automated general QA
- automated technical SEO QA
