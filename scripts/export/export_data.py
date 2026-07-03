#!/usr/bin/env python3
"""Export canonical CSV files to JSON for the API and static site."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SITE_DATA = ROOT / "site" / "public" / "data"

INTEGER_FIELDS = {"year", "target_count", "current_count"}


def read_csv(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [normalize_row(row) for row in csv.DictReader(handle)]


def normalize_row(row: dict[str, str]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in row.items():
        clean_value = (value or "").strip()
        if key in INTEGER_FIELDS and clean_value.isdigit():
            normalized[key] = int(clean_value)
        else:
            normalized[key] = clean_value
    return normalized


def write_json(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(list(rows), handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def export_pair(csv_path: Path, json_path: Path) -> None:
    write_json(json_path, read_csv(csv_path))


def main() -> None:
    export_pair(DATA / "recipes" / "recipes.csv", DATA / "recipes" / "recipes.json")
    export_pair(DATA / "families" / "recipe_families.csv", DATA / "families" / "recipe_families.json")
    export_pair(DATA / "roadmap.csv", DATA / "roadmap.json")
    if (DATA / "magazines" / "rev2_issue_candidates.csv").exists():
        export_pair(DATA / "magazines" / "rev2_issue_candidates.csv", DATA / "magazines" / "rev2_issue_candidates.json")
    if (DATA / "magazines" / "rev2_recipe_candidates.csv").exists():
        export_pair(DATA / "magazines" / "rev2_recipe_candidates.csv", DATA / "magazines" / "rev2_recipe_candidates.json")

    SITE_DATA.mkdir(parents=True, exist_ok=True)
    for source in [
        DATA / "recipes" / "recipes.json",
        DATA / "families" / "recipe_families.json",
        DATA / "roadmap.json",
        DATA / "magazines" / "rev2_issue_candidates.json",
        DATA / "magazines" / "rev2_recipe_candidates.json",
    ]:
        if source.exists():
            shutil.copy2(source, SITE_DATA / source.name)


if __name__ == "__main__":
    main()
