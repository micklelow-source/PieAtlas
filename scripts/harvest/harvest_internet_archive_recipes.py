#!/usr/bin/env python3
"""Extract Rev2 recipe candidates from Internet Archive issue OCR text."""

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
TERMS = re.compile(
    r"\b(pie|pies|pye|pyes|tart|tarts|pastry|paste|mince|mincemeat|crust|"
    r"filling|meringue|shortening)\b",
    re.IGNORECASE,
)
ACTION_TERMS = re.compile(r"\b(bake|mix|stir|add|roll|line|fill|cook|beat|serve|make|take)\b", re.IGNORECASE)
NOISE_TERMS = re.compile(r"\b(mud pies|pie chart|pie charts|pie in the sky)\b", re.IGNORECASE)


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


def fetch_text(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=75) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(str(last_error))


def text_file_url(issue_id: str) -> str | None:
    metadata_url = f"https://archive.org/metadata/{urllib.parse.quote(issue_id)}"
    data = fetch_json(metadata_url)
    files = data.get("files", [])
    if not isinstance(files, list):
        return None
    candidates: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        fmt = str(item.get("format", "")).lower()
        if name.endswith("_djvu.txt") or fmt in {"text", "djvutxt"}:
            candidates.append(name)
    if not candidates:
        return None
    return f"https://archive.org/download/{urllib.parse.quote(issue_id)}/{urllib.parse.quote(candidates[0])}"


def candidate_rows(issue: dict[str, str], per_issue_limit: int) -> list[dict[str, str]]:
    url = text_file_url(issue["issue_id"])
    if not url:
        return []
    lines = fetch_text(url).splitlines()
    rows: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        if not TERMS.search(line):
            continue
        context = " ".join(lines[max(0, index - 3) : min(len(lines), index + 14)])
        context = re.sub(r"\s+", " ", context).strip()
        action_count = len(ACTION_TERMS.findall(context))
        if len(context) < 140 or action_count < 2 or NOISE_TERMS.search(context):
            continue
        rows.append(
            {
                "candidate_id": f"{issue['issue_id']}-{index}",
                "issue_id": issue["issue_id"],
                "source_group_id": issue["source_group_id"],
                "revision": "rev2",
                "year": issue["year"],
                "title_guess": line.strip()[:140],
                "context": context[:1800],
                "source_url": issue["source_url"],
                "ocr_text_url": url,
                "status": "needs_review",
            }
        )
        if len(rows) >= per_issue_limit:
            break
    return rows


def main() -> None:
    issues_path = ROOT / "data" / "magazines" / "rev2_issue_candidates.csv"
    per_issue_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    max_issues = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    offset = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    issues = list(csv.DictReader(issues_path.open(newline="", encoding="utf-8-sig")))
    if offset:
        issues = issues[offset:]
    if max_issues:
        issues = issues[:max_issues]
    output = output_path.open("w", newline="", encoding="utf-8") if output_path else sys.stdout
    out = csv.DictWriter(
        output,
        fieldnames=[
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
        ],
    )
    try:
        out.writeheader()
        for issue in issues:
            try:
                rows = candidate_rows(issue, per_issue_limit)
            except Exception as exc:
                print(f"# {issue['issue_id']}: {exc}", file=sys.stderr)
                continue
            out.writerows(rows)
    finally:
        if output_path:
            output.close()


if __name__ == "__main__":
    main()
