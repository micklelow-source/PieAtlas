#!/usr/bin/env python3
import csv, re, sys

def norm(s):
    s = (s or "").lower()
    replacements = {
        "pompkin": "pumpkin",
        "pye": "pie",
        "pyes": "pies",
        "pie plant": "rhubarb",
        "pieplant": "rhubarb",
        "shoo fly": "shoofly"
    }
    for a,b in replacements.items():
        s = s.replace(a,b)
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def main(recipe_csv, family_csv):
    recipes = list(csv.DictReader(open(recipe_csv, newline="", encoding="utf-8")))
    families = list(csv.DictReader(open(family_csv, newline="", encoding="utf-8")))
    fmap = []
    for f in families:
        aliases = [f["family_name"]] + [x.strip() for x in f["aliases"].split(";") if x.strip()]
        fmap.append((f["family_id"], [norm(x) for x in aliases]))
    fields = list(recipes[0].keys())
    if "family_id" not in fields:
        fields.append("family_id")
    out = csv.DictWriter(sys.stdout, fieldnames=fields)
    out.writeheader()
    for r in recipes:
        title = norm(r.get("title") or r.get("title_guess"))
        if not r.get("family_id"):
            for fid, aliases in fmap:
                if any(a and a in title for a in aliases):
                    r["family_id"] = fid
                    break
        out.writerow(r)
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
