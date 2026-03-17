"""
Build a compact JSON for the website by merging CSV stats with AI scores.

Reads occupations.csv (for stats), scores.json (for AI exposure), and
optionally scores_advantage.json and scores_growth.json for the opportunity
layers. Writes site/data.json.

Usage:
    uv run python build_site_data.py
"""

import csv
import json
import os


def load_scores(path):
    """Load a scores JSON file, returning a slug-keyed dict (empty if missing)."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return {s["slug"]: s for s in json.load(f)}


def main():
    # Load all score files
    scores = load_scores("scores.json")
    scores_adv = load_scores("scores_advantage.json")
    scores_gro = load_scores("scores_growth.json")

    # Load CSV stats
    with open("occupations.csv") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Merge
    data = []
    for row in rows:
        slug = row["slug"]
        score = scores.get(slug, {})
        adv = scores_adv.get(slug, {})
        gro = scores_gro.get(slug, {})

        advantage = adv.get("advantage")
        growth = gro.get("growth")
        opportunity = None
        if advantage is not None and growth is not None:
            opportunity = round((advantage + growth) / 2, 1)

        data.append({
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
            "advantage": advantage,
            "advantage_rationale": adv.get("rationale"),
            "growth": growth,
            "growth_rationale": gro.get("rationale"),
            "opportunity": opportunity,
            "url": row.get("url", ""),
        })

    os.makedirs("site", exist_ok=True)
    with open("site/data.json", "w") as f:
        json.dump(data, f)

    print(f"Wrote {len(data)} occupations to site/data.json")
    total_jobs = sum(d["jobs"] for d in data if d["jobs"])
    print(f"Total jobs represented: {total_jobs:,}")

    # Report which layers have data
    for label, key in [("exposure", "exposure"), ("advantage", "advantage"),
                       ("growth", "growth"), ("opportunity", "opportunity")]:
        count = sum(1 for d in data if d[key] is not None)
        if count:
            print(f"  {label}: {count} scored")


if __name__ == "__main__":
    main()
