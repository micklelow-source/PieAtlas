#!/usr/bin/env python3
"""Extract marked ingredient lists from preserved historical recipe text."""

from __future__ import annotations

import csv
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES_CSV = ROOT / "data" / "recipes" / "recipes.csv"

INGREDIENT_MARKER = re.compile(
    r"(?P<label>\bINGREDIENTS?\b\s*(?:[.:;-]+|--|—)\s*)",
    re.IGNORECASE,
)
DIRECTION_MARKER = re.compile(
    r"\b(?:_?MODE_?|DIRECTIONS?|METHOD|PREPARATION)\b\s*(?:[.:;-]+|--|—)\s*",
    re.IGNORECASE,
)
STOP_MARKER = re.compile(
    r"\s+(?:_?TIME_?|AVERAGE\s+COST|SUFFICIENT|SEASONABLE|NOTE|NOTES)\b\s*(?:[.:;-]+|--|—)\s*",
    re.IGNORECASE,
)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip(" ;,.-")


def split_marked_ingredients(text: str) -> tuple[str, str] | None:
    ingredient_match = INGREDIENT_MARKER.search(text or "")
    if not ingredient_match:
        return None

    start = ingredient_match.end()
    direction_match = DIRECTION_MARKER.search(text, start)
    if not direction_match:
        stop_match = STOP_MARKER.search(text, start)
        if not stop_match:
            return None
        ingredients = clean(text[start:stop_match.start()])
        directions = clean(text[: ingredient_match.start()] + " " + text[stop_match.start() :])
    else:
        ingredients = clean(text[start:direction_match.start()])
        directions = clean(text[: ingredient_match.start()] + " " + text[direction_match.end() :])

    if not is_plausible_ingredient_list(ingredients):
        return None
    return ingredients, directions


def is_plausible_ingredient_list(value: str) -> bool:
    if len(value) < 8 or len(value) > 900:
        return False
    lower = value.lower()
    measures = [
        "cup",
        "pint",
        "quart",
        "lb",
        "pound",
        "ounce",
        "oz",
        "spoon",
        "teaspoon",
        "tablespoon",
        "egg",
        "butter",
        "sugar",
        "flour",
        "milk",
        "salt",
        "paste",
        "crust",
    ]
    return any(measure in lower for measure in measures)


def extract_row(row: dict[str, str]) -> bool:
    if clean(row.get("ingredients_original", "")):
        return False

    source_text = row.get("original_text", "") or row.get("directions_original", "")
    extracted = split_marked_ingredients(source_text)
    if not extracted:
        return False

    ingredients, directions = extracted
    row["ingredients_original"] = ingredients
    if directions:
        row["directions_original"] = directions
    return True


def main() -> None:
    with RECIPES_CSV.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        raise SystemExit("recipes.csv has no header")

    updated = sum(1 for row in rows if extract_row(row))
    if not updated:
        print("No marked ingredient lists found to extract")
        return

    backup = RECIPES_CSV.with_suffix(".csv.bak")
    shutil.copy2(RECIPES_CSV, backup)
    with RECIPES_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    backup.unlink()
    print(f"Extracted ingredients for {updated} recipes")


if __name__ == "__main__":
    sys.exit(main())
