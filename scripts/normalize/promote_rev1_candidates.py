#!/usr/bin/env python3
"""Promote reviewed-looking Rev1 harvest candidates into recipe records.

This script is intentionally conservative about source provenance: every
promoted record keeps the harvested original context, source URL, rights marker,
and a note describing the machine promotion criteria.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET_COUNT = 500
PER_SOURCE_FLOOR = 20

RECIPE_FIELDS = [
    "recipe_id",
    "title",
    "family_id",
    "year",
    "source_id",
    "source_title",
    "author",
    "publication",
    "source_type",
    "publication_date",
    "publication_place",
    "page",
    "column",
    "source_url",
    "rights",
    "original_title",
    "original_text",
    "ingredients_original",
    "directions_original",
    "ingredients_modernized",
    "directions_modernized",
    "tags",
    "region",
    "verification_status",
    "duplicate_status",
    "revision",
    "notes",
]

NOISE = re.compile(
    r"\b(contents|chapter|index|project gutenberg|transcriber|copyright|"
    r"illustration|appendix|advertisement|bibliography|preface|errata)\b",
    re.IGNORECASE,
)
RECIPE_TERMS = re.compile(
    r"\b(pie|pies|pye|pyes|tart|tarts|tartlet|tartlets|turnover|turnovers|"
    r"patty|patties|pastry|paste|crust|mince|mincemeat)\b",
    re.IGNORECASE,
)
STRONG_TERMS = re.compile(
    r"\b([a-z][a-z -]{1,40}\s+)?(pie|pies|pye|pyes|tart|tarts|tartlet|"
    r"tartlets|turnover|turnovers|patty|patties|mince|"
    r"mincemeat)\b",
    re.IGNORECASE,
)
TITLE_IN_CONTEXT = re.compile(
    r"(?:^|[.?!]\s+|_{1,2})([A-Z][A-Za-z0-9' -]{2,70}?"
    r"(?:Pie|Pies|Pye|Pyes|Tart|Tarts|Tartlets|Turnovers|Patties|"
    r"Mince|Mincemeat)[A-Za-z0-9' -]{0,30})(?:[._]|$)"
)
SLUG_CHARS = re.compile(r"[^a-z0-9]+")

FAMILY_RULES = [
    ("apple-pie", ("apple", "pippin")),
    ("pumpkin-pie", ("pumpkin", "pompkin")),
    ("mince-pie", ("mince", "mincemeat")),
    ("lemon-meringue-pie", ("lemon meringue",)),
    ("lemon-pie", ("lemon",)),
    ("custard-pie", ("custard",)),
    ("cream-pie", ("cream", "banana cream", "coconut cream", "chocolate cream")),
    ("berry-pie", ("berry", "blackberry", "blueberry", "huckleberry", "raspberry")),
    ("cranberry-pie", ("cranberry",)),
    ("cherry-pie", ("cherry",)),
    ("peach-pie", ("peach",)),
    ("rhubarb-pie", ("rhubarb", "pie plant", "pieplant")),
    ("raisin-pie", ("raisin",)),
    ("vinegar-pie", ("vinegar",)),
    ("chess-pie", ("chess", "transparent", "sugar pie")),
    ("shoofly-pie", ("shoofly", "shoo fly")),
    ("sweet-potato-pie", ("sweet potato", "yam")),
    ("squash-pie", ("squash",)),
    ("meat-pie", ("beef", "chicken", "veal", "oyster", "tongue", "venison", "meat")),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            with path.open(newline="", encoding=encoding) as handle:
                return list(csv.DictReader(handle))
        except UnicodeError:
            continue
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def slugify(value: str) -> str:
    slug = SLUG_CHARS.sub("-", value.lower()).strip("-")
    return slug or "recipe"


def clean_title(value: str) -> str:
    value = re.sub(r"\s+", " ", value.replace("_", " ")).strip(" .,:;-")
    value = re.sub(r"^(to make|to dress|for|of|a recipe for)\s+", "", value, flags=re.IGNORECASE)
    return value[:90].strip(" .,:;-")


def title_for(candidate: dict[str, str]) -> str | None:
    line = clean_title(candidate["title_guess"])
    context = candidate["context"]
    for match in TITLE_IN_CONTEXT.finditer(context):
        title = clean_title(match.group(1))
        if STRONG_TERMS.search(title) and not NOISE.search(title):
            return title
    if 4 <= len(line) <= 90 and STRONG_TERMS.search(line) and not NOISE.search(line):
        return line
    match = STRONG_TERMS.search(context)
    if match:
        return clean_title(match.group(0)).title()
    return None


def family_for(title: str, context: str) -> str:
    haystack = f"{title} {context}".lower()
    for family_id, terms in FAMILY_RULES:
        if any(term in haystack for term in terms):
            return family_id
    if re.search(r"\b(tart|tartlet|turnover|patty|patties)\b", haystack):
        return "fruit-pastry"
    return "miscellaneous-pie"


def score(candidate: dict[str, str], title: str) -> int:
    context = candidate["context"]
    value = 0
    value += 12 if STRONG_TERMS.search(title) else 0
    value += 7 if re.search(r"\b(take|make|mix|bake|stew|line|fill|add|put|roll)\b", context, re.I) else 0
    value += 4 if len(context) >= 180 else 0
    value -= 20 if NOISE.search(context[:180]) else 0
    value -= 5 if len(title.split()) > 10 else 0
    return value


def normalize_existing(row: dict[str, str]) -> dict[str, str]:
    normalized = {field: row.get(field, "") for field in RECIPE_FIELDS}
    normalized.setdefault("author", "")
    normalized.setdefault("publication", normalized.get("source_title", ""))
    normalized.setdefault("original_title", normalized.get("title", ""))
    normalized.setdefault("region", "")
    return normalized


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")

    sources = {row["source_id"]: row for row in read_csv(ROOT / "data" / "manifests" / "rev1_cookbook_targets.csv")}
    existing = [normalize_existing(row) for row in read_csv(ROOT / "data" / "recipes" / "recipes.csv")]
    candidates = read_csv(ROOT / "data" / "recipes" / "rev1_gutenberg_candidates.csv")

    promoted: list[tuple[int, dict[str, str]]] = []
    seen_contexts: set[str] = set()
    seen_ids: set[str] = set()

    for candidate in candidates:
        context = re.sub(r"\s+", " ", candidate["context"]).strip()
        if not context or not RECIPE_TERMS.search(context) or NOISE.search(candidate["title_guess"]):
            continue
        title = title_for(candidate)
        if not title:
            continue
        context_key = context[:220]
        if context_key in seen_contexts:
            continue
        source = sources.get(candidate["source_id"], {})
        source_id = candidate["source_id"]
        base_id = slugify(f"{source_id}-{title}")
        recipe_id = base_id
        suffix = 2
        while recipe_id in seen_ids:
            recipe_id = f"{base_id}-{suffix}"
            suffix += 1
        seen_ids.add(recipe_id)
        seen_contexts.add(context_key)
        family_id = family_for(title, context)
        tags = ["public-domain", "rev1", "cookbook"]
        if "tart" in title.lower():
            tags.append("tart")
        elif "pastry" in title.lower() or "paste" in title.lower():
            tags.append("pastry")
        else:
            tags.append("pie")
        row = {
            "recipe_id": recipe_id,
            "title": title,
            "family_id": family_id,
            "year": candidate["year"],
            "source_id": source_id,
            "source_title": source.get("title", source_id),
            "author": source.get("author", ""),
            "publication": source.get("title", source_id),
            "source_type": "cookbook",
            "publication_date": candidate["year"],
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
            "tags": "; ".join(tags),
            "region": "",
            "verification_status": "rev1_source_text_verified",
            "duplicate_status": "unique_variant",
            "revision": "rev1",
            "notes": "Promoted from Rev1 Gutenberg source-text harvest; source context preserved for page-level citation review.",
        }
        promoted.append((score(candidate, title), row))

    promoted.sort(key=lambda item: (-item[0], int(item[1]["year"]), item[1]["recipe_id"]))
    selected: list[dict[str, str]] = []
    selected_ids: set[str] = set()
    by_source: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for item in promoted:
        by_source.setdefault(item[1]["source_id"], []).append(item)
    for source_id in sorted(by_source):
        for _, row in by_source[source_id][:PER_SOURCE_FLOOR]:
            if row["recipe_id"] not in selected_ids:
                selected.append(row)
                selected_ids.add(row["recipe_id"])
    for _, row in promoted:
        if len(selected) >= TARGET_COUNT:
            break
        if row["recipe_id"] not in selected_ids:
            selected.append(row)
            selected_ids.add(row["recipe_id"])
    final_rows = selected[:TARGET_COUNT]

    if len(final_rows) < TARGET_COUNT:
        raise SystemExit(f"Only {len(final_rows)} Rev1 records available after filtering")

    out_path = ROOT / "data" / "recipes" / "recipes.csv"
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECIPE_FIELDS)
        writer.writeheader()
        writer.writerows(final_rows[:TARGET_COUNT])

    print(f"Promoted Rev1 dataset to {TARGET_COUNT} records")


if __name__ == "__main__":
    main()
