"""
Build a compact JSON for the website by merging CSV stats with AI exposure scores.

Reads occupations.csv (Cyprus occupation stats in EUR) and scores.json
(AI exposure ratings). Writes site/data.json for the treemap visualization.

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
        data.append(
            {
                "title": row["title"],
                "slug": slug,
                "category": row["category"],
                "pay": int(row["median_pay_annual"]) if row["median_pay_annual"] else None,
                "jobs": int(row["num_jobs_2024"]) if row["num_jobs_2024"] else None,
                "outlook": int(row["outlook_pct"]) if row["outlook_pct"] else None,
                "outlook_desc": row["outlook_desc"],
                "education": row["entry_education"],
                "exposure": score.get("exposure"),
                "exposure_rationale": score.get("rationale"),
                "url": row.get("url", ""),
            }
        )

    import os

    os.makedirs("site", exist_ok=True)
    with open("site/data.json", "w") as f:
        json.dump(data, f)

    print(f"Wrote {len(data)} occupations to site/data.json")
    total_jobs = sum(d["jobs"] for d in data if d["jobs"])
    print(f"Total jobs represented: {total_jobs:,}")


if __name__ == "__main__":
    main()
