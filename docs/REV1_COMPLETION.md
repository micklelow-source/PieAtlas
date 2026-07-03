# Rev1 Completion

Rev1 is complete at 500 source-text-verified recipe records.

## Completed deliverables

- `data/recipes/recipes.csv`
- `data/recipes/recipes.json`
- `data/families/recipe_families.csv`
- `data/families/recipe_families.json`
- `data/manifests/rev1_cookbook_targets.csv`
- `data/recipes/rev1_gutenberg_candidates.csv`
- `scripts/harvest/harvest_gutenberg.py`
- `scripts/normalize/promote_rev1_candidates.py`
- `scripts/export/export_data.py`
- `scripts/validate/validate_recipes.py`
- `site/` searchable static website
- `site/public/data/` JSON API files

## Verification standard

Rev1 records use `verification_status=rev1_source_text_verified`.
Each promoted row is derived from a public-domain source-text harvest, includes
the original harvested context, and keeps the source URL for citation review.

## Remaining post-Rev1 work

Rev2 should add page-level citation extraction, magazine sources, richer
ingredient parsing, regional metadata, and human review queues for exact print
page references.
