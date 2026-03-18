"""
Build a CSV summary of all occupations from data sources.

Currently reads from html/<slug>.html (BLS format), writes to occupations.csv.
Will be adapted to ingest Eurostat API data (ISCO-08 employment, EUR wages)
and HRDA occupation forecasts for Cyprus.

Usage:
    uv run python make_csv.py
"""

import csv
import json
import os
import re

from bs4 import BeautifulSoup


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def parse_pay(value):
    """Parse '62,350 per year $29.98 per hour' or '$23.33 per hour' into (annual, hourly)."""
    annual = ""
    hourly = ""
    # Find all dollar amounts
    amounts = re.findall(r"\$([\d,]+(?:\.\d+)?)", value)
    if "per year" in value and "per hour" in value and len(amounts) >= 2:
        annual = amounts[0].replace(",", "")
        hourly = amounts[1].replace(",", "")
    elif "per year" in value and amounts:
        annual = amounts[0].replace(",", "")
    elif "per hour" in value and amounts:
        hourly = amounts[0].replace(",", "")
    return annual, hourly


def parse_outlook(value):
    """Parse '9% (Much faster than average)' into (pct, description)."""
    m = re.match(r"(-?\d+)%\s*\((.+)\)", value)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"(-?\d+)%", value)
    if m:
        return m.group(1), ""
    return "", value


def parse_number(value):
    """Strip commas and return a clean number string."""
    cleaned = value.replace(",", "").strip()
    # Handle negative numbers
    if re.match(r"^-?\d+$", cleaned):
        return cleaned
    return value.strip()


def extract_occupation(html_path, occ_meta):
    """Extract one row of data from an HTML file."""
    with open(html_path) as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    row = {
        "title": occ_meta["title"],
        "category": occ_meta["category"],
        "slug": occ_meta["slug"],
        "url": occ_meta["url"],
        "soc_code": "",
        "median_pay_annual": "",
        "median_pay_hourly": "",
        "entry_education": "",
        "work_experience": "",
        "training": "",
        "num_jobs_2024": "",
        "outlook_pct": "",
        "outlook_desc": "",
        "employment_change": "",
        "projected_employment_2034": "",
    }

    # Quick Facts table
    qf_table = soup.find("table", id="quickfacts")
    if qf_table:
        tbody = qf_table.find("tbody")
        if tbody:
            for tr in tbody.find_all("tr"):
                th = tr.find("th")
                td = tr.find("td")
                if not th or not td:
                    continue
                field = clean(th.get_text()).lower()
                value = clean(td.get_text())

                if "median pay" in field:
                    row["median_pay_annual"], row["median_pay_hourly"] = parse_pay(value)
                elif "entry-level education" in field:
                    row["entry_education"] = value
                elif "work experience" in field:
                    row["work_experience"] = value
                elif "on-the-job training" in field:
                    row["training"] = value
                elif "number of jobs" in field:
                    row["num_jobs_2024"] = parse_number(value)
                elif "job outlook" in field:
                    row["outlook_pct"], row["outlook_desc"] = parse_outlook(value)
                elif "employment change" in field:
                    row["employment_change"] = parse_number(value)

    # Projections table (for SOC code and projected employment)
    outlook_table = soup.find("table", id="outlook-table")
    if outlook_table:
        tbody = outlook_table.find("tbody")
        if tbody:
            tr = tbody.find("tr")
            if tr:
                cells = [clean(c.get_text()) for c in tr.find_all(["td", "th"])]
                # cells: [Title, SOC, Emp2024, Emp2034, %change, numchange, ...]
                if len(cells) >= 4:
                    soc = cells[1]
                    if soc != "—":
                        row["soc_code"] = soc
                    row["projected_employment_2034"] = parse_number(cells[3])

    # Impute missing pay: annual <-> hourly using 2080 hours/year
    if row["median_pay_annual"] and not row["median_pay_hourly"]:
        row["median_pay_hourly"] = f"{float(row['median_pay_annual']) / 2080:.2f}"
    elif row["median_pay_hourly"] and not row["median_pay_annual"]:
        row["median_pay_annual"] = str(round(float(row["median_pay_hourly"]) * 2080))

    return row


def main():
    with open("occupations.json") as f:
        occupations = json.load(f)

    fieldnames = [
        "title",
        "category",
        "slug",
        "soc_code",
        "median_pay_annual",
        "median_pay_hourly",
        "entry_education",
        "work_experience",
        "training",
        "num_jobs_2024",
        "projected_employment_2034",
        "outlook_pct",
        "outlook_desc",
        "employment_change",
        "url",
    ]

    rows = []
    missing = 0
    for occ in occupations:
        html_path = f"html/{occ['slug']}.html"
        if not os.path.exists(html_path):
            missing += 1
            continue
        row = extract_occupation(html_path, occ)
        rows.append(row)

    with open("occupations.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to occupations.csv (missing HTML: {missing})")

    # Quick sanity check
    print("\nSample rows:")
    for r in rows[:3]:
        print(f"  {r['title']}: ${r['median_pay_annual']}/yr, {r['num_jobs_2024']} jobs, {r['outlook_pct']}% outlook")


if __name__ == "__main__":
    main()
