#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
recipes = list(csv.DictReader(open(ROOT/"data/recipes/recipes.csv", newline="", encoding="utf-8")))
families = list(csv.DictReader(open(ROOT/"data/families/recipe_families.csv", newline="", encoding="utf-8")))
family_ids = {f["family_id"] for f in families}
ids = set()
errors = []
for i, r in enumerate(recipes, 2):
    if not r["recipe_id"]:
        errors.append(f"row {i}: missing recipe_id")
    if r["recipe_id"] in ids:
        errors.append(f"row {i}: duplicate recipe_id {r['recipe_id']}")
    ids.add(r["recipe_id"])
    if r["family_id"] and r["family_id"] not in family_ids:
        errors.append(f"row {i}: unknown family_id {r['family_id']}")
    if not str(r["year"]).isdigit():
        errors.append(f"row {i}: bad year {r['year']}")
if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print(f"OK: {len(recipes)} recipes")
