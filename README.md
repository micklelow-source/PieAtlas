# PieAtlas

PieAtlas is an open-source historical pie recipe archive focused on public-domain recipes through 1928.

Repository target: https://github.com/micklelow-source/PieAtlas

## Current phase

**Rev1 is in progress**: 500 verified recipes from major public-domain cookbooks.

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

## Start Rev1 harvesting

```bash
python scripts/harvest/harvest_gutenberg.py data/manifests/rev1_cookbook_targets.csv > data/recipes/rev1_gutenberg_candidates.csv
python scripts/validate/validate_recipes.py
```

## Website data

The folder `site/public/data/` mirrors JSON data for a static website.

Generated 2026-07-03.
