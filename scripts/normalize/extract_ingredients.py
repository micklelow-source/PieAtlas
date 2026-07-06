#!/usr/bin/env python3
"""Extract ingredient lists from preserved historical recipe text."""

from __future__ import annotations

import csv
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECIPES_CSV = ROOT / "data" / "recipes" / "recipes.csv"

INGREDIENT_MARKER = re.compile(
    r"(?P<label>\bINGREDIENTS?\b\s*(?:[.:;-]+|--|\u2014)\s*)",
    re.IGNORECASE,
)
DIRECTION_MARKER = re.compile(
    r"\b(?:_?MODE_?|DIRECTIONS?|METHOD|PREPARATION)\b\s*(?:[.:;-]+|--|\u2014)\s*",
    re.IGNORECASE,
)
STOP_MARKER = re.compile(
    r"\s+(?:_?TIME_?|AVERAGE\s+COST|SUFFICIENT|SEASONABLE|NOTE|NOTES)\b\s*(?:[.:;-]+|--|\u2014)\s*",
    re.IGNORECASE,
)
PLACEHOLDER_TEXT = re.compile(
    r"\b(?:"
    r"newspaper index record|page-level ocr review remains queued|"
    r"source manifest record|source-manifest|generated from rev4|"
    r"candidate review queue|ocr enrichment is tracked"
    r")\b",
    re.IGNORECASE,
)
NEXT_RECIPE_MARKER = re.compile(
    r"\s(?:_[A-Z][^_]{3,80}_|[A-Z][A-Z0-9 ,;:'&().-]{5,80}\.)"
)
HYPHENATED_OCR = {
    "table- spoonful": "tablespoonful",
    "table- spoonfuls": "tablespoonfuls",
    "tea- spoonful": "teaspoonful",
    "tea- spoonfuls": "teaspoonfuls",
    "cup- ful": "cupful",
    "cup- fuls": "cupfuls",
}
NUMBER_WORD = (
    r"\d+(?:[-/]\d+)?|[a-z]+-[a-z]+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|half|quarter|a|an"
)
MEASURE_OR_COUNT = (
    r"pounds?|lbs?\.?|ounces?|oz\.?|cups?|cupfuls?|pints?|quarts?|gills?|"
    r"teaspoonfuls?|teaspoons?|tablespoonfuls?|tablespoons?|spoonfuls?|spoons?|"
    r"saltspoonfuls?|wineglassfuls?|slices?|squares?|sticks?|cans?|eggs?|yolks?|whites?|"
    r"apples?|chickens?|lobsters?|bananas?|berries?|currants?|lemons?|oranges?|"
    r"gooseberries|raspberries|cherries|apricots|peaches|potatoes|onions?"
)
QUANTITY_INGREDIENT = re.compile(
    rf"\b(?:{NUMBER_WORD})(?:\s+(?:and\s+)?(?:a\s+)?half)?\s+(?:{MEASURE_OR_COUNT})"
    rf"(?:\s+of)?(?:\s+[a-z][a-z'/-]*){{0,8}}",
    re.IGNORECASE,
)
ACTION_WORDS = (
    r"add|bake|beat|boil|chop|cover|cut|fill|lay|line|make|mix|pare|place|"
    r"press|proceeding|put|replace|roll|season|sift|sprinkle|stew|stir|strain|sweeten|turn|wet"
)
HISTORICAL_LEAD_IN = re.compile(
    rf"\b(?:take|use|allow)\s+(?P<items>.{{12,420}}?)(?=\b(?:{ACTION_WORDS})\b|[.!?])",
    re.IGNORECASE,
)
FLOUR_ALLOWANCE = re.compile(
    rf"\bto\s+every\s+(?P<base>.{{6,90}}?)\s+allow\s+(?P<items>.{{8,420}}?)(?=\b(?:{ACTION_WORDS})\b|[.!?])",
    re.IGNORECASE,
)
OPENING_BLOCK_END = re.compile(rf"\b(?:{ACTION_WORDS})\b", re.IGNORECASE)
INGREDIENT_WORDS = [
    "apples",
    "apple",
    "apricots",
    "bananas",
    "beef",
    "berries",
    "blackberries",
    "brandy",
    "bread",
    "butter",
    "cherries",
    "chickens",
    "cinnamon",
    "cream",
    "crust",
    "currants",
    "eggs",
    "flour",
    "gooseberries",
    "grapes",
    "lard",
    "lemon",
    "mace",
    "milk",
    "molasses",
    "nutmeg",
    "orange",
    "paste",
    "pepper",
    "pork",
    "raisins",
    "raspberries",
    "rose-water",
    "salt",
    "shortening",
    "suet",
    "sugar",
    "veal",
    "vinegar",
    "water",
    "wine",
]


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip(" ;,.-")


def normalize_recipe_text(value: str) -> str:
    text = value or ""
    for original, replacement in HYPHENATED_OCR.items():
        text = re.sub(original, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"(?<=[a-z])- (?=[a-z])", "", text)
    return clean(text)


def unique_items(items: object) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        cleaned = clean(str(item))
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            unique.append(cleaned)
    return unique


def split_marked_ingredients(text: str) -> tuple[str, str] | None:
    text = normalize_recipe_text(text)
    ingredient_match = INGREDIENT_MARKER.search(text)
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


def focused_recipe_body(row: dict[str, str], text: str) -> str:
    text = normalize_recipe_text(text)
    start = 0
    for key in ("original_title", "title"):
        title = clean(row.get(key, ""))
        if title and len(title) > 4:
            match = re.search(re.escape(title), text, re.IGNORECASE)
            if match:
                start = match.end()
                break
    body = text[start:]
    next_match = NEXT_RECIPE_MARKER.search(body, 40)
    if next_match:
        body = body[: next_match.start()]
    return body[:900]


def split_quantity_ingredients(row: dict[str, str], text: str) -> tuple[str, str] | None:
    body = focused_recipe_body(row, text)
    items = unique_items(clean_quantity_match(match.group(0)) for match in QUANTITY_INGREDIENT.finditer(body))
    items = [item for item in items if is_plausible_quantity_item(item)]
    if len(items) < 2:
        return None
    return "; ".join(items), normalize_recipe_text(text)


def split_named_ingredients(row: dict[str, str], text: str) -> tuple[str, str] | None:
    body = focused_recipe_body(row, text)[:420].lower()
    if not re.search(r"\b(?:add|bake|boil|cover|lay|line|make|mix|pare|put|roll|stew|sweeten)\b", body):
        return None
    found = []
    for ingredient in INGREDIENT_WORDS:
        if re.search(rf"\b{re.escape(ingredient)}\b", body):
            found.append(ingredient)
    found = unique_items(found)
    if len(found) < 3:
        return None
    return "; ".join(found), normalize_recipe_text(text)


def split_historical_leadin_ingredients(row: dict[str, str], text: str) -> tuple[str, str] | None:
    body = focused_recipe_body(row, text)
    for pattern in (FLOUR_ALLOWANCE, HISTORICAL_LEAD_IN):
        match = pattern.search(body)
        if not match:
            continue
        items = historical_items_from_match(match)
        if is_plausible_historical_items(items, minimum_hits=2, require_list_punctuation=False):
            return items, normalize_recipe_text(text)
    return None


def split_opening_block_ingredients(row: dict[str, str], text: str) -> tuple[str, str] | None:
    body = focused_recipe_body(row, text)
    match = OPENING_BLOCK_END.search(body, 24)
    if not match:
        return None
    candidate = clean(body[: match.start()])
    if not is_plausible_historical_items(candidate, minimum_hits=3, require_list_punctuation=True):
        return None
    return candidate, normalize_recipe_text(text)


def historical_items_from_match(match: re.Match[str]) -> str:
    if "base" in match.groupdict():
        value = f"{match.group('base')}; {match.group('items')}"
    else:
        value = match.group("items")
    return clean_historical_items(value)


def clean_historical_items(value: str) -> str:
    value = clean(value)
    value = re.sub(r"\b(?:then|when|until|proceeding as above)\b.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+(?:in|into|on|over|through|to)\s+(?:a|an|the)\b.*$", "", value, flags=re.IGNORECASE)
    items = unique_items(
        item for item in re.split(r";|,\s+and\s+|\s+and\s+(?=(?:one|two|three|four|five|six|half|a|an|\d))", value)
    )
    if len(items) >= 2:
        return "; ".join(items)
    return value


def is_plausible_historical_items(value: str, minimum_hits: int, require_list_punctuation: bool) -> bool:
    if len(value) < 10 or len(value) > 500:
        return False
    if re.search(
        r"[?\"\u201c\u201d]|\b(?:advertisement|better for cleaning|directed that|doubting|fortune|people|read of|success|suppose)\b",
        value,
        re.IGNORECASE,
    ):
        return False
    if re.match(r"^(?:and\b|then\b|_+|-+|\(?no\.|\(?\d+\.|make|roll|spread|transfer)\b", value, re.IGNORECASE):
        return False
    if re.search(r"\b(?:brush|cut|pare|press|replace|sprinkle|turn|wet)\b", value, re.IGNORECASE):
        return False
    lower = value.lower()
    ingredient_hits = sum(1 for ingredient in INGREDIENT_WORDS if re.search(rf"\b{re.escape(ingredient)}\b", lower))
    quantity_hits = len(QUANTITY_INGREDIENT.findall(value))
    if quantity_hits + ingredient_hits < minimum_hits:
        return False
    if require_list_punctuation and quantity_hits < 2 and not re.search(r"[,;]", value):
        return False
    if re.search(r"\b(?:average cost|seasonable|sufficient|serve|minutes?|hours?|oven)\b", lower):
        return False
    return True


def extract_cookbook_recipe(row: dict[str, str]) -> tuple[str, str] | None:
    """Extract from cookbook rows, preferring formal INGREDIENTS / Mode blocks."""
    source_text = recipe_text(row)
    return (
        split_marked_ingredients(source_text)
        or split_quantity_ingredients(row, source_text)
        or split_historical_leadin_ingredients(row, source_text)
        or split_opening_block_ingredients(row, source_text)
        or split_named_ingredients(row, source_text)
    )


def extract_magazine_paragraph_recipe(row: dict[str, str]) -> tuple[str, str] | None:
    """Extract from magazine prose where ingredients are often embedded in paragraphs."""
    source_text = recipe_text(row)
    if is_placeholder_record(row, source_text):
        return None
    return split_quantity_ingredients(row, source_text) or split_named_ingredients(row, source_text)


def extract_newspaper_index_record(row: dict[str, str]) -> tuple[str, str] | None:
    """Skip newspaper index placeholders unless a row later gains real recipe text."""
    source_text = recipe_text(row)
    if is_placeholder_record(row, source_text):
        return None
    return split_quantity_ingredients(row, source_text) or split_named_ingredients(row, source_text)


def extract_collection_source_manifest_record(row: dict[str, str]) -> tuple[str, str] | None:
    """Skip source-manifest placeholders unless a collection row has recipe prose."""
    source_text = recipe_text(row)
    if is_placeholder_record(row, source_text):
        return None
    return (
        split_marked_ingredients(source_text)
        or split_quantity_ingredients(row, source_text)
        or split_historical_leadin_ingredients(row, source_text)
        or split_opening_block_ingredients(row, source_text)
        or split_named_ingredients(row, source_text)
    )


def extract_by_source_type(row: dict[str, str]) -> tuple[str, str] | None:
    extractors = {
        "cookbook": extract_cookbook_recipe,
        "magazine": extract_magazine_paragraph_recipe,
        "newspaper": extract_newspaper_index_record,
        "collection": extract_collection_source_manifest_record,
    }
    extractor = extractors.get(row.get("source_type", ""))
    if extractor:
        return extractor(row)
    return extract_magazine_paragraph_recipe(row)


def recipe_text(row: dict[str, str]) -> str:
    return row.get("original_text", "") or row.get("directions_original", "")


def is_placeholder_record(row: dict[str, str], text: str) -> bool:
    searchable = " ".join(
        [
            row.get("title", ""),
            row.get("source_title", ""),
            row.get("verification_status", ""),
            row.get("notes", ""),
            text,
        ]
    )
    return bool(PLACEHOLDER_TEXT.search(searchable))


def clean_quantity_match(value: str) -> str:
    value = clean(value)
    value = re.split(
        r"\b(?:and\s+(?:add|bake|boil|cover|let|mix|put|stir)|then|when|until|with\s+a\s+fork)\b",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    value = re.sub(r"\s+(?:in|into|on|over|through|to)\s+(?:a|an|the)\b.*$", "", value, flags=re.IGNORECASE)
    return clean(value)


def is_plausible_quantity_item(value: str) -> bool:
    if len(value) < 6 or len(value) > 140:
        return False
    if re.search(r"\b(?:bake|boil|cook|serve|oven|minutes?|hours?|recipe)\b", value, re.IGNORECASE):
        return False
    return is_plausible_ingredient_list(value)


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


def extract_row(row: dict[str, str], refresh: bool = False) -> bool:
    original_ingredients = row.get("ingredients_original", "")
    original_directions = row.get("directions_original", "")
    if clean(original_ingredients) and not refresh:
        return False

    extracted = extract_by_source_type(row)
    if not extracted:
        if refresh:
            row["ingredients_original"] = ""
            row["directions_original"] = normalize_recipe_text(recipe_text(row))
            return row.get("ingredients_original", "") != original_ingredients or row.get("directions_original", "") != original_directions
        return False

    ingredients, directions = extracted
    row["ingredients_original"] = ingredients
    if directions:
        row["directions_original"] = directions
    return True


def main() -> None:
    refresh = "--refresh" in sys.argv[1:]
    with RECIPES_CSV.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        raise SystemExit("recipes.csv has no header")

    updated = sum(1 for row in rows if extract_row(row, refresh=refresh))
    if not updated:
        print("No ingredient lists found to extract")
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
