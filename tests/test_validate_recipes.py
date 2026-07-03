from __future__ import annotations

import unittest

import csv
from pathlib import Path

from scripts.validate.validate_recipes import (
    RECIPE_FIELDS,
    REV2_ISSUE_FIELDS,
    REV2_RECIPE_CANDIDATE_FIELDS,
    ROOT,
    validate,
)


class RecipeValidationTests(unittest.TestCase):
    def test_current_dataset_is_valid(self) -> None:
        self.assertEqual(validate(), [])

    def test_schema_contains_project_spec_fields(self) -> None:
        for field in [
            "recipe_id",
            "original_title",
            "original_text",
            "ingredients_original",
            "directions_original",
            "ingredients_modernized",
            "directions_modernized",
            "region",
        ]:
            self.assertIn(field, RECIPE_FIELDS)

    def test_rev1_has_500_source_text_verified_records(self) -> None:
        path = Path(ROOT) / "data" / "recipes" / "recipes.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        rev1_rows = [row for row in rows if row["revision"] == "rev1"]
        self.assertEqual(len(rev1_rows), 500)
        self.assertTrue(all(row["verification_status"] == "rev1_source_text_verified" for row in rev1_rows))

    def test_rev2_has_1500_source_text_verified_records(self) -> None:
        path = Path(ROOT) / "data" / "recipes" / "recipes.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        rev2_rows = [row for row in rows if row["revision"] == "rev2"]
        self.assertEqual(len(rev2_rows), 1500)
        self.assertTrue(all(row["verification_status"] == "rev2_source_text_verified" for row in rev2_rows))

    def test_rev3_and_rev4_complete_total_targets(self) -> None:
        path = Path(ROOT) / "data" / "recipes" / "recipes.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        rev3_rows = [row for row in rows if row["revision"] == "rev3"]
        rev4_rows = [row for row in rows if row["revision"] == "rev4"]
        self.assertEqual(len(rows), 10000)
        self.assertEqual(len(rev3_rows), 3000)
        self.assertEqual(len(rev4_rows), 5000)
        self.assertTrue(all(row["verification_status"] == "rev3_newspaper_index_verified" for row in rev3_rows))
        self.assertTrue(all(row["verification_status"] == "rev4_source_manifest_verified" for row in rev4_rows))

    def test_rev2_candidate_schemas_are_declared(self) -> None:
        self.assertIn("issue_id", REV2_ISSUE_FIELDS)
        self.assertIn("ocr_text_url", REV2_RECIPE_CANDIDATE_FIELDS)


if __name__ == "__main__":
    unittest.main()
