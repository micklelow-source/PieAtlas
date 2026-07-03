# Rev3 Completion

Rev3 is complete at 5,000 total records.

## Completed deliverables

- 2,000 Rev1/Rev2 records retained
- 3,000 Rev3 newspaper index records promoted
- `data/recipes/rev3_newspaper_candidates.csv`
- `scripts/harvest/harvest_chronicling_america.py`
- `scripts/normalize/promote_rev3_candidates.py`
- JSON exports mirrored to `site/public/data/`

## Verification Standard

Rev3 records use `verification_status=rev3_newspaper_index_verified`.
They are generated from the Chronicling America search manifest and preserve the
query/index context needed for OCR and page-level enrichment.

## Post-Rev3 Enrichment

Future passes should rehydrate each index record with OCR text, page image URLs,
column details, and stronger duplicate/reprint matching.
