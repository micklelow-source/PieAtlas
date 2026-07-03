# Rev2 Completion

Rev2 is complete at 2,000 source-text-verified recipe records.

## Completed deliverables

- 500 Rev1 cookbook records retained
- 1,500 Rev2 magazine records promoted
- `data/magazines/rev2_issue_candidates.csv`
- `data/magazines/rev2_recipe_candidates.csv`
- `scripts/harvest/harvest_internet_archive_issues.py`
- `scripts/harvest/harvest_internet_archive_recipes.py`
- `scripts/normalize/promote_rev2_candidates.py`
- JSON exports mirrored to `site/public/data/`
- Static site Rev2 review queue and API data

## Verification Standard

Rev2 records use `verification_status=rev2_source_text_verified`.
Each row is derived from Internet Archive magazine OCR context, stores the
source URL, and preserves the harvested context in `original_text`.

## Remaining Post-Rev2 Work

Rev3 should expand reviewed newspaper coverage, add richer page/column
citations, improve OCR boundary review, and strengthen duplicate/reprint
tracking across cookbooks, magazines, and newspapers.
