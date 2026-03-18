"""
Build a compact JSON for the Brazil website by merging CSV stats with AI scores,
plus regional/demographic breakdowns and a summary file.

Reads:
  - brazil/occupations_br.csv (CBO + CAGED stats)
  - brazil/scores/scores_exposicao.json
  - brazil/scores/scores_vantagem.json
  - brazil/scores/scores_crescimento.json
  - brazil/data/rais_stats.json (por_uf, escolaridade_distribuicao)
  - brazil/data/rais_demographics.json (race x gender counts)

Writes:
  - brazil/site/data.json (per-occupation, now with por_uf, demographics, escolaridade_dist)
  - brazil/site/summary.json (UF-level and demographic aggregates)

Usage:
    uv run python brazil/build_site_data_br.py
"""

import csv
import json
import os

SCORES_DIR = "brazil/scores"
SITE_DIR = "brazil/site"
DATA_DIR = "brazil/data"

UF_NAMES = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

# RAIS race codes: 2=Branca, 4=Preta, 6=Amarela, 8=Parda, 9=Indígena, 1=Não identificado
# RAIS gender codes: 1=Masculino, 2=Feminino


def load_scores(path):
    """Load a scores JSON file, returning a slug-keyed dict (empty if missing)."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {s["slug"]: s for s in json.load(f)}


def load_json(path):
    """Load a JSON file, returning empty structure if missing."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_demographics(demo_entry):
    """Convert race x gender nested dict into simple demographic totals.

    Input: {race_code: {gender_code: count, ...}, ...}
    Output: dict with total_feminino, total_masculino, total_branca, total_negra, etc.
    """
    total_masc = 0
    total_fem = 0
    total_branca = 0
    total_preta = 0
    total_parda = 0

    for race_code, genders in demo_entry.items():
        masc = genders.get("1", 0)
        fem = genders.get("2", 0)
        total_masc += masc
        total_fem += fem

        if race_code == "2":
            total_branca += masc + fem
        elif race_code == "4":
            total_preta += masc + fem
        elif race_code == "8":
            total_parda += masc + fem

    return {
        "total_feminino": total_fem,
        "total_masculino": total_masc,
        "total_branca": total_branca,
        "total_negra": total_preta + total_parda,
        "total_preta": total_preta,
        "total_parda": total_parda,
    }


def build_summary(data):
    """Build UF-level and demographic aggregates for summary.json."""
    # --- UF aggregates ---
    uf_agg = {}  # uf_code -> {total_workers, salary_sum, salary_count, exposure_weighted_sum, exposure_worker_count, occupations: [(titulo, workers)]}
    for occ in data:
        por_uf = occ.get("por_uf")
        if not por_uf:
            continue
        exposicao = occ.get("exposicao")
        for uf_code, uf_data in por_uf.items():
            if uf_code not in uf_agg:
                uf_agg[uf_code] = {
                    "total_workers": 0,
                    "salary_sum": 0.0,
                    "salary_count": 0,
                    "exposure_weighted_sum": 0.0,
                    "exposure_worker_count": 0,
                    "occupations": [],
                }
            agg = uf_agg[uf_code]
            workers = uf_data.get("ativos", 0)
            agg["total_workers"] += workers
            sal = uf_data.get("salario_mediano")
            if sal is not None and workers > 0:
                agg["salary_sum"] += sal * workers
                agg["salary_count"] += workers
            if exposicao is not None and workers > 0:
                agg["exposure_weighted_sum"] += exposicao * workers
                agg["exposure_worker_count"] += workers
            if workers > 0:
                agg["occupations"].append((occ["titulo"], workers))

    uf_summary = {}
    for uf_code in sorted(uf_agg.keys()):
        agg = uf_agg[uf_code]
        top_occs = sorted(agg["occupations"], key=lambda x: x[1], reverse=True)[:5]
        uf_summary[uf_code] = {
            "nome": UF_NAMES.get(uf_code, uf_code),
            "total_workers": agg["total_workers"],
            "avg_salary": round(agg["salary_sum"] / agg["salary_count"]) if agg["salary_count"] else None,
            "avg_exposicao": round(agg["exposure_weighted_sum"] / agg["exposure_worker_count"], 1) if agg["exposure_worker_count"] else None,
            "top_occupations": [{"titulo": t, "workers": w} for t, w in top_occs],
        }

    # --- Demographic aggregates ---
    demo_totals = {
        "total_feminino": 0, "total_masculino": 0,
        "total_branca": 0, "total_negra": 0, "total_preta": 0, "total_parda": 0,
        "high_risk_feminino": 0, "high_risk_masculino": 0,
        "high_risk_branca": 0, "high_risk_negra": 0,
        "workers_with_exposure": 0,
    }
    HIGH_RISK_THRESHOLD = 7.0

    for occ in data:
        demo = occ.get("demographics")
        if not demo:
            continue
        exposicao = occ.get("exposicao")
        is_high_risk = exposicao is not None and exposicao >= HIGH_RISK_THRESHOLD

        for key in ["total_feminino", "total_masculino", "total_branca", "total_negra",
                     "total_preta", "total_parda"]:
            demo_totals[key] += demo.get(key, 0)

        if exposicao is not None:
            demo_totals["workers_with_exposure"] += demo.get("total_feminino", 0) + demo.get("total_masculino", 0)

        if is_high_risk:
            demo_totals["high_risk_feminino"] += demo.get("total_feminino", 0)
            demo_totals["high_risk_masculino"] += demo.get("total_masculino", 0)
            demo_totals["high_risk_branca"] += demo.get("total_branca", 0)
            demo_totals["high_risk_negra"] += demo.get("total_negra", 0)

    # Compute risk percentages
    total_f = demo_totals["total_feminino"]
    total_m = demo_totals["total_masculino"]
    total_b = demo_totals["total_branca"]
    total_n = demo_totals["total_negra"]

    demo_totals["pct_high_risk_feminino"] = round(100 * demo_totals["high_risk_feminino"] / total_f, 1) if total_f else None
    demo_totals["pct_high_risk_masculino"] = round(100 * demo_totals["high_risk_masculino"] / total_m, 1) if total_m else None
    demo_totals["pct_high_risk_branca"] = round(100 * demo_totals["high_risk_branca"] / total_b, 1) if total_b else None
    demo_totals["pct_high_risk_negra"] = round(100 * demo_totals["high_risk_negra"] / total_n, 1) if total_n else None

    return {
        "uf_codes": UF_NAMES,
        "por_uf": uf_summary,
        "demographics": demo_totals,
    }


def main():
    # Load all score files
    scores_exp = load_scores(os.path.join(SCORES_DIR, "scores_exposicao.json"))
    scores_van = load_scores(os.path.join(SCORES_DIR, "scores_vantagem.json"))
    scores_cre = load_scores(os.path.join(SCORES_DIR, "scores_crescimento.json"))

    # Load RAIS stats (keyed by codigo_familia)
    rais_stats_list = load_json(os.path.join(DATA_DIR, "rais_stats.json"))
    rais_stats = {}
    if isinstance(rais_stats_list, list):
        rais_stats = {r["codigo_familia"]: r for r in rais_stats_list}

    # Load RAIS demographics (already keyed by codigo_familia)
    rais_demo = load_json(os.path.join(DATA_DIR, "rais_demographics.json"))

    # Load CSV stats
    with open("brazil/occupations_br.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Merge
    data = []
    for row in rows:
        slug = row["slug"]
        codigo = row["codigo_cbo"]
        exp = scores_exp.get(slug, {})
        van = scores_van.get(slug, {})
        cre = scores_cre.get(slug, {})

        vantagem = van.get("vantagem")
        crescimento = cre.get("crescimento")
        oportunidade = None
        if vantagem is not None and crescimento is not None:
            oportunidade = round((vantagem + crescimento) / 2, 1)

        # RAIS (stock)
        empregados = row.get("empregados", "")
        salario_rais = row.get("salario_mediano_rais", "")
        escolaridade = row.get("escolaridade_tipica", "")
        # CAGED (flow)
        salario_caged = row.get("salario_mediano_caged", "")
        admissoes = row.get("admissoes", "")
        saldo = row.get("saldo_periodo", "")

        # Best salary: prefer RAIS (market rate) over CAGED (admission rate)
        salario = salario_rais or salario_caged

        # Regional breakdown from rais_stats
        rais_entry = rais_stats.get(codigo, {})
        por_uf = rais_entry.get("por_uf")

        # Education distribution from rais_stats
        escolaridade_dist = rais_entry.get("escolaridade_distribuicao")

        # Demographics from rais_demographics
        demo_entry = rais_demo.get(codigo)
        demographics = build_demographics(demo_entry) if demo_entry else None

        data.append({
            "titulo": row["titulo"],
            "slug": slug,
            "codigo": codigo,
            "grande_grupo": row["grande_grupo"],
            "grande_grupo_codigo": row["grande_grupo_codigo"],
            "subgrupo_principal": row["subgrupo_principal"],
            "empregados": int(empregados) if empregados else None,
            "salario": round(float(salario)) if salario else None,
            "salario_admissao": round(float(salario_caged)) if salario_caged else None,
            "escolaridade": escolaridade,
            "admissoes": int(admissoes) if admissoes else None,
            "saldo": int(saldo) if saldo else None,
            "exposicao": exp.get("exposicao"),
            "exposicao_rationale": exp.get("rationale"),
            "vantagem": vantagem,
            "vantagem_rationale": van.get("rationale"),
            "crescimento": crescimento,
            "crescimento_rationale": cre.get("rationale"),
            "oportunidade": oportunidade,
            "por_uf": por_uf,
            "demographics": demographics,
            "escolaridade_dist": escolaridade_dist,
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

    # Report new fields
    por_uf_count = sum(1 for d in data if d["por_uf"])
    demo_count = sum(1 for d in data if d["demographics"])
    esc_count = sum(1 for d in data if d["escolaridade_dist"])
    print(f"  por_uf: {por_uf_count} occupations")
    print(f"  demographics: {demo_count} occupations")
    print(f"  escolaridade_dist: {esc_count} occupations")

    # Build and write summary.json
    summary = build_summary(data)
    with open(os.path.join(SITE_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False)
    print(f"Wrote summary.json ({len(summary['por_uf'])} UFs, demographics aggregated)")


if __name__ == "__main__":
    main()
