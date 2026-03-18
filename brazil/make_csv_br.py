"""
Build a CSV summary of all Brazilian occupations by merging CBO + CAGED data.

Merges:
- brazil/data/cbo_occupations.json (structure, hierarchy, activities)
- brazil/data/caged_stats.json (salary, employment, saldo)

Output: brazil/occupations_br.csv

Usage:
    uv run python brazil/make_csv_br.py
"""

import csv
import json
import os


DATA_DIR = "brazil/data"


def main():
    # Load CBO families
    with open(os.path.join(DATA_DIR, "cbo_occupations.json"), encoding="utf-8") as f:
        familias = json.load(f)

    # Load CAGED stats, index by family code
    caged_path = os.path.join(DATA_DIR, "caged_stats.json")
    caged_by_code = {}
    if os.path.exists(caged_path):
        with open(caged_path, encoding="utf-8") as f:
            caged_stats = json.load(f)
        for s in caged_stats:
            caged_by_code[s["codigo_familia"]] = s
    else:
        print(f"WARNING: {caged_path} not found. CSV will have empty salary/employment columns.")

    # Build rows
    fieldnames = [
        "codigo_cbo", "titulo", "slug",
        "grande_grupo_codigo", "grande_grupo",
        "subgrupo_principal_codigo", "subgrupo_principal",
        "subgrupo_codigo", "subgrupo",
        "salario_mediano", "salario_medio",
        "admissoes", "desligamentos", "saldo_periodo",
        "n_ocupacoes",  # count of 6-digit sub-occupations
        "n_areas_atividade",  # count of activity areas
        "n_atividades",  # count of distinct activities
    ]

    rows = []
    matched = 0
    for fam in familias:
        codigo = fam["codigo"]
        caged = caged_by_code.get(codigo, {})

        # Count activities (deduplicated)
        atividades = fam.get("atividades", [])
        areas = fam.get("areas_de_atividade", [])
        unique_atividades = set()
        for at in atividades:
            unique_atividades.add(at.get("atividade", ""))

        row = {
            "codigo_cbo": codigo,
            "titulo": fam["titulo"],
            "slug": fam["slug"],
            "grande_grupo_codigo": fam["grande_grupo_codigo"],
            "grande_grupo": fam["grande_grupo"],
            "subgrupo_principal_codigo": fam["subgrupo_principal_codigo"],
            "subgrupo_principal": fam["subgrupo_principal"],
            "subgrupo_codigo": fam["subgrupo_codigo"],
            "subgrupo": fam["subgrupo"],
            "salario_mediano": caged.get("salario_mediano", ""),
            "salario_medio": caged.get("salario_medio", ""),
            "admissoes": caged.get("admissoes", ""),
            "desligamentos": caged.get("desligamentos", ""),
            "saldo_periodo": caged.get("saldo_periodo", ""),
            "n_ocupacoes": 0,  # will fill below
            "n_areas_atividade": len(areas),
            "n_atividades": len(unique_atividades),
        }

        if caged:
            matched += 1

        rows.append(row)

    # Count sub-occupations per family from the ocupacao CSV
    occ_path = os.path.join(DATA_DIR, "cbo2002-ocupacao.csv")
    if os.path.exists(occ_path):
        occ_count = {}
        with open(occ_path, encoding="latin-1") as f:
            for occ_row in csv.DictReader(f, delimiter=";"):
                fam_code = occ_row["CODIGO"].strip()[:4]
                occ_count[fam_code] = occ_count.get(fam_code, 0) + 1
        for row in rows:
            row["n_ocupacoes"] = occ_count.get(row["codigo_cbo"], 0)

    # Write CSV
    out_path = "brazil/occupations_br.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    print(f"  With CAGED data: {matched}/{len(rows)}")

    # Spot checks
    print(f"\nSample rows:")
    checks = ["2124", "7152", "5211", "2251", "7823"]
    for code in checks:
        match = [r for r in rows if r["codigo_cbo"] == code]
        if match:
            r = match[0]
            sal = f"R${float(r['salario_mediano']):,.0f}" if r['salario_mediano'] else "N/A"
            print(f"  {r['codigo_cbo']} {r['titulo']}: {sal}/mês, adm={r['admissoes']}, saldo={r['saldo_periodo']}")


if __name__ == "__main__":
    main()
