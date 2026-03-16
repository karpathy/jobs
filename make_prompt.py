"""
Generate prompt.md — a single file containing all project data, designed to be
copy-pasted into an LLM for analysis and conversation about AI exposure of the
Australian job market.

Usage:
    uv run python make_prompt.py
"""

import csv
import json


def fmt_pay(pay):
    if pay is None:
        return "?"
    return f"A${pay:,}"


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

    # Merge into unified records
    records = []
    for occ in occupations:
        slug = occ["slug"]
        row = csv_rows.get(slug, {})
        score = scores.get(slug, {})
        pay = int(row["median_pay_annual"]) if row.get("median_pay_annual") else None
        jobs = int(row["employment_level"]) if row.get("employment_level") else None
        outlook_str = row.get("future_growth_5yr_pct") or row.get("employment_growth_pct") or ""
        outlook_pct = None
        if outlook_str:
            try:
                outlook_pct = round(float(outlook_str))
            except ValueError:
                pass
        records.append({
            "title": occ["title"],
            "slug": slug,
            "category": row.get("category", occ.get("category", "")),
            "pay": pay,
            "jobs": jobs,
            "outlook_pct": outlook_pct,
            "outlook_desc": row.get("employment_growth_desc", ""),
            "education": row.get("education_level", ""),
            "exposure": score.get("exposure"),
            "rationale": score.get("rationale", ""),
            "url": occ.get("url", ""),
        })

    # Sort by exposure desc, then jobs desc
    records.sort(key=lambda r: (-(r["exposure"] or 0), -(r["jobs"] or 0)))

    lines = []

    # ── Header ──
    lines.append("# AI Exposure of the Australian Job Market")
    lines.append("")
    lines.append("This document contains structured data on Australian occupations from Jobs and Skills Australia (ANZSCO classification), each scored for AI exposure on a 0-10 scale by an LLM (Gemini Flash). Use this data to analyze, question, and discuss how AI will reshape the Australian labour market.")
    lines.append("")

    # ── Scoring methodology ──
    lines.append("## Scoring methodology")
    lines.append("")
    lines.append("Each occupation was scored on a single AI Exposure axis from 0 to 10, measuring how much AI will reshape that occupation. The score considers both direct automation (AI doing the work) and indirect effects (AI making workers so productive that fewer are needed).")
    lines.append("")
    lines.append("A key heuristic: if the job can be done entirely from a home office on a computer — writing, coding, analyzing, communicating — then AI exposure is inherently high (7+), because AI capabilities in digital domains are advancing rapidly. Conversely, jobs requiring physical presence, manual skill, or real-time human interaction have a natural barrier.")
    lines.append("")
    lines.append("Calibration anchors:")
    lines.append("- 0-1 Minimal: roofers, landscape gardeners, construction labourers")
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
    lines.append(f"- Total jobs: {total_jobs:,} ({total_jobs/1e6:.1f}M)")
    lines.append(f"- Total annual wages: A${total_wages/1e9:.1f}B")
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
        pct_jobs = jobs / total_jobs * 100 if total_jobs else 0
        pct_wages = wages / total_wages * 100 if total_wages else 0
        lines.append(f"| {name} | {len(group)} | {fmt_jobs(jobs)} | {pct_jobs:.1f}% | A${wages/1e9:.1f}B | {pct_wages:.1f}% | {fmt_pay(int(avg_pay))} |")
    lines.append("")

    # By pay band (AUD)
    lines.append("### Average exposure by pay band (job-weighted)")
    lines.append("")
    pay_bands = [
        ("<A$50K", 0, 50000),
        ("A$50-75K", 50000, 75000),
        ("A$75-100K", 75000, 100000),
        ("A$100-130K", 100000, 130000),
        ("A$130K+", 130000, float("inf")),
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
        ("No formal / Year 10-12", ["No formal qualification", "Year 10", "Year 12"]),
        ("Certificate I-IV", ["Certificate I", "Certificate II", "Certificate III", "Certificate IV"]),
        ("Diploma / Advanced Diploma", ["Diploma", "Advanced diploma"]),
        ("Bachelor degree", ["Bachelor degree"]),
        ("Postgraduate", ["Graduate diploma", "Master degree", "Doctoral degree"]),
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

    # Declining occupations
    lines.append("### Declining occupations")
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
    lines.append(f"## All {len(records)} occupations")
    lines.append("")
    lines.append("Sorted by AI exposure (descending), then by number of jobs (descending).")
    lines.append("")

    for score_val in range(10, -1, -1):
        group = [r for r in records if r["exposure"] == score_val]
        if not group:
            continue
        group_jobs = sum(r["jobs"] or 0 for r in group)
        lines.append(f"### Exposure {score_val}/10 ({len(group)} occupations, {fmt_jobs(group_jobs)} jobs)")
        lines.append("")
        lines.append("| # | Occupation | Pay | Jobs | Outlook | Education | Rationale |")
        lines.append("|---|-----------|-----|------|---------|-----------|-----------|")
        for i, r in enumerate(group, 1):
            outlook = f"{r['outlook_pct']:+d}%" if r["outlook_pct"] is not None else "?"
            edu = r["education"] if r["education"] else "?"
            rationale = r["rationale"].replace("|", "/").replace("\n", " ")
            lines.append(f"| {i} | {r['title']} | {fmt_pay(r['pay'])} | {fmt_jobs(r['jobs'])} | {outlook} | {edu} | {rationale} |")
        lines.append("")

    # Write
    text = "\n".join(lines)
    with open("prompt.md", "w") as f:
        f.write(text)

    print(f"Wrote prompt.md ({len(text):,} chars, {len(lines):,} lines)")


if __name__ == "__main__":
    main()
