"""
Generate prompt.md — a single file containing all project data, designed to be
copy-pasted into an LLM for analysis and conversation about AI exposure of the
US job market.

Usage:
    uv run python make_prompt.py
"""

import csv
import json
import os


def fmt_pay(pay):
    if pay is None:
        return "?"
    return f"${pay:,}"


def fmt_jobs(jobs):
    if jobs is None:
        return "?"
    if jobs >= 1_000_000:
        return f"{jobs / 1e6:.1f}M"
    if jobs >= 1_000:
        return f"{jobs / 1e3:.0f}K"
    return str(jobs)


def main():
    # Load all data sources
    with open("occupations.json") as f:
        occupations = json.load(f)

    with open("occupations.csv") as f:
        csv_rows = {row["slug"]: row for row in csv.DictReader(f)}

    with open("scores.json") as f:
        scores = {s["slug"]: s for s in json.load(f)}

    scores_adv = {}
    if os.path.exists("scores_advantage.json"):
        with open("scores_advantage.json") as f:
            scores_adv = {s["slug"]: s for s in json.load(f)}

    scores_gro = {}
    if os.path.exists("scores_growth.json"):
        with open("scores_growth.json") as f:
            scores_gro = {s["slug"]: s for s in json.load(f)}

    # Merge into unified records
    records = []
    for occ in occupations:
        slug = occ["slug"]
        row = csv_rows.get(slug, {})
        score = scores.get(slug, {})
        adv = scores_adv.get(slug, {})
        gro = scores_gro.get(slug, {})
        pay = int(row["median_pay_annual"]) if row.get("median_pay_annual") else None
        jobs = int(row["num_jobs_2024"]) if row.get("num_jobs_2024") else None
        advantage = adv.get("advantage")
        growth = gro.get("growth")
        opportunity = round((advantage + growth) / 2, 1) if advantage is not None and growth is not None else None
        records.append({
            "title": occ["title"],
            "slug": slug,
            "category": row.get("category", occ.get("category", "")),
            "pay": pay,
            "jobs": jobs,
            "outlook_pct": int(row["outlook_pct"]) if row.get("outlook_pct") else None,
            "outlook_desc": row.get("outlook_desc", ""),
            "education": row.get("entry_education", ""),
            "exposure": score.get("exposure"),
            "rationale": score.get("rationale", ""),
            "advantage": advantage,
            "advantage_rationale": adv.get("rationale", ""),
            "growth": growth,
            "growth_rationale": gro.get("rationale", ""),
            "opportunity": opportunity,
            "url": occ.get("url", ""),
        })

    # Sort by exposure desc, then jobs desc
    records.sort(key=lambda r: (-(r["exposure"] or 0), -(r["jobs"] or 0)))

    lines = []

    # ── Header ──
    lines.append("# AI Exposure of the US Job Market")
    lines.append("")
    lines.append("This document contains structured data on 342 US occupations from the Bureau of Labor Statistics Occupational Outlook Handbook, each scored for AI exposure on a 0-10 scale by an LLM (Gemini Flash). Use this data to analyze, question, and discuss how AI will reshape the US labor market.")
    lines.append("")
    lines.append("Live visualization: https://karpathy.ai/jobs/")
    lines.append("GitHub: https://github.com/karpathy/jobs")
    lines.append("")

    # ── Scoring methodology ──
    lines.append("## Scoring methodology")
    lines.append("")
    lines.append("Each occupation was scored on a single AI Exposure axis from 0 to 10, measuring how much AI will reshape that occupation. The score considers both direct automation (AI doing the work) and indirect effects (AI making workers so productive that fewer are needed).")
    lines.append("")
    lines.append("A key heuristic: if the job can be done entirely from a home office on a computer — writing, coding, analyzing, communicating — then AI exposure is inherently high (7+), because AI capabilities in digital domains are advancing rapidly. Conversely, jobs requiring physical presence, manual skill, or real-time human interaction have a natural barrier.")
    lines.append("")
    lines.append("Calibration anchors:")
    lines.append("- 0-1 Minimal: roofers, janitors, construction laborers")
    lines.append("- 2-3 Low: electricians, plumbers, firefighters, dental hygienists")
    lines.append("- 4-5 Moderate: registered nurses, police officers, veterinarians")
    lines.append("- 6-7 High: teachers, managers, accountants, journalists")
    lines.append("- 8-9 Very high: software developers, graphic designers, translators, paralegals")
    lines.append("- 10 Maximum: data entry clerks, telemarketers")
    lines.append("")

    # ── Aggregate statistics ──
    lines.append("## Aggregate statistics")
    lines.append("")

    total_jobs = sum(r["jobs"] or 0 for r in records)
    total_wages = sum((r["jobs"] or 0) * (r["pay"] or 0) for r in records)

    # Weighted avg exposure
    w_sum = sum((r["exposure"] or 0) * (r["jobs"] or 0) for r in records if r["exposure"] is not None and r["jobs"])
    w_count = sum(r["jobs"] or 0 for r in records if r["exposure"] is not None and r["jobs"])
    w_avg = w_sum / w_count if w_count else 0

    lines.append(f"- Total occupations: {len(records)}")
    lines.append(f"- Total jobs: {total_jobs:,} ({total_jobs/1e6:.0f}M)")
    lines.append(f"- Total annual wages: ${total_wages/1e12:.1f}T")
    lines.append(f"- Job-weighted average AI exposure: {w_avg:.1f}/10")
    lines.append("")

    # Tier breakdown
    tiers = [
        ("Minimal (0-1)", 0, 1),
        ("Low (2-3)", 2, 3),
        ("Moderate (4-5)", 4, 5),
        ("High (6-7)", 6, 7),
        ("Very high (8-10)", 8, 10),
    ]
    lines.append("### Breakdown by exposure tier")
    lines.append("")
    lines.append("| Tier | Occupations | Jobs | % of jobs | Wages | % of wages | Avg pay |")
    lines.append("|------|-------------|------|-----------|-------|------------|---------|")
    for name, lo, hi in tiers:
        group = [r for r in records if r["exposure"] is not None and lo <= r["exposure"] <= hi]
        jobs = sum(r["jobs"] or 0 for r in group)
        wages = sum((r["jobs"] or 0) * (r["pay"] or 0) for r in group)
        avg_pay = wages / jobs if jobs else 0
        lines.append(f"| {name} | {len(group)} | {fmt_jobs(jobs)} | {jobs/total_jobs*100:.1f}% | ${wages/1e12:.1f}T | {wages/total_wages*100:.1f}% | {fmt_pay(int(avg_pay))} |")
    lines.append("")

    # By pay band
    lines.append("### Average exposure by pay band (job-weighted)")
    lines.append("")
    pay_bands = [
        ("<$35K", 0, 35000),
        ("$35-50K", 35000, 50000),
        ("$50-75K", 50000, 75000),
        ("$75-100K", 75000, 100000),
        ("$100K+", 100000, float("inf")),
    ]
    lines.append("| Pay band | Avg exposure | Jobs |")
    lines.append("|----------|-------------|------|")
    for name, lo, hi in pay_bands:
        group = [r for r in records if r["pay"] and lo <= r["pay"] < hi and r["exposure"] is not None and r["jobs"]]
        if group:
            ws = sum(r["exposure"] * r["jobs"] for r in group)
            wc = sum(r["jobs"] for r in group)
            lines.append(f"| {name} | {ws/wc:.1f} | {fmt_jobs(wc)} |")
    lines.append("")

    # By education
    lines.append("### Average exposure by education level (job-weighted)")
    lines.append("")
    edu_groups = [
        ("No degree / HS diploma", ["No formal educational credential", "High school diploma or equivalent"]),
        ("Postsecondary / Associate's", ["Postsecondary nondegree award", "Some college, no degree", "Associate's degree"]),
        ("Bachelor's", ["Bachelor's degree"]),
        ("Master's", ["Master's degree"]),
        ("Doctoral / Professional", ["Doctoral or professional degree"]),
    ]
    lines.append("| Education | Avg exposure | Jobs |")
    lines.append("|-----------|-------------|------|")
    for name, matches in edu_groups:
        group = [r for r in records if r["education"] in matches and r["exposure"] is not None and r["jobs"]]
        if group:
            ws = sum(r["exposure"] * r["jobs"] for r in group)
            wc = sum(r["jobs"] for r in group)
            lines.append(f"| {name} | {ws/wc:.1f} | {fmt_jobs(wc)} |")
    lines.append("")

    # BLS outlook vs exposure
    lines.append("### BLS-projected declining occupations")
    lines.append("")
    declining = [r for r in records if r["outlook_pct"] is not None and r["outlook_pct"] < 0]
    declining.sort(key=lambda r: r["outlook_pct"])
    lines.append("| Occupation | Exposure | Outlook | Jobs |")
    lines.append("|-----------|----------|---------|------|")
    for r in declining:
        lines.append(f"| {r['title']} | {r['exposure']}/10 | {r['outlook_pct']:+d}% | {fmt_jobs(r['jobs'])} |")
    lines.append("")

    lines.append("### Fastest-growing occupations (10%+ projected growth)")
    lines.append("")
    growing = [r for r in records if r["outlook_pct"] is not None and r["outlook_pct"] >= 10]
    growing.sort(key=lambda r: -r["outlook_pct"])
    lines.append("| Occupation | Exposure | Outlook | Jobs |")
    lines.append("|-----------|----------|---------|------|")
    for r in growing:
        lines.append(f"| {r['title']} | {r['exposure']}/10 | +{r['outlook_pct']}% | {fmt_jobs(r['jobs'])} |")
    lines.append("")

    # ── Full occupation table ──
    lines.append("## All 342 occupations")
    lines.append("")
    lines.append("Sorted by AI exposure (descending), then by number of jobs (descending).")
    lines.append("")

    has_opp = any(r["advantage"] is not None for r in records)

    for score in range(10, -1, -1):
        group = [r for r in records if r["exposure"] == score]
        if not group:
            continue
        group_jobs = sum(r["jobs"] or 0 for r in group)
        lines.append(f"### Exposure {score}/10 ({len(group)} occupations, {fmt_jobs(group_jobs)} jobs)")
        lines.append("")
        if has_opp:
            lines.append("| # | Occupation | Pay | Jobs | Outlook | Education | Exposure | Advantage | Growth | Opportunity | Rationale |")
            lines.append("|---|-----------|-----|------|---------|-----------|----------|-----------|--------|-------------|-----------|")
        else:
            lines.append("| # | Occupation | Pay | Jobs | Outlook | Education | Rationale |")
            lines.append("|---|-----------|-----|------|---------|-----------|-----------|")
        for i, r in enumerate(group, 1):
            outlook = f"{r['outlook_pct']:+d}%" if r["outlook_pct"] is not None else "?"
            edu = r["education"] if r["education"] else "?"
            # Truncate education for readability
            edu_short = {
                "High school diploma or equivalent": "HS diploma",
                "Bachelor's degree": "Bachelor's",
                "Master's degree": "Master's",
                "Doctoral or professional degree": "Doctoral",
                "Associate's degree": "Associate's",
                "Postsecondary nondegree award": "Postsecondary",
                "No formal educational credential": "No formal",
                "Some college, no degree": "Some college",
                "See How to Become One": "Varies",
            }.get(edu, edu)
            rationale = r["rationale"].replace("|", "/").replace("\n", " ")
            if has_opp:
                adv_s = str(r["advantage"]) if r["advantage"] is not None else "?"
                gro_s = str(r["growth"]) if r["growth"] is not None else "?"
                opp_s = str(r["opportunity"]) if r["opportunity"] is not None else "?"
                lines.append(f"| {i} | {r['title']} | {fmt_pay(r['pay'])} | {fmt_jobs(r['jobs'])} | {outlook} | {edu_short} | {score}/10 | {adv_s}/10 | {gro_s}/10 | {opp_s}/10 | {rationale} |")
            else:
                lines.append(f"| {i} | {r['title']} | {fmt_pay(r['pay'])} | {fmt_jobs(r['jobs'])} | {outlook} | {edu_short} | {rationale} |")
        lines.append("")

    # Write
    text = "\n".join(lines)
    with open("prompt.md", "w") as f:
        f.write(text)

    print(f"Wrote prompt.md ({len(text):,} chars, {len(lines):,} lines)")


if __name__ == "__main__":
    main()
