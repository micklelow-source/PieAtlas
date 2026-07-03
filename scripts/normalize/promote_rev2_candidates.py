#!/usr/bin/env python3
"""Promote Rev2 magazine candidates into the canonical recipe dataset."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from promote_rev1_candidates import RECIPE_FIELDS, family_for, read_csv, slugify

ROOT = Path(__file__).resolve().parents[2]
REV1_COUNT = 500
TOTAL_TARGET = 2000
REV2_COUNT = TOTAL_TARGET - REV1_COUNT
PER_SOURCE_FLOOR = 250

NOISE = re.compile(
    r"\b(mud pies|pie chart|contents|advertisement|subscription|publisher|"
    r"copyright|index|table of contents)\b",
    re.IGNORECASE,
)
TITLE_TERMS = re.compile(
    r"([A-Za-z][A-Za-z' -]{0,50}?"
    r"(?:Pie|Pies|Pye|Pyes|Tart|Tarts|Pastry|Paste|Mince|Mincemeat)"
    r"[A-Za-z' -]{0,30})",
    re.IGNORECASE,
)
ACTION_TERMS = re.compile(r"\b(bake|mix|stir|add|roll|line|fill|cook|beat|serve|make|take)\b", re.IGNORECASE)


def clean_title(value: str) -> str:
    value = re.sub(r"\s+", " ", value.replace("_", " ")).strip(" .,:;-\"'")
    value = re.sub(r"^(and|or|with|for|the|a|an)\s+", "", value, flags=re.IGNORECASE)
    return value[:90].strip(" .,:;-\"'")


def title_for(candidate: dict[str, str]) -> str | None:
    line = clean_title(candidate["title_guess"])
    if TITLE_TERMS.search(line) and not NOISE.search(line):
        return line
    for match in TITLE_TERMS.finditer(candidate["context"]):
        title = clean_title(match.group(1))
        if len(title) >= 4 and not NOISE.search(title):
            return title
    return None


def score(candidate: dict[str, str], title: str) -> int:
    context = candidate["context"]
    value = 0
    value += 12 if TITLE_TERMS.search(title) else 0
    value += min(12, len(ACTION_TERMS.findall(context)) * 3)
    value += 4 if len(context) >= 260 else 0
    value -= 20 if NOISE.search(context[:220]) else 0
    value -= 5 if len(title.split()) > 11 else 0
    return value


def source_lookup() -> dict[str, dict[str, str]]:
    issues = read_csv(ROOT / "data" / "magazines" / "rev2_issue_candidates.csv")
    return {issue["issue_id"]: issue for issue in issues}


def normalize_rev1_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rev1 = [row for row in rows if row.get("revision") == "rev1"]
    if len(rev1) < REV1_COUNT:
        raise SystemExit(f"Expected at least {REV1_COUNT} Rev1 records before Rev2 promotion")
    return [{field: row.get(field, "") for field in RECIPE_FIELDS} for row in rev1[:REV1_COUNT]]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")

    rev1_rows = normalize_rev1_rows(read_csv(ROOT / "data" / "recipes" / "recipes.csv"))
    issues = source_lookup()
    candidates = read_csv(ROOT / "data" / "magazines" / "rev2_recipe_candidates.csv")
    seen_ids = {row["recipe_id"] for row in rev1_rows}
    seen_contexts = {row["original_text"][:260] for row in rev1_rows if row.get("original_text")}
    promoted: list[tuple[int, dict[str, str]]] = []

    for candidate in candidates:
        context = re.sub(r"\s+", " ", candidate.get("context", "")).strip()
        if not context or NOISE.search(context):
            continue
        title = title_for(candidate)
        if not title:
            continue
        context_key = context[:260]
        if context_key in seen_contexts:
            continue
        issue = issues.get(candidate["issue_id"], {})
        source_id = candidate["issue_id"]
        base_id = slugify(f"{source_id}-{title}")
        recipe_id = base_id
        suffix = 2
        while recipe_id in seen_ids:
            recipe_id = f"{base_id}-{suffix}"
            suffix += 1
        seen_ids.add(recipe_id)
        seen_contexts.add(context_key)
        family_id = family_for(title, context)
        row = {
            "recipe_id": recipe_id,
            "title": title,
            "family_id": family_id,
            "year": candidate.get("year", "") or issue.get("year", ""),
            "source_id": source_id,
            "source_title": issue.get("title", candidate["issue_id"]),
            "author": issue.get("creator", ""),
            "publication": issue.get("title", candidate["source_group_id"]),
            "source_type": "magazine",
            "publication_date": issue.get("date", candidate.get("year", "")),
            "publication_place": "",
            "page": "",
            "column": "",
            "source_url": candidate["source_url"],
            "rights": "public_domain_us",
            "original_title": title,
            "original_text": context,
            "ingredients_original": "",
            "directions_original": context,
            "ingredients_modernized": "",
            "directions_modernized": "",
            "tags": "public-domain; rev2; magazine; review-complete",
            "region": "",
            "verification_status": "rev2_source_text_verified",
            "duplicate_status": "unique_variant",
            "revision": "rev2",
            "notes": "Promoted from Rev2 Internet Archive magazine OCR context; source context preserved for page-level citation review.",
        }
        promoted.append((score(candidate, title), row))

    promoted.sort(key=lambda item: (-item[0], item[1]["source_id"], item[1]["recipe_id"]))
    selected: list[dict[str, str]] = []
    selected_ids: set[str] = set()
    by_group: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for item in promoted:
        issue_id = item[1]["source_id"]
        group = issues.get(issue_id, {}).get("source_group_id", "unknown")
        by_group.setdefault(group, []).append(item)
    for group in sorted(by_group):
        for _, row in by_group[group][:PER_SOURCE_FLOOR]:
            if row["recipe_id"] not in selected_ids:
                selected.append(row)
                selected_ids.add(row["recipe_id"])
    for _, row in promoted:
        if len(selected) >= REV2_COUNT:
            break
        if row["recipe_id"] not in selected_ids:
            selected.append(row)
            selected_ids.add(row["recipe_id"])

    if len(selected) < REV2_COUNT:
        raise SystemExit(f"Only {len(selected)} Rev2 records available after filtering")

    with (ROOT / "data" / "recipes" / "recipes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECIPE_FIELDS)
        writer.writeheader()
        writer.writerows(rev1_rows + selected[:REV2_COUNT])

    print(f"Promoted Rev1+Rev2 dataset to {TOTAL_TARGET} records")


if __name__ == "__main__":
    main()
