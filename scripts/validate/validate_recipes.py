#!/usr/bin/env python3
"""Validate PieAtlas recipe data against the project schema."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

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

REQUIRED_VALUES = [
    "recipe_id",
    "title",
    "family_id",
    "year",
    "source_title",
    "source_url",
    "rights",
    "verification_status",
    "duplicate_status",
]

PUBLIC_DOMAIN_RIGHTS = {"public_domain_us", "public_domain"}
REV1_TARGET = 500
REV2_TOTAL_TARGET = 2000
REV3_TOTAL_TARGET = 5000
REV4_TOTAL_TARGET = 10000
REV2_ISSUE_FIELDS = [
    "issue_id",
    "source_group_id",
    "revision",
    "title",
    "creator",
    "year",
    "date",
    "repository",
    "source_url",
    "status",
]
REV2_RECIPE_CANDIDATE_FIELDS = [
    "candidate_id",
    "issue_id",
    "source_group_id",
    "revision",
    "year",
    "title_guess",
    "context",
    "source_url",
    "ocr_text_url",
    "status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


def validate() -> list[str]:
    errors: list[str] = []
    recipes_path = ROOT / "data" / "recipes" / "recipes.csv"
    families_path = ROOT / "data" / "families" / "recipe_families.csv"
    recipes = read_csv(recipes_path)
    families = read_csv(families_path)

    if recipes and list(recipes[0].keys()) != RECIPE_FIELDS:
        errors.append("recipes.csv header does not match the PieAtlas recipe schema")
    if len(recipes) < REV1_TARGET:
        errors.append(f"Rev1 requires at least {REV1_TARGET} recipe records")
    if len(recipes) < REV2_TOTAL_TARGET:
        errors.append(f"Rev2 requires at least {REV2_TOTAL_TARGET} recipe records")
    if len(recipes) < REV3_TOTAL_TARGET:
        errors.append(f"Rev3 requires at least {REV3_TOTAL_TARGET} recipe records")
    if len(recipes) < REV4_TOTAL_TARGET:
        errors.append(f"Rev4 requires at least {REV4_TOTAL_TARGET} recipe records")

    family_ids = {family["family_id"] for family in families}
    recipe_ids: set[str] = set()
    for index, recipe in enumerate(recipes, 2):
        label = f"row {index}"
        for field in REQUIRED_VALUES:
            if not recipe.get(field):
                errors.append(f"{label}: missing {field}")
        recipe_id = recipe.get("recipe_id", "")
        if recipe_id in recipe_ids:
            errors.append(f"{label}: duplicate recipe_id {recipe_id}")
        recipe_ids.add(recipe_id)
        family_id = recipe.get("family_id", "")
        if family_id and family_id not in family_ids:
            errors.append(f"{label}: unknown family_id {family_id}")
        year = recipe.get("year", "")
        if not year.isdigit() or int(year) > 1928:
            errors.append(f"{label}: year must be numeric and no later than 1928")
        if recipe.get("rights") not in PUBLIC_DOMAIN_RIGHTS:
            errors.append(f"{label}: rights must identify public-domain status")
        if recipe.get("source_url") and not recipe["source_url"].startswith(("http://", "https://")):
            errors.append(f"{label}: source_url must be absolute")
        if recipe.get("revision") == "rev1" and recipe.get("verification_status") != "rev1_source_text_verified":
            errors.append(f"{label}: Rev1 records must be source-text verified")
        if recipe.get("revision") == "rev2" and recipe.get("verification_status") != "rev2_source_text_verified":
            errors.append(f"{label}: Rev2 records must be source-text verified")
        if recipe.get("revision") == "rev3" and recipe.get("verification_status") != "rev3_newspaper_index_verified":
            errors.append(f"{label}: Rev3 records must be newspaper-index verified")
        if recipe.get("revision") == "rev4" and recipe.get("verification_status") != "rev4_source_manifest_verified":
            errors.append(f"{label}: Rev4 records must be source-manifest verified")
        if recipe.get("verification_status") == "rev1_source_text_verified" and not recipe.get("original_text"):
            errors.append(f"{label}: source-text verified records must preserve original_text")
        if recipe.get("verification_status") == "rev2_source_text_verified" and not recipe.get("original_text"):
            errors.append(f"{label}: source-text verified records must preserve original_text")
        if recipe.get("verification_status") in {"rev3_newspaper_index_verified", "rev4_source_manifest_verified"} and not recipe.get("original_text"):
            errors.append(f"{label}: verified records must preserve original_text")

    json_recipes = read_json(ROOT / "data" / "recipes" / "recipes.json")
    site_recipes = read_json(ROOT / "site" / "public" / "data" / "recipes.json")
    if len(json_recipes) != len(recipes):
        errors.append("recipes.json is out of sync with recipes.csv")
    if json_recipes != site_recipes:
        errors.append("site/public/data/recipes.json is out of sync with data/recipes/recipes.json")

    errors.extend(validate_optional_candidate_file(ROOT / "data" / "magazines" / "rev2_issue_candidates.csv", REV2_ISSUE_FIELDS))
    errors.extend(
        validate_optional_candidate_file(
            ROOT / "data" / "magazines" / "rev2_recipe_candidates.csv",
            REV2_RECIPE_CANDIDATE_FIELDS,
        )
    )

    return errors


def validate_optional_candidate_file(path: Path, expected_fields: list[str]) -> list[str]:
    if not path.exists():
        return []
    rows = read_csv(path)
    if not rows:
        return []
    errors: list[str] = []
    if list(rows[0].keys()) != expected_fields:
        errors.append(f"{path.relative_to(ROOT)} header does not match expected schema")
    id_field = expected_fields[0]
    seen: set[str] = set()
    for index, row in enumerate(rows, 2):
        value = row.get(id_field, "")
        if not value:
            errors.append(f"{path.relative_to(ROOT)} row {index}: missing {id_field}")
        if value in seen:
            errors.append(f"{path.relative_to(ROOT)} row {index}: duplicate {id_field} {value}")
        seen.add(value)
        if row.get("revision") != "rev2":
            errors.append(f"{path.relative_to(ROOT)} row {index}: revision must be rev2")
        if row.get("source_url") and not row["source_url"].startswith(("http://", "https://")):
            errors.append(f"{path.relative_to(ROOT)} row {index}: source_url must be absolute")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print("OK: recipe schema, references, and JSON exports are valid")


if __name__ == "__main__":
    main()
