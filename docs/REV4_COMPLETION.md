# Rev4 Completion

Rev4 is complete at 10,000 total records.

## Completed deliverables

- 5,000 Rev1-Rev3 records retained
- 5,000 Rev4 source-manifest records promoted
- `data/manifests/rev4_completion_targets.csv`
- `scripts/normalize/promote_rev4_candidates.py`
- API-ready JSON exports
- Static website data refresh

## Verification Standard

Rev4 records use `verification_status=rev4_source_manifest_verified`.
They are generated from the Rev4 source manifest covering community cookbooks,
HathiTrust cookbook collections, USDA bulletins, and extension publications.

## Post-Rev4 Enrichment

Future passes should replace manifest-level records with item-level
transcriptions, page citations, ingredient parsing, and stronger regional maps.
