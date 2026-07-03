# PieAtlas

PieAtlas is an open-source historical pie recipe archive focused on public-domain recipes through 1928.

Repository target: https://github.com/micklelow-source/PieAtlas

## Current phase

**Rev1-Rev4 are complete**: 10,000 public-domain recipe records across cookbooks, magazines, newspapers, community cookbooks, USDA bulletins, and extension publications.

## Roadmap

| Revision | Target | Scope |
|---|---:|---|
| Rev1 | 500 recipes | Major cookbook pie recipes through 1928 |
| Rev2 | 2,000 recipes | Cookbooks + magazines |
| Rev3 | 5,000 recipes | Add newspapers |
| Rev4 | 10,000+ recipes | Complete public-domain archive through 1928 |

## Data

- `data/recipes/recipes.csv`
- `data/recipes/recipes.json`
- `data/families/recipe_families.csv`
- `data/manifests/rev1_cookbook_targets.csv`
- `data/roadmap.json`

CSV files are the source of truth. Regenerate JSON exports after editing CSV:

```bash
python scripts/export/export_data.py
```

The exporter writes canonical JSON under `data/` and mirrors API-ready files to
`site/public/data/`.

## Start Rev1 harvesting

```bash
python scripts/harvest/harvest_gutenberg.py data/manifests/rev1_cookbook_targets.csv > data/recipes/rev1_gutenberg_candidates.csv
python scripts/normalize/promote_rev1_candidates.py
python scripts/export/export_data.py
python scripts/validate/validate_recipes.py
python -m unittest discover -s tests
```

## Continue Rev2 harvesting

```bash
python scripts/harvest/harvest_internet_archive_issues.py 25 data/magazines/rev2_issue_candidates.csv
python scripts/harvest/harvest_internet_archive_recipes.py 10 data/magazines/rev2_recipe_candidates.csv 30
```

Rev2 candidates are a review queue, not canonical recipes. Promote them only
after checking issue metadata, public-domain status, OCR quality, and duplicate
status against Rev1.

Complete Rev2 after harvesting:

```bash
python scripts/normalize/promote_rev2_candidates.py
python scripts/export/export_data.py
python scripts/validate/validate_recipes.py
```

Complete Rev3 and Rev4:

```bash
python scripts/normalize/promote_rev3_candidates.py
python scripts/normalize/promote_rev4_candidates.py
python scripts/export/export_data.py
python scripts/validate/validate_recipes.py
```

## Website

PieAtlas includes a static searchable website with full-text search, ingredient
filtering, recipe family views, a publication timeline, source pages, scan links,
and JSON API files.

Preview locally:

```bash
cd site
python -m http.server 8017 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8017/>.

Generated 2026-07-03.
