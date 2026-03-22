"""
Build occupations_cy.csv from Eurostat data for Cyprus.

Merges the ISCO-08 master occupation list (occupations_cy.json) with
employment and earnings data from Eurostat. Supports both live API
fetching and cached JSON files.

Output fields are in EUR and follow EU statistical classifications.

Usage:
    uv run python make_cy_csv.py                          # fetch from Eurostat API
    uv run python make_cy_csv.py --cached data/eurostat/  # use cached JSON files
    uv run python make_cy_csv.py --output occupations_cy.csv
"""

import argparse
import csv
import json
import os

from eurostat import (
    fetch_earnings_by_occupation,
    fetch_employment_by_occupation,
)

FIELDNAMES = [
    "title",
    "category",
    "slug",
    "isco_code",
    "median_pay_annual_eur",
    "median_pay_hourly_eur",
    "entry_education",
    "employment_thousands",
    "year_employment",
    "year_earnings",
]


def load_occupations(path="occupations_cy.json"):
    """Load the Cyprus master occupation list."""
    with open(path) as f:
        return json.load(f)


def fetch_eurostat_data(geo="CY", client=None):
    """Fetch employment and earnings data from Eurostat API.

    Returns:
        Tuple of (employment_data, earnings_data).
    """
    employment = fetch_employment_by_occupation(geo=geo, client=client)
    earnings = fetch_earnings_by_occupation(geo=geo, client=client)
    return employment, earnings


def load_cached_data(cache_dir):
    """Load previously saved Eurostat data from JSON files.

    Args:
        cache_dir: Directory containing employment.json and earnings.json.

    Returns:
        Tuple of (employment_data, earnings_data).
    """
    emp_path = os.path.join(cache_dir, "employment.json")
    earn_path = os.path.join(cache_dir, "earnings.json")

    with open(emp_path) as f:
        employment = json.load(f)
    with open(earn_path) as f:
        earnings = json.load(f)

    return employment, earnings


def save_cached_data(employment, earnings, cache_dir):
    """Save fetched Eurostat data to JSON files for future use."""
    os.makedirs(cache_dir, exist_ok=True)

    with open(os.path.join(cache_dir, "employment.json"), "w") as f:
        json.dump(employment, f, indent=2)
    with open(os.path.join(cache_dir, "earnings.json"), "w") as f:
        json.dump(earnings, f, indent=2)


def build_csv_rows(occupations, employment, earnings):
    """Build CSV rows by merging occupation list with Eurostat data.

    Each 2-digit ISCO occupation is matched to its parent 1-digit group
    for earnings data (since Eurostat SES only provides 1-digit earnings),
    and to its own 2-digit entry for employment data.

    Args:
        occupations: List from occupations_cy.json.
        employment: Output of fetch_employment_by_occupation().
        earnings: Output of fetch_earnings_by_occupation().

    Returns:
        List of dicts matching FIELDNAMES.
    """
    # Index employment by ISCO code
    emp_by_code = {}
    for row in employment:
        emp_by_code[row["isco_code"]] = row

    # Index earnings by ISCO 1-digit code
    earn_by_code = {}
    for row in earnings:
        earn_by_code[row["isco_code"]] = row

    # Education mapping for ISCO major groups (typical for Cyprus/EU)
    # Based on ISCED 2011 typical requirements per ISCO group
    isco_education = {
        "OC1": "Bachelor's degree or higher",
        "OC2": "Bachelor's degree or higher",
        "OC3": "Short-cycle tertiary / Associate",
        "OC4": "Upper secondary / Vocational",
        "OC5": "Upper secondary / Vocational",
        "OC6": "Upper secondary / Vocational",
        "OC7": "Upper secondary / Vocational",
        "OC8": "Lower secondary or below",
        "OC9": "Lower secondary or below",
        "OC0": "Varies (military)",
    }

    rows = []
    for occ in occupations:
        code = occ["isco_code"]
        parent = occ.get("isco_parent", code[:3])

        # Employment: try exact 2-digit match, fall back to 1-digit
        emp = emp_by_code.get(code, emp_by_code.get(parent, {}))

        # Earnings: always from 1-digit (SES limitation)
        earn = earn_by_code.get(parent, {})

        rows.append(
            {
                "title": occ["title"],
                "category": occ["category"],
                "slug": occ["slug"],
                "isco_code": code,
                "median_pay_annual_eur": round(earn["hourly_earnings_eur"] * 2080)
                if earn.get("hourly_earnings_eur")
                else "",
                "median_pay_hourly_eur": f"{earn['hourly_earnings_eur']:.2f}"
                if earn.get("hourly_earnings_eur")
                else "",
                "entry_education": isco_education.get(parent, ""),
                "employment_thousands": emp.get("employment_thousands", ""),
                "year_employment": emp.get("year", ""),
                "year_earnings": earn.get("year", ""),
            }
        )

    return rows


def main():
    parser = argparse.ArgumentParser(description="Build Cyprus occupations CSV from Eurostat data")
    parser.add_argument("--output", default="occupations_cy.csv", help="Output CSV file")
    parser.add_argument("--occupations", default="occupations_cy.json", help="Master occupation list")
    parser.add_argument("--cached", help="Directory with cached employment.json and earnings.json")
    parser.add_argument("--save-cache", help="Save fetched data to this directory for future use")
    parser.add_argument("--geo", default="CY", help="Country code (default: CY)")
    parser.add_argument("--verbose", action="store_true", help="Print API URLs and debug info")
    args = parser.parse_args()

    # Load master occupation list
    occupations = load_occupations(args.occupations)

    # Get Eurostat data
    if args.cached:
        print(f"Loading cached data from {args.cached}")
        employment, earnings = load_cached_data(args.cached)
    else:
        print(f"Fetching data from Eurostat for {args.geo}...")
        employment, earnings = fetch_eurostat_data(geo=args.geo)

    if not earnings:
        print("WARNING: No earnings data returned from Eurostat.")
        print("  Run 'uv run python diagnose_eurostat.py' to investigate.")

    if args.save_cache:
        save_cached_data(employment, earnings, args.save_cache)
        print(f"Cached data saved to {args.save_cache}/")

    # Build CSV rows
    rows = build_csv_rows(occupations, employment, earnings)

    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")

    # Summary
    with_emp = sum(1 for r in rows if r["employment_thousands"])
    with_pay = sum(1 for r in rows if r["median_pay_annual_eur"])
    print(f"  With employment data: {with_emp}/{len(rows)}")
    print(f"  With earnings data: {with_pay}/{len(rows)}")

    if rows:
        print("\nSample rows:")
        for r in rows[:3]:
            pay = f"€{r['median_pay_annual_eur']}" if r["median_pay_annual_eur"] else "—"
            emp = f"{r['employment_thousands']}K" if r["employment_thousands"] else "—"
            print(f"  {r['title']}: {pay}/yr, {emp} employed")


if __name__ == "__main__":
    main()
