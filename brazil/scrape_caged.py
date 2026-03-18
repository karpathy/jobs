"""
Download and aggregate CAGED (Novo CAGED) employment data by CBO family.

Downloads monthly movement files from MTE FTP, aggregates to produce:
- Median salary by CBO family (4-digit)
- Net employment (admissions - terminations) over 12 months
- Total admissions (proxy for demand)
- Breakdown by UF (state) for regional analysis

Usage:
    uv run python brazil/scrape_caged.py                        # last 12 months
    uv run python brazil/scrape_caged.py --months 6             # last 6 months
    uv run python brazil/scrape_caged.py --year 2025 --month 12 # specific month only
    uv run python brazil/scrape_caged.py --skip-download        # aggregate from cached files
"""

import argparse
import csv
import json
import os
import statistics
import subprocess
import tempfile
from collections import defaultdict

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_DIR = "brazil/data"
CAGED_DIR = os.path.join(DATA_DIR, "caged_raw")
FTP_BASE = "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED"


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def download_month(year: int, month: int, force: bool = False) -> str | None:
    """Download and extract a single CAGED month. Returns path to extracted txt."""
    ym = f"{year}{month:02d}"
    archive_name = f"CAGEDMOV{ym}.7z"
    txt_name = f"CAGEDMOV{ym}.txt"

    os.makedirs(CAGED_DIR, exist_ok=True)
    txt_path = os.path.join(CAGED_DIR, txt_name)

    if not force and os.path.exists(txt_path):
        print(f"  CACHED {txt_name}")
        return txt_path

    url = f"{FTP_BASE}/{year}/{ym}/{archive_name}"
    archive_path = os.path.join(CAGED_DIR, archive_name)

    print(f"  Downloading {archive_name}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", archive_path, url],
            timeout=300, capture_output=True
        )
        if result.returncode != 0 or not os.path.exists(archive_path):
            print(f"FAILED (curl returned {result.returncode})")
            return None

        size = os.path.getsize(archive_path)
        if size < 1000:
            print(f"FAILED (file too small: {size} bytes)")
            os.remove(archive_path)
            return None

        print(f"OK ({size:,} bytes)", end=" ", flush=True)

        # Extract
        print("extracting...", end=" ", flush=True)
        result = subprocess.run(
            ["7z", "x", archive_path, f"-o{CAGED_DIR}", "-y"],
            timeout=120, capture_output=True
        )
        if result.returncode != 0:
            print(f"EXTRACT FAILED")
            return None

        # Remove archive to save space
        os.remove(archive_path)

        if os.path.exists(txt_path):
            txt_size = os.path.getsize(txt_path)
            print(f"OK ({txt_size:,} bytes)")
            return txt_path
        else:
            print("EXTRACT FAILED (no txt file)")
            return None

    except Exception as e:
        print(f"ERROR: {e}")
        return None


def download_months(year_start: int, month_start: int, count: int, force: bool) -> list[str]:
    """Download multiple months of CAGED data. Returns list of txt paths."""
    paths = []
    y, m = year_start, month_start
    for _ in range(count):
        path = download_month(y, m, force)
        if path:
            paths.append(path)
        # Go back one month
        m -= 1
        if m < 1:
            m = 12
            y -= 1
    return paths


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
def aggregate_caged(txt_paths: list[str]) -> dict:
    """
    Aggregate CAGED movement files by CBO family (4-digit).

    Returns dict keyed by CBO family code with:
    - salarios: list of all salaries (for median calculation)
    - saldo: net employment change (admissions - terminations)
    - admissoes: total admissions
    - desligamentos: total terminations
    - por_uf: {uf_code: {saldo, admissoes, salarios}}
    """
    by_family = defaultdict(lambda: {
        "salarios": [],
        "saldo": 0,
        "admissoes": 0,
        "desligamentos": 0,
        "por_uf": defaultdict(lambda: {"saldo": 0, "admissoes": 0, "salarios": []}),
    })

    total_rows = 0

    for txt_path in txt_paths:
        filename = os.path.basename(txt_path)
        print(f"  Processing {filename}...", end=" ", flush=True)
        rows = 0

        with open(txt_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                rows += 1
                cbo6 = row.get("cbo2002ocupação", "").strip()
                if not cbo6 or len(cbo6) < 4:
                    continue

                cbo4 = cbo6[:4]  # Family level
                saldo = int(row.get("saldomovimentação", "0"))
                uf = row.get("uf", "").strip()

                # Salary — only for admissions (saldo=1), and only if reasonable
                salario_str = row.get("valorsaláriofixo", "0").replace(",", ".")
                try:
                    salario = float(salario_str)
                except ValueError:
                    salario = 0.0

                fam = by_family[cbo4]
                fam["saldo"] += saldo

                if saldo > 0:
                    fam["admissoes"] += 1
                    if 100 < salario < 500000:  # Filter unreasonable values
                        fam["salarios"].append(salario)
                elif saldo < 0:
                    fam["desligamentos"] += 1

                if uf:
                    uf_data = fam["por_uf"][uf]
                    uf_data["saldo"] += saldo
                    if saldo > 0:
                        uf_data["admissoes"] += 1
                        if 100 < salario < 500000:
                            uf_data["salarios"].append(salario)

        total_rows += rows
        print(f"{rows:,} rows")

    print(f"\n  Total: {total_rows:,} rows across {len(txt_paths)} files")
    print(f"  CBO families with data: {len(by_family)}")

    return dict(by_family)


def build_caged_stats(aggregated: dict) -> list[dict]:
    """Convert aggregated data to final stats JSON."""
    stats = []
    for cbo4, data in sorted(aggregated.items()):
        salarios = data["salarios"]
        record = {
            "codigo_familia": cbo4,
            "salario_mediano": round(statistics.median(salarios), 2) if salarios else None,
            "salario_medio": round(statistics.mean(salarios), 2) if salarios else None,
            "saldo_periodo": data["saldo"],
            "admissoes": data["admissoes"],
            "desligamentos": data["desligamentos"],
            "n_salarios": len(salarios),
        }

        # Top states by admissions
        por_uf = {}
        for uf, uf_data in data["por_uf"].items():
            uf_salarios = uf_data["salarios"]
            por_uf[uf] = {
                "saldo": uf_data["saldo"],
                "admissoes": uf_data["admissoes"],
                "salario_mediano": round(statistics.median(uf_salarios), 2) if uf_salarios else None,
            }
        record["por_uf"] = por_uf

        stats.append(record)

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Download and aggregate CAGED data")
    parser.add_argument("--months", type=int, default=12, help="Number of months to download (default: 12)")
    parser.add_argument("--year", type=int, default=2025, help="End year (default: 2025)")
    parser.add_argument("--month", type=int, default=12, help="End month (default: 12)")
    parser.add_argument("--force", action="store_true", help="Re-download even if cached")
    parser.add_argument("--skip-download", action="store_true", help="Skip download, aggregate cached files")
    args = parser.parse_args()

    if args.skip_download:
        # Find all cached txt files
        if not os.path.exists(CAGED_DIR):
            print(f"No cached files in {CAGED_DIR}")
            return
        txt_paths = sorted([
            os.path.join(CAGED_DIR, f)
            for f in os.listdir(CAGED_DIR)
            if f.startswith("CAGEDMOV") and f.endswith(".txt")
        ])
        if not txt_paths:
            print("No CAGED txt files found")
            return
        print(f"Found {len(txt_paths)} cached CAGED files")
    else:
        print(f"Step 1: Downloading {args.months} months of CAGED data (ending {args.year}-{args.month:02d})...")
        txt_paths = download_months(args.year, args.month, args.months, args.force)
        if not txt_paths:
            print("No data downloaded. Check FTP connectivity.")
            return

    print(f"\nStep 2: Aggregating {len(txt_paths)} months by CBO family...")
    aggregated = aggregate_caged(txt_paths)

    print("\nStep 3: Building stats JSON...")
    stats = build_caged_stats(aggregated)

    out_path = os.path.join(DATA_DIR, "caged_stats.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(stats)} CBO family stats to {out_path}")

    # Summary
    with_salary = sum(1 for s in stats if s["salario_mediano"] is not None)
    total_admissoes = sum(s["admissoes"] for s in stats)
    total_saldo = sum(s["saldo_periodo"] for s in stats)
    print(f"\nSummary:")
    print(f"  Families with salary data: {with_salary}/{len(stats)}")
    print(f"  Total admissions: {total_admissoes:,}")
    print(f"  Net employment change: {total_saldo:+,}")


if __name__ == "__main__":
    main()
