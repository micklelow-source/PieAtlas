#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", newline="")


def fetch_json(url: str) -> dict[str, object]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "PieAtlas/1.0 research harvest (public-domain recipe catalog)"},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(str(last_error))


def main(manifest_csv: str, rows: str = "25", output_csv: str | None = None) -> None:
    manifest = list(csv.DictReader(open(manifest_csv, newline="", encoding="utf-8")))
    output = Path(output_csv).open("w", newline="", encoding="utf-8") if output_csv else sys.stdout
    out = csv.DictWriter(sys.stdout, fieldnames=[
        "candidate_id","archive_id","query","date","newspaper_title","state","page_url","ocr_url","status"
    ])
    out = csv.DictWriter(output, fieldnames=[
        "candidate_id","archive_id","query","date","newspaper_title","state","page_url","ocr_url","status"
    ])
    seen: set[str] = set()
    try:
        out.writeheader()
        for query in manifest:
            if query["archive_id"] != "chronicling-america":
                continue
            url = query["example_api_url"] + f"&rows={rows}"
            try:
                data = fetch_json(url)
            except Exception as exc:
                print(f"# {query['query']}: {exc}", file=sys.stderr)
                continue
            for item in data.get("items", []):  # type: ignore[union-attr]
                page_url = item.get("url", "")
                candidate_id = item.get("id", page_url)
                if not candidate_id or candidate_id in seen:
                    continue
                seen.add(candidate_id)
                out.writerow({
                    "candidate_id": candidate_id,
                    "archive_id": query["archive_id"],
                    "query": query["query"],
                    "date": item.get("date", ""),
                    "newspaper_title": item.get("title", ""),
                    "state": item.get("state", ""),
                    "page_url": page_url,
                    "ocr_url": page_url + "ocr.txt" if page_url else "",
                    "status": "needs_review"
                })
            time.sleep(0.2)
    finally:
        if output_csv:
            output.close()


if __name__ == "__main__":
    main(
        sys.argv[1],
        sys.argv[2] if len(sys.argv) > 2 else "25",
        sys.argv[3] if len(sys.argv) > 3 else None,
    )
