"""
Build a compact JSON for the Brazil website by merging CSV stats with AI scores.

Reads:
  - brazil/occupations_br.csv (CBO + CAGED stats)
  - brazil/scores/scores_exposicao.json
  - brazil/scores/scores_vantagem.json
  - brazil/scores/scores_crescimento.json

Writes: brazil/site/data.json

Usage:
    uv run python brazil/build_site_data_br.py
"""

import csv
import json
import os


SCORES_DIR = "brazil/scores"
SITE_DIR = "brazil/site"


def load_scores(path):
    """Load a scores JSON file, returning a slug-keyed dict (empty if missing)."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {s["slug"]: s for s in json.load(f)}


def main():
    # Load all score files
    scores_exp = load_scores(os.path.join(SCORES_DIR, "scores_exposicao.json"))
    scores_van = load_scores(os.path.join(SCORES_DIR, "scores_vantagem.json"))
    scores_cre = load_scores(os.path.join(SCORES_DIR, "scores_crescimento.json"))

    # Load CSV stats
    with open("brazil/occupations_br.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Merge
    data = []
    for row in rows:
        slug = row["slug"]
        exp = scores_exp.get(slug, {})
        van = scores_van.get(slug, {})
        cre = scores_cre.get(slug, {})

        vantagem = van.get("vantagem")
        crescimento = cre.get("crescimento")
        oportunidade = None
        if vantagem is not None and crescimento is not None:
            oportunidade = round((vantagem + crescimento) / 2, 1)

        salario = row.get("salario_mediano", "")
        admissoes = row.get("admissoes", "")
        saldo = row.get("saldo_periodo", "")

        data.append({
            "titulo": row["titulo"],
            "slug": slug,
            "codigo": row["codigo_cbo"],
            "grande_grupo": row["grande_grupo"],
            "grande_grupo_codigo": row["grande_grupo_codigo"],
            "subgrupo_principal": row["subgrupo_principal"],
            "salario": round(float(salario)) if salario else None,
            "admissoes": int(admissoes) if admissoes else None,
            "saldo": int(saldo) if saldo else None,
            "exposicao": exp.get("exposicao"),
            "exposicao_rationale": exp.get("rationale"),
            "vantagem": vantagem,
            "vantagem_rationale": van.get("rationale"),
            "crescimento": crescimento,
            "crescimento_rationale": cre.get("rationale"),
            "oportunidade": oportunidade,
        })

    os.makedirs(SITE_DIR, exist_ok=True)
    with open(os.path.join(SITE_DIR, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"Wrote {len(data)} occupations to {SITE_DIR}/data.json")
    total_admissoes = sum(d["admissoes"] for d in data if d["admissoes"])
    print(f"Total admissions represented: {total_admissoes:,}")

    # Report which layers have data
    for label, key in [("exposição", "exposicao"), ("vantagem", "vantagem"),
                       ("crescimento", "crescimento"), ("oportunidade", "oportunidade")]:
        count = sum(1 for d in data if d[key] is not None)
        if count:
            print(f"  {label}: {count} scored")
        else:
            print(f"  {label}: (no scores yet)")


if __name__ == "__main__":
    main()
