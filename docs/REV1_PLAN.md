# Rev1 Plan

Target: 500 verified recipe records.

## Scope

All major public-domain cookbook pie recipes published through 1928.

## Starting workflow

```bash
python scripts/harvest/harvest_gutenberg.py data/manifests/rev1_cookbook_targets.csv > data/recipes/rev1_gutenberg_candidates.csv
python scripts/normalize/assign_recipe_families.py data/recipes/recipes.csv data/families/recipe_families.csv > /tmp/recipes_with_families.csv
python scripts/validate/validate_recipes.py
```

## Review rule

Candidates are not final recipes. Promote only after checking recipe boundaries, rights, citation, and OCR quality.
