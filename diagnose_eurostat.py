"""Diagnostic script for Eurostat API issues.

Run from a machine with internet access (e.g. GitHub Codespace):
    uv run python diagnose_eurostat.py

Checks:
    1. Employment data: validates geo filtering and number magnitudes
    2. Earnings data: tests multiple datasets and parameter combinations
"""

import csv
import io
import sys

import httpx

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"


def fetch_csv(dataset, params, client):
    """Fetch SDMX-CSV from Eurostat, return (rows, url)."""
    url = f"{BASE_URL}/{dataset}"
    query = {"format": "SDMX-CSV", **params}
    try:
        resp = client.get(url, params=query)
        print(f"  URL: {resp.url}")
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  Body: {resp.text[:300]}")
            return [], str(resp.url)
        rows = list(csv.DictReader(io.StringIO(resp.text)))
        return rows, str(resp.url)
    except Exception as e:
        print(f"  ERROR: {e}")
        return [], ""


def diagnose_employment(client):
    """Check employment data for CY."""
    print("\n" + "=" * 70)
    print("EMPLOYMENT DIAGNOSTICS (LFSA_EGAI2D)")
    print("=" * 70)

    params = {
        "geo": "CY",
        "sex": "T",
        "age": "Y_GE15",
        "unit": "THS_PER",
        "lastNPeriods": "1",
    }

    rows, url = fetch_csv("LFSA_EGAI2D", params, client)
    print(f"  Rows returned: {len(rows)}")

    if not rows:
        print("  No data returned!")
        return

    # Show first 3 raw rows with ALL columns
    print("\n  Sample raw rows (all columns):")
    for i, row in enumerate(rows[:3]):
        print(f"    Row {i}: {dict(row)}")

    # Check geo column
    geos = {row.get("geo", "?") for row in rows}
    print(f"\n  Unique geo values in response: {geos}")
    if geos != {"CY"}:
        print("  WARNING: Response contains non-CY data! Geo filter may not be working.")

    # Check unit column
    units = {row.get("unit", "?") for row in rows}
    print(f"  Unique unit values: {units}")

    # Sum 2-digit employment
    total = 0.0
    two_digit_rows = []
    for row in rows:
        code = row.get("isco08", "")
        val = row.get("OBS_VALUE", "")
        if len(code) == 4 and val and val != ":":  # 2-digit like OC25
            total += float(val)
            two_digit_rows.append((code, float(val)))

    print(f"\n  Sum of all 2-digit employment values: {total:.1f}")
    if "THS_PER" in units:
        print(f"  Interpreted as thousands: {total * 1000:.0f} people")
        if total > 500:
            print("  WARNING: Total > 500K — too high for Cyprus (~450K workforce)")
            print("  Numbers may be absolute counts, not thousands")
        elif total < 100:
            print("  Numbers seem low for thousands — may actually be in thousands (OK)")
    else:
        print(f"  Unit is {units}, not THS_PER — check if values need conversion")

    # Show some 2-digit values
    print("\n  2-digit employment values:")
    for code, val in sorted(two_digit_rows)[:10]:
        print(f"    {code}: {val}")


def diagnose_earnings(client):
    """Check earnings data for CY across multiple datasets and params."""
    print("\n" + "=" * 70)
    print("EARNINGS DIAGNOSTICS")
    print("=" * 70)

    # Test 1: Current params (what's failing)
    print("\n--- Test 1: earn_ses_pub1s with CURRENT params ---")
    params = {
        "geo": "CY",
        "isco08": "OC0+OC1+OC2+OC3+OC4+OC5+OC6+OC7+OC8+OC9",
        "indic_se": "MEAN_ME_HRS",
        "nace_r2": "B-S",
        "worktime": "TOTAL",
        "lastNPeriods": "1",
    }
    rows, _ = fetch_csv("earn_ses_pub1s", params, client)
    print(f"  Rows: {len(rows)}")
    for row in rows[:3]:
        print(f"    {dict(row)}")

    # Test 2: earn_ses_pub1s with ONLY geo (no other filters)
    print("\n--- Test 2: earn_ses_pub1s with ONLY geo=CY ---")
    rows, _ = fetch_csv("earn_ses_pub1s", {"geo": "CY", "lastNPeriods": "3"}, client)
    print(f"  Rows: {len(rows)}")
    if rows:
        # Show unique dimension values
        keys_of_interest = ["isco08", "indic_se", "nace_r2", "worktime"]
        for key in keys_of_interest:
            vals = {row.get(key, "?") for row in rows}
            print(f"  Available {key} values: {sorted(vals)}")
        print("  Sample rows:")
        for row in rows[:5]:
            print(
                f"    {row.get('isco08', '?')} | {row.get('indic_se', '?')} | "
                f"{row.get('nace_r2', '?')} | {row.get('worktime', '?')} | "
                f"val={row.get('OBS_VALUE', '?')} | {row.get('TIME_PERIOD', '?')}"
            )

    # Test 3: earn_ses_pub1s — try adding filters one at a time
    print("\n--- Test 3: earn_ses_pub1s — adding filters one at a time ---")
    base = {"geo": "CY", "lastNPeriods": "3"}
    filters_to_try = [
        ("isco08", "OC1"),
        ("indic_se", "MEAN_ME_HRS"),
        ("nace_r2", "B-S"),
        ("worktime", "TOTAL"),
    ]
    for key, val in filters_to_try:
        test_params = {**base, key: val}
        rows, _ = fetch_csv("earn_ses_pub1s", test_params, client)
        status = f"{len(rows)} rows" if rows else "EMPTY"
        print(f"  + {key}={val} → {status}")

    # Test 4: earn_ses_pub2s (median hourly earnings)
    print("\n--- Test 4: earn_ses_pub2s with geo=CY ---")
    rows, _ = fetch_csv("earn_ses_pub2s", {"geo": "CY", "lastNPeriods": "3"}, client)
    print(f"  Rows: {len(rows)}")
    if rows:
        keys_of_interest = ["isco08", "indic_se", "nace_r2", "worktime"]
        for key in keys_of_interest:
            vals = {row.get(key, "?") for row in rows}
            print(f"  Available {key} values: {sorted(vals)}")
        print("  Sample rows:")
        for row in rows[:5]:
            print(
                f"    {row.get('isco08', '?')} | {row.get('indic_se', '?')} | "
                f"val={row.get('OBS_VALUE', '?')} | {row.get('TIME_PERIOD', '?')}"
            )

    # Test 5: earn_ses_hourly (alternative dataset)
    print("\n--- Test 5: earn_ses_hourly with geo=CY ---")
    rows, _ = fetch_csv("earn_ses_hourly", {"geo": "CY", "lastNPeriods": "3"}, client)
    print(f"  Rows: {len(rows)}")
    if rows:
        keys_of_interest = ["isco08", "indic_se", "nace_r2", "worktime"]
        for key in keys_of_interest:
            vals = {row.get(key, "?") for row in rows}
            print(f"  Available {key} values: {sorted(vals)}")
        print("  Sample rows:")
        for row in rows[:5]:
            print(
                f"    {row.get('isco08', '?')} | {row.get('indic_se', '?')} | "
                f"val={row.get('OBS_VALUE', '?')} | {row.get('TIME_PERIOD', '?')}"
            )

    # Test 6: Try NACE as explicit list instead of range
    print("\n--- Test 6: earn_ses_pub1s with nace_r2 as explicit list ---")
    nace_explicit = "+".join(["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"])
    params = {"geo": "CY", "isco08": "OC1", "nace_r2": nace_explicit, "lastNPeriods": "3"}
    rows, _ = fetch_csv("earn_ses_pub1s", params, client)
    print(f"  Rows: {len(rows)}")
    for row in rows[:3]:
        print(f"    {dict(row)}")


def main():
    print("Eurostat API Diagnostics")
    print(f"Python: {sys.version}")

    with httpx.Client(timeout=60) as client:
        diagnose_employment(client)
        diagnose_earnings(client)

    print("\n" + "=" * 70)
    print("DONE — paste this output back to Claude for analysis")
    print("=" * 70)


if __name__ == "__main__":
    main()
