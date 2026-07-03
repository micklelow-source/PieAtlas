# Rev2 Plan

Status: complete.

Target: 2,000 source-text-verified recipe records.

## Scope

Rev2 extends Rev1 with public-domain magazines, household journals, and regional
food columns published through 1928.

## Workflow

```bash
python scripts/harvest/harvest_internet_archive_issues.py 25 data/magazines/rev2_issue_candidates.csv
python scripts/harvest/harvest_internet_archive_recipes.py 10 data/magazines/rev2_recipe_candidates.csv 30
python scripts/export/export_data.py
python scripts/validate/validate_recipes.py
python -m unittest discover -s tests
```

## Review Rule

Rev2 candidates are not canonical recipes. Promote a magazine candidate only
after verifying public-domain status, issue metadata, OCR quality, recipe
boundaries, and whether it is a reprint of an existing Rev1 recipe.

## Promotion Standard

Rev2 promoted rows use `revision=rev2`, preserve magazine issue OCR context in
`original_text`, store the issue URL in `source_url`, and keep
`duplicate_status` explicit for reprints.
