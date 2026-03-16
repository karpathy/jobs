"""
Build a CSV summary of all occupations from the scraped HTML files.

Reads from html/<slug>.html, writes to occupations.csv.
Adapted for Jobs and Skills Australia occupation profiles (ANZSCO classification).

Usage:
    uv run python make_csv.py
"""

import csv
import json
import os
import re
from bs4 import BeautifulSoup


def clean(text):
    return re.sub(r'\s+', ' ', text).strip()


def parse_earnings(text):
    """Parse Australian weekly earnings like '$1,889' or '$1,889 per week' into weekly amount."""
    m = re.search(r'\$([\d,]+)', text)
    if m:
        return m.group(1).replace(",", "")
    return ""


def parse_employment(text):
    """Parse employment numbers, handling commas and thousands."""
    cleaned = re.sub(r'[^\d.]', '', text.replace(",", ""))
    # Handle numbers like "234.5" (thousands)
    if "." in cleaned:
        try:
            return str(int(float(cleaned) * 1000))
        except ValueError:
            pass
    if cleaned.isdigit():
        return cleaned
    return text.strip()


def parse_growth(text):
    """Parse growth percentage like '+5.2%' or '-2.1%'."""
    m = re.search(r'([+-]?\d+\.?\d*)%', text)
    if m:
        return m.group(1)
    return ""


def extract_occupation(html_path, occ_meta):
    """Extract one row of data from a JSA HTML file."""
    with open(html_path) as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    row = {
        "title": occ_meta["title"],
        "category": occ_meta["category"],
        "slug": occ_meta["slug"],
        "url": occ_meta["url"],
        "anzsco_code": occ_meta.get("anzsco_code", ""),
        "median_weekly_earnings": "",
        "median_pay_annual": "",
        "employment_level": "",
        "employment_growth_pct": "",
        "employment_growth_desc": "",
        "future_growth_5yr_pct": "",
        "education_level": "",
        "pct_female": "",
        "pct_part_time": "",
        "median_age": "",
        "skill_level": occ_meta.get("skill_level", ""),
    }

    text = soup.get_text()

    # --- Extract median weekly earnings ---
    # Look for patterns like "$1,889 per week" or "Median weekly earnings: $1,889"
    earnings_match = re.search(r'(?:median\s+(?:weekly\s+)?(?:full-time\s+)?earnings?|earn[s]?\s+around)\s*\$?([\d,]+)\s*(?:per\s*week)?', text, re.I)
    if earnings_match:
        weekly = earnings_match.group(1).replace(",", "")
        row["median_weekly_earnings"] = weekly
        # Convert weekly to annual (52 weeks)
        try:
            row["median_pay_annual"] = str(int(weekly) * 52)
        except ValueError:
            pass

    # Also try to find standalone dollar amounts near "earnings" or "per week"
    if not row["median_weekly_earnings"]:
        pw_match = re.search(r'\$([\d,]+)\s*per\s*week', text, re.I)
        if pw_match:
            weekly = pw_match.group(1).replace(",", "")
            row["median_weekly_earnings"] = weekly
            try:
                row["median_pay_annual"] = str(int(weekly) * 52)
            except ValueError:
                pass

    # Try annual salary pattern
    if not row["median_pay_annual"]:
        annual_match = re.search(r'\$([\d,]+)\s*per\s*(?:year|annum)', text, re.I)
        if annual_match:
            annual = annual_match.group(1).replace(",", "")
            row["median_pay_annual"] = annual

    # --- Extract employment level ---
    emp_match = re.search(r'(?:employment\s+(?:level|size)|(?:number\s+of\s+)?(?:people\s+)?employed)\s*[:\s]*([\d,]+(?:\.\d+)?(?:\s*(?:thousand|million))?)', text, re.I)
    if emp_match:
        val = emp_match.group(1).strip()
        if 'thousand' in val.lower():
            val = str(int(float(re.sub(r'[^\d.]', '', val)) * 1000))
        elif 'million' in val.lower():
            val = str(int(float(re.sub(r'[^\d.]', '', val)) * 1000000))
        else:
            val = val.replace(",", "")
        row["employment_level"] = val

    # --- Extract employment growth ---
    growth_match = re.search(r'(?:employment\s+growth|grew|growth\s+rate)\s*[:\s]*([+-]?\d+\.?\d*)\s*%', text, re.I)
    if growth_match:
        row["employment_growth_pct"] = growth_match.group(1)

    # --- Extract future growth / projections ---
    future_match = re.search(r'(?:projected?\s+(?:to\s+)?(?:grow|growth|change)|future\s+growth)\s*[:\s]*([+-]?\d+\.?\d*)\s*%', text, re.I)
    if future_match:
        row["future_growth_5yr_pct"] = future_match.group(1)

    # Classify growth description
    if row["employment_growth_pct"] or row["future_growth_5yr_pct"]:
        pct_str = row["future_growth_5yr_pct"] or row["employment_growth_pct"]
        try:
            pct = float(pct_str)
            if pct < 0:
                row["employment_growth_desc"] = "Declining"
            elif pct < 3:
                row["employment_growth_desc"] = "Slow growth"
            elif pct < 7:
                row["employment_growth_desc"] = "Moderate growth"
            elif pct < 15:
                row["employment_growth_desc"] = "Strong growth"
            else:
                row["employment_growth_desc"] = "Very strong growth"
        except ValueError:
            pass

    # --- Extract demographics ---
    female_match = re.search(r'(\d+\.?\d*)\s*%\s*(?:are\s+)?female', text, re.I)
    if female_match:
        row["pct_female"] = female_match.group(1)

    pt_match = re.search(r'(\d+\.?\d*)\s*%\s*(?:work\s+)?part[- ]time', text, re.I)
    if pt_match:
        row["pct_part_time"] = pt_match.group(1)

    age_match = re.search(r'median\s+age\s*(?:is|of)?\s*(\d+)', text, re.I)
    if age_match:
        row["median_age"] = age_match.group(1)

    # --- Extract education level ---
    # Look for common Australian qualification levels
    edu_patterns = [
        (r'(?:bachelor|university)\s+degree', "Bachelor degree"),
        (r'doctoral\s+degree|phd', "Doctoral degree"),
        (r"master'?s?\s+degree", "Master degree"),
        (r'graduate\s+diploma', "Graduate diploma"),
        (r'advanced\s+diploma', "Advanced diploma"),
        (r'diploma', "Diploma"),
        (r'certificate\s+iv|cert\s*iv', "Certificate IV"),
        (r'certificate\s+iii|cert\s*iii', "Certificate III"),
        (r'certificate\s+ii|cert\s*ii', "Certificate II"),
        (r'certificate\s+i|cert\s*i', "Certificate I"),
        (r'year\s+12|secondary\s+school', "Year 12"),
        (r'year\s+10', "Year 10"),
        (r'no\s+(?:formal\s+)?(?:educational?\s+)?(?:qualification|credential)', "No formal qualification"),
    ]

    for pattern, label in edu_patterns:
        if re.search(pattern, text, re.I):
            row["education_level"] = label
            break

    # --- Extract from structured data/tables ---
    # Look for key-value pairs in tables or definition lists
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) >= 2:
                field = clean(cells[0].get_text()).lower()
                value = clean(cells[1].get_text())

                if "earnings" in field or "pay" in field or "wage" in field:
                    weekly_val = parse_earnings(value)
                    if weekly_val:
                        row["median_weekly_earnings"] = weekly_val
                        try:
                            row["median_pay_annual"] = str(int(weekly_val) * 52)
                        except ValueError:
                            pass
                elif "employment" in field and "level" in field:
                    row["employment_level"] = parse_employment(value)
                elif "growth" in field:
                    row["employment_growth_pct"] = parse_growth(value)
                elif "education" in field or "qualification" in field:
                    row["education_level"] = value
                elif "female" in field or "gender" in field:
                    m = re.search(r'(\d+\.?\d*)\s*%?', value)
                    if m:
                        row["pct_female"] = m.group(1)

    # Look in definition lists
    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            field = clean(dt.get_text()).lower()
            value = clean(dd.get_text())

            if "earnings" in field:
                weekly_val = parse_earnings(value)
                if weekly_val:
                    row["median_weekly_earnings"] = weekly_val
                    try:
                        row["median_pay_annual"] = str(int(weekly_val) * 52)
                    except ValueError:
                        pass
            elif "employed" in field or "employment" in field:
                row["employment_level"] = parse_employment(value)

    return row


def main():
    with open("occupations.json") as f:
        occupations = json.load(f)

    fieldnames = [
        "title", "category", "slug", "anzsco_code",
        "median_weekly_earnings", "median_pay_annual",
        "education_level", "skill_level",
        "employment_level", "employment_growth_pct",
        "employment_growth_desc", "future_growth_5yr_pct",
        "pct_female", "pct_part_time", "median_age",
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
    print(f"\nSample rows:")
    for r in rows[:3]:
        weekly = r['median_weekly_earnings']
        annual = r['median_pay_annual']
        pay_str = f"${weekly}/wk (${annual}/yr)" if weekly else "no pay data"
        print(f"  {r['title']}: {pay_str}, {r['employment_level']} employed, {r['employment_growth_pct']}% growth")


if __name__ == "__main__":
    main()
