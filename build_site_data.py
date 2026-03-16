"""
Build a compact JSON for the website by merging CSV stats with AI exposure scores.

Reads occupations.csv (for stats) and scores.json (for AI exposure).
Writes site/data.json.

Adapted for Australian occupation data from Jobs and Skills Australia.

Usage:
    uv run python build_site_data.py
"""

import csv
import json


def main():
    # Load AI exposure scores
    with open("scores.json") as f:
        scores_list = json.load(f)
    scores = {s["slug"]: s for s in scores_list}

    # Load CSV stats
    with open("occupations.csv") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Merge
    data = []
    for row in rows:
        slug = row["slug"]
        score = scores.get(slug, {})

        # Pay: use annual (derived from weekly * 52) or direct annual
        pay = int(row["median_pay_annual"]) if row.get("median_pay_annual") else None

        # Jobs: employment level
        jobs = int(row["employment_level"]) if row.get("employment_level") else None

        # Outlook: use future growth or recent growth
        outlook_str = row.get("future_growth_5yr_pct") or row.get("employment_growth_pct") or ""
        outlook = None
        if outlook_str:
            try:
                outlook = round(float(outlook_str))
            except ValueError:
                pass

        data.append({
            "title": row["title"],
            "slug": slug,
            "category": row["category"],
            "pay": pay,
            "jobs": jobs,
            "outlook": outlook,
            "outlook_desc": row.get("employment_growth_desc", ""),
            "education": row.get("education_level", ""),
            "exposure": score.get("exposure"),
            "exposure_rationale": score.get("rationale"),
            "url": row.get("url", ""),
        })

    import os
    os.makedirs("site", exist_ok=True)
    with open("site/data.json", "w") as f:
        json.dump(data, f)

    print(f"Wrote {len(data)} occupations to site/data.json")
    total_jobs = sum(d["jobs"] for d in data if d["jobs"])
    print(f"Total jobs represented: {total_jobs:,}")


if __name__ == "__main__":
    main()
