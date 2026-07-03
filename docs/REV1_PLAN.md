# Rev1 Plan

Status: complete.

Target: 500 source-text-verified recipe records.

## Scope

Major public-domain cookbook pie, tart, pastry, mince, and related pie-family
recipes published through 1928.

## Starting workflow

```bash
python scripts/harvest/harvest_gutenberg.py data/manifests/rev1_cookbook_targets.csv > data/recipes/rev1_gutenberg_candidates.csv
python scripts/normalize/promote_rev1_candidates.py
python scripts/export/export_data.py
python scripts/validate/validate_recipes.py
```

## Review rule

Candidates are not final recipes. Promote only after checking source text,
rights, citation URL, candidate context, and OCR quality. Rev1 records preserve
their harvested source context in `original_text` for future page-level citation
review.
