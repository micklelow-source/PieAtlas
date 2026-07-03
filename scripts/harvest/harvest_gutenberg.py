#!/usr/bin/env python3
import csv, re, sys, urllib.request

TERMS = re.compile(r'\b(pie|pies|pye|pyes|tart|tarts|pastry|paste|mince|mincemeat|crust)\b', re.I)

def text_url(ebook_url):
    m = re.search(r'/ebooks/(\d+)', ebook_url)
    if not m:
        return None
    n = m.group(1)
    return f"https://www.gutenberg.org/files/{n}/{n}-0.txt"

def fetch(url):
    with urllib.request.urlopen(url, timeout=45) as r:
        return r.read().decode("utf-8", errors="replace")

def main(src_csv):
    sources = list(csv.DictReader(open(src_csv, newline="", encoding="utf-8")))
    out = csv.DictWriter(sys.stdout, fieldnames=[
        "candidate_id","source_id","year","title_guess","context","source_url","status"
    ])
    out.writeheader()
    for s in sources:
        if "gutenberg.org" not in s["source_url"]:
            continue
        tu = text_url(s["source_url"])
        if not tu:
            continue
        try:
            lines = fetch(tu).splitlines()
        except Exception:
            continue
        for i,line in enumerate(lines):
            if TERMS.search(line):
                context = "\n".join(lines[max(0,i-2):min(len(lines),i+12)]).strip()
                if len(context) > 80:
                    out.writerow({
                        "candidate_id": f'{s["source_id"]}-{i}',
                        "source_id": s["source_id"],
                        "year": s["year"],
                        "title_guess": line.strip()[:120],
                        "context": context.replace("\n"," ")[:1500],
                        "source_url": s["source_url"],
                        "status": "needs_review"
                    })
if __name__ == "__main__":
    main(sys.argv[1])
