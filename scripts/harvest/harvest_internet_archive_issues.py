#!/usr/bin/env python3
"""Discover public-domain magazine issue candidates from Internet Archive."""

from __future__ import annotations

import csv
import json
import re
import sys
import urllib.parse
import urllib.request
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", newline="")

ROOT = Path(__file__).resolve().parents[2]
IA_ADVANCED_SEARCH = "https://archive.org/advancedsearch.php"
DEFAULT_LIMIT = 25
SOURCE_PHRASES = {
    "american-cookery-magazine": [
        "American Cookery",
        "Boston Cooking-School Magazine",
        "Boston Cooking School Magazine",
    ],
    "good-housekeeping-early": ["Good Housekeeping"],
    "ladies-home-journal-early": ["Ladies' Home Journal", "Ladies Home Journal"],
    "table-talk": ["Table Talk"],
    "delineator": ["The Delineator", "Delineator"],
}


def slug_words(value: str) -> list[str]:
    return [word for word in re.split(r"[^a-z0-9]+", value.lower()) if len(word) > 2]


def query_for(row: dict[str, str]) -> str:
    phrases = SOURCE_PHRASES.get(row["source_id"], [row["title"]])
    quoted = " OR ".join(f'title:"{phrase}" OR description:"{phrase}" OR subject:"{phrase}"' for phrase in phrases)
    return f"mediatype:texts AND year:[1800 TO 1928] AND ({quoted})"


def fetch_json(url: str) -> dict[str, object]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(str(last_error))


def discover(row: dict[str, str], limit: int) -> list[dict[str, str]]:
    params = {
        "q": query_for(row),
        "fl[]": ["identifier", "title", "creator", "year", "date", "publicdate"],
        "rows": str(limit),
        "page": "1",
        "output": "json",
        "sort[]": "year asc",
    }
    url = f"{IA_ADVANCED_SEARCH}?{urllib.parse.urlencode(params, doseq=True)}"
    data = fetch_json(url)
    docs = data.get("response", {}).get("docs", [])  # type: ignore[union-attr]
    rows: list[dict[str, str]] = []
    for doc in docs:
        identifier = str(doc.get("identifier", "")).strip()
        if not identifier:
            continue
        rows.append(
            {
                "issue_id": identifier,
                "source_group_id": row["source_id"],
                "revision": "rev2",
                "title": str(doc.get("title", "")).strip(),
                "creator": str(doc.get("creator", "")).strip(),
                "year": str(doc.get("year") or "").strip(),
                "date": str(doc.get("date") or "").strip(),
                "repository": "Internet Archive",
                "source_url": f"https://archive.org/details/{identifier}",
                "status": "issue_candidate",
            }
        )
    return rows


def main() -> None:
    manifest = ROOT / "data" / "manifests" / "rev2_magazine_targets.csv"
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LIMIT
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    targets = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))
    output = output_path.open("w", newline="", encoding="utf-8") if output_path else sys.stdout
    out = csv.DictWriter(
        output,
        fieldnames=[
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
        ],
    )
    try:
        out.writeheader()
        seen: set[str] = set()
        for target in targets:
            try:
                rows = discover(target, limit)
            except Exception as exc:
                print(f"# {target['source_id']}: {exc}", file=sys.stderr)
                continue
            for row in rows:
                if row["issue_id"] in seen:
                    continue
                seen.add(row["issue_id"])
                out.writerow(row)
    finally:
        if output_path:
            output.close()


if __name__ == "__main__":
    main()
