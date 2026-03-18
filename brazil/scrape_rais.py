"""
Download and aggregate RAIS (Relação Anual de Informações Sociais) data by CBO family.

RAIS provides the employment STOCK — total workers per occupation as of Dec 31.
This complements CAGED (which gives flows: admissions/terminations).

Key fields extracted:
- Total employed (vínculos ativos em 31/12) per CBO family
- Median salary (remuneração média nominal) across all workers
- Education distribution
- Regional breakdown by UF

Usage:
    uv run python brazil/scrape_rais.py                    # download + aggregate RAIS 2023
    uv run python brazil/scrape_rais.py --year 2023
    uv run python brazil/scrape_rais.py --skip-download    # aggregate from cached files
"""

import argparse
import csv
import io
import json
import os
import statistics
import subprocess
from collections import defaultdict

DATA_DIR = "brazil/data"
RAIS_DIR = os.path.join(DATA_DIR, "rais_raw")
FTP_BASE = "ftp://ftp.mtps.gov.br/pdet/microdados/RAIS"

# RAIS 2023 files — split by region
RAIS_FILES = [
    "RAIS_VINC_PUB_NORTE.7z",
    "RAIS_VINC_PUB_NORDESTE.7z",
    "RAIS_VINC_PUB_CENTRO_OESTE.7z",
    "RAIS_VINC_PUB_MG_ES_RJ.7z",
    "RAIS_VINC_PUB_SP.7z",
    "RAIS_VINC_PUB_SUL.7z",
]

# RAIS column indices (0-based) — from layout
# These are quoted, semicolon-delimited
COL_CBO = 7          # "CBO 2002 Ocupação - Código"
COL_ATIVO = 11        # "Ind Vínculo Ativo 31/12 - Código" (1=active)
COL_ESCOL = 17        # "Escolaridade Após 2005 - Código"
COL_MUNICIPIO = 25    # "Município - Código"
COL_REM_MEDIA = 34    # "Vl Rem Média Nom" (average monthly salary)
COL_REM_DEZ = 32      # "Vl Rem Dezembro Nom"
COL_SEXO = 37         # "Sexo - Código"

# Education codes → labels
ESCOLARIDADE = {
    "1": "Analfabeto",
    "2": "Até 5ª Incompleto",
    "3": "5ª Completo Fundamental",
    "4": "6ª a 9ª Fundamental",
    "5": "Fundamental Completo",
    "6": "Médio Incompleto",
    "7": "Médio Completo",
    "8": "Superior Incompleto",
    "9": "Superior Completo",
    "10": "Mestrado",
    "11": "Doutorado",
}


def download_rais(year: int, force: bool = False) -> list[str]:
    """Download and extract RAIS files for a given year."""
    os.makedirs(RAIS_DIR, exist_ok=True)
    paths = []

    for filename in RAIS_FILES:
        # The extracted file has .COMT extension instead of .7z
        txt_name = filename.replace(".7z", ".COMT")
        txt_path = os.path.join(RAIS_DIR, txt_name)

        if not force and os.path.exists(txt_path):
            print(f"  CACHED {txt_name}")
            paths.append(txt_path)
            continue

        url = f"{FTP_BASE}/{year}/{filename}"
        archive_path = os.path.join(RAIS_DIR, filename)

        print(f"  Downloading {filename}...", end=" ", flush=True)
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", archive_path, url],
                timeout=600, capture_output=True
            )
            if result.returncode != 0 or not os.path.exists(archive_path):
                print(f"FAILED (curl returned {result.returncode})")
                continue

            size = os.path.getsize(archive_path)
            if size < 1000:
                print(f"FAILED (too small: {size} bytes)")
                os.remove(archive_path)
                continue

            print(f"OK ({size:,} bytes)", end=" ", flush=True)

            # Extract
            print("extracting...", end=" ", flush=True)
            result = subprocess.run(
                ["7z", "x", archive_path, f"-o{RAIS_DIR}", "-y"],
                timeout=300, capture_output=True
            )
            os.remove(archive_path)

            if result.returncode != 0:
                print("EXTRACT FAILED")
                continue

            # Find extracted file
            if os.path.exists(txt_path):
                txt_size = os.path.getsize(txt_path)
                print(f"OK ({txt_size:,} bytes)")
                paths.append(txt_path)
            else:
                # Try to find whatever was extracted
                extracted = [f for f in os.listdir(RAIS_DIR)
                             if f.startswith("RAIS_VINC") and not f.endswith(".7z")]
                for ef in extracted:
                    ep = os.path.join(RAIS_DIR, ef)
                    if ep not in paths:
                        print(f"OK (as {ef})")
                        paths.append(ep)

        except Exception as e:
            print(f"ERROR: {e}")

    return paths


def parse_rais_row(fields: list[str]) -> dict | None:
    """Parse a single RAIS row into relevant fields."""
    try:
        cbo6 = fields[COL_CBO].strip().strip('"')
        if not cbo6 or len(cbo6) < 4:
            return None

        ativo = fields[COL_ATIVO].strip().strip('"')
        municipio = fields[COL_MUNICIPIO].strip().strip('"')
        escol = fields[COL_ESCOL].strip().strip('"')
        sexo = fields[COL_SEXO].strip().strip('"')

        # Salary — Brazilian format uses comma as decimal
        rem_str = fields[COL_REM_MEDIA].strip().strip('"').replace(",", ".")
        try:
            rem_media = float(rem_str) if rem_str else 0.0
        except ValueError:
            rem_media = 0.0

        # UF from municipality code (first 2 digits)
        uf = municipio[:2] if len(municipio) >= 2 else ""

        return {
            "cbo4": cbo6[:4],
            "ativo": ativo == "1",
            "uf": uf,
            "escolaridade": escol,
            "salario": rem_media,
            "sexo": sexo,
        }
    except (IndexError, ValueError):
        return None


def aggregate_rais(txt_paths: list[str]) -> dict:
    """Aggregate RAIS data by CBO family (4-digit)."""
    by_family = defaultdict(lambda: {
        "vinculos_ativos": 0,
        "vinculos_total": 0,
        "salarios": [],
        "por_escolaridade": defaultdict(int),
        "por_uf": defaultdict(lambda: {"ativos": 0, "salarios": []}),
    })

    total_rows = 0

    for txt_path in txt_paths:
        filename = os.path.basename(txt_path)
        print(f"  Processing {filename}...", end=" ", flush=True)
        rows = 0

        with open(txt_path, encoding="latin-1") as f:
            # Skip header
            next(f)
            for line in f:
                rows += 1
                fields = line.split(";")
                parsed = parse_rais_row(fields)
                if not parsed:
                    continue

                fam = by_family[parsed["cbo4"]]
                fam["vinculos_total"] += 1

                if parsed["ativo"]:
                    fam["vinculos_ativos"] += 1

                    # Only count salary for active workers with reasonable values
                    if 100 < parsed["salario"] < 500000:
                        fam["salarios"].append(parsed["salario"])

                    # Education
                    fam["por_escolaridade"][parsed["escolaridade"]] += 1

                    # Regional
                    if parsed["uf"]:
                        uf_data = fam["por_uf"][parsed["uf"]]
                        uf_data["ativos"] += 1
                        if 100 < parsed["salario"] < 500000:
                            uf_data["salarios"].append(parsed["salario"])

        total_rows += rows
        print(f"{rows:,} rows")

    print(f"\n  Total: {total_rows:,} rows across {len(txt_paths)} files")
    print(f"  CBO families with data: {len(by_family)}")

    return dict(by_family)


def build_rais_stats(aggregated: dict) -> list[dict]:
    """Convert aggregated RAIS data to stats JSON."""
    stats = []
    for cbo4, data in sorted(aggregated.items()):
        salarios = data["salarios"]

        # Education distribution — find most common level
        escol_dist = dict(data["por_escolaridade"])
        escol_tipica = ""
        if escol_dist:
            most_common = max(escol_dist, key=escol_dist.get)
            escol_tipica = ESCOLARIDADE.get(most_common, most_common)

        record = {
            "codigo_familia": cbo4,
            "vinculos_ativos": data["vinculos_ativos"],
            "vinculos_total": data["vinculos_total"],
            "salario_mediano_rais": round(statistics.median(salarios), 2) if salarios else None,
            "salario_medio_rais": round(statistics.mean(salarios), 2) if salarios else None,
            "n_salarios_rais": len(salarios),
            "escolaridade_tipica": escol_tipica,
            "escolaridade_distribuicao": escol_dist,
        }

        # Regional summary (top states)
        por_uf = {}
        for uf, uf_data in data["por_uf"].items():
            uf_salarios = uf_data["salarios"]
            por_uf[uf] = {
                "ativos": uf_data["ativos"],
                "salario_mediano": round(statistics.median(uf_salarios), 2) if uf_salarios else None,
            }
        record["por_uf"] = por_uf

        stats.append(record)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Download and aggregate RAIS data")
    parser.add_argument("--year", type=int, default=2023, help="RAIS year (default: 2023)")
    parser.add_argument("--force", action="store_true", help="Re-download even if cached")
    parser.add_argument("--skip-download", action="store_true", help="Skip download, aggregate cached files")
    args = parser.parse_args()

    if args.skip_download:
        if not os.path.exists(RAIS_DIR):
            print(f"No cached files in {RAIS_DIR}")
            return
        txt_paths = sorted([
            os.path.join(RAIS_DIR, f)
            for f in os.listdir(RAIS_DIR)
            if f.startswith("RAIS_VINC") and f.endswith(".COMT")
        ])
        if not txt_paths:
            print("No RAIS files found")
            return
        print(f"Found {len(txt_paths)} cached RAIS files")
    else:
        print(f"Step 1: Downloading RAIS {args.year} (6 regional files)...")
        txt_paths = download_rais(args.year, args.force)
        if not txt_paths:
            print("No data downloaded.")
            return

    print(f"\nStep 2: Aggregating {len(txt_paths)} files by CBO family...")
    aggregated = aggregate_rais(txt_paths)

    print("\nStep 3: Building stats JSON...")
    stats = build_rais_stats(aggregated)

    out_path = os.path.join(DATA_DIR, "rais_stats.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(stats)} CBO family stats to {out_path}")

    # Summary
    total_ativos = sum(s["vinculos_ativos"] for s in stats)
    with_salary = sum(1 for s in stats if s["salario_mediano_rais"] is not None)
    print(f"\nSummary:")
    print(f"  Families with data: {len(stats)}")
    print(f"  With salary data: {with_salary}")
    print(f"  Total active workers: {total_ativos:,}")


if __name__ == "__main__":
    main()
