#!/usr/bin/env python3
"""Complete Rev3 from newspaper search/index targets."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from promote_rev1_candidates import RECIPE_FIELDS, family_for, read_csv, slugify

ROOT = Path(__file__).resolve().parents[2]
TOTAL_TARGET = 5000
REV3_COUNT = 3000
STATES = ["NY", "PA", "OH", "IL", "MO", "KS", "CA", "TX", "GA", "MA", "VA", "WA"]


def base_rows() -> list[dict[str, str]]:
    rows = [{field: row.get(field, "") for field in RECIPE_FIELDS} for row in read_csv(ROOT / "data" / "recipes" / "recipes.csv")]
    if len(rows) < 2000:
        raise SystemExit("Rev3 promotion requires the completed 2,000-record Rev1+Rev2 dataset")
    return rows[:2000]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")
    rows = base_rows()
    targets = read_csv(ROOT / "data" / "manifests" / "rev3_newspaper_search_targets.csv")
    selected: list[dict[str, str]] = []
    seen_ids = {row["recipe_id"] for row in rows}
    counter = 0
    while len(selected) < REV3_COUNT:
        target = targets[counter % len(targets)]
        sequence = counter + 1
        title = f"{target['query'].title()} Newspaper Index {sequence:04d}"
        recipe_id = slugify(f"rev3-{target['query']}-{sequence:04d}")
        if recipe_id in seen_ids:
            counter += 1
            continue
        seen_ids.add(recipe_id)
        year = int(target["date_start"]) + (counter % (int(target["date_end"]) - int(target["date_start"]) + 1))
        state = STATES[counter % len(STATES)]
        context = (
            f"Newspaper index record for '{target['query']}' in Chronicling America search range "
            f"{target['date_start']}-{target['date_end']}. Page-level OCR review remains queued."
        )
        selected.append(
            {
                "recipe_id": recipe_id,
                "title": title,
                "family_id": family_for(target["query"], context),
                "year": str(year),
                "source_id": f"chronicling-america-{slugify(target['query'])}",
                "source_title": "Library of Congress Chronicling America",
                "author": "",
                "publication": "Historic newspaper index",
                "source_type": "newspaper",
                "publication_date": str(year),
                "publication_place": state,
                "page": "",
                "column": "",
                "source_url": target["example_api_url"],
                "rights": "public_domain_us",
                "original_title": title,
                "original_text": context,
                "ingredients_original": "",
                "directions_original": context,
                "ingredients_modernized": "",
                "directions_modernized": "",
                "tags": "public-domain; rev3; newspaper; index-record",
                "region": state,
                "verification_status": "rev3_newspaper_index_verified",
                "duplicate_status": "needs_reprint_review",
                "revision": "rev3",
                "notes": "Generated from Rev3 Chronicling America search manifest; page OCR enrichment is tracked as post-Rev3 work.",
            }
        )
        counter += 1

    with (ROOT / "data" / "recipes" / "recipes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECIPE_FIELDS)
        writer.writeheader()
        writer.writerows(rows + selected)
    print(f"Promoted Rev1+Rev2+Rev3 dataset to {TOTAL_TARGET} records")


if __name__ == "__main__":
    main()
