#!/usr/bin/env python3
import csv, json, sys, urllib.request, urllib.parse, time

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))

def main(manifest_csv, rows="25"):
    manifest = list(csv.DictReader(open(manifest_csv, newline="", encoding="utf-8")))
    out = csv.DictWriter(sys.stdout, fieldnames=[
        "candidate_id","archive_id","query","date","newspaper_title","state","page_url","ocr_url","status"
    ])
    out.writeheader()
    for q in manifest:
        if q["archive_id"] != "chronicling-america":
            continue
        url = q["example_api_url"] + f"&rows={rows}"
        try:
            data = fetch_json(url)
        except Exception:
            continue
        for item in data.get("items", []):
            page_url = item.get("url", "")
            out.writerow({
                "candidate_id": item.get("id", page_url),
                "archive_id": q["archive_id"],
                "query": q["query"],
                "date": item.get("date", ""),
                "newspaper_title": item.get("title", ""),
                "state": item.get("state", ""),
                "page_url": page_url,
                "ocr_url": page_url + "ocr.txt" if page_url else "",
                "status": "needs_review"
            })
        time.sleep(0.2)
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "25")
