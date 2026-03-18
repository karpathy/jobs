"""
Analyze AI risk by demographics (race, gender) using RAIS + LLM scores.

Answers João's questions:
1. Vagas pretas em risco (Black workers at risk)
2. Vagas femininas em risco (Women workers at risk)
3. Melhores pontos de entrada (low disruption + high salary)
4. Número total de empregos em risco

Usage:
    uv run python brazil/analise_demografica.py
"""

import csv
import json
import os
from collections import defaultdict

DATA_DIR = "brazil/data"
RAIS_DIR = os.path.join(DATA_DIR, "rais_raw")

# RAIS column indices (0-based)
COL_CBO = 7
COL_ATIVO = 11
COL_RACA = 30      # Raça Cor: 1=Indígena, 2=Branca, 4=Preta, 6=Amarela, 8=Parda, 9=Não identificado
COL_SEXO = 37      # Sexo: 1=Masculino, 2=Feminino
COL_REM_MEDIA = 34

RACA_LABELS = {
    "1": "Indígena",
    "2": "Branca",
    "4": "Preta",
    "6": "Amarela",
    "8": "Parda",
    "9": "Não identificado",
}

SEXO_LABELS = {
    "1": "Masculino",
    "2": "Feminino",
}


def aggregate_demographics():
    """Aggregate RAIS by CBO family × race × gender (active workers only)."""
    # Structure: {cbo4: {race: {gender: count}}}
    by_family = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    rais_files = sorted([
        os.path.join(RAIS_DIR, f)
        for f in os.listdir(RAIS_DIR)
        if f.startswith("RAIS_VINC") and f.endswith(".COMT")
    ])

    total = 0
    for path in rais_files:
        print(f"  Processing {os.path.basename(path)}...", end=" ", flush=True)
        rows = 0
        with open(path, encoding="latin-1") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for fields in reader:
                rows += 1
                try:
                    ativo = fields[COL_ATIVO].strip()
                    if ativo != "1":
                        continue
                    cbo6 = fields[COL_CBO].strip()
                    if not cbo6 or len(cbo6) < 4:
                        continue
                    cbo4 = cbo6[:4]
                    raca = fields[COL_RACA].strip()
                    sexo = fields[COL_SEXO].strip()
                    by_family[cbo4][raca][sexo] += 1
                except (IndexError, ValueError):
                    continue
        total += rows
        print(f"{rows:,} rows")

    print(f"\nTotal rows processed: {total:,}")
    return dict(by_family)


def analyze(demographics):
    """Run all analyses using demographics + AI scores."""
    # Load scores
    scores_path = os.path.join("brazil/scores", "scores_exposicao.json")
    with open(scores_path, encoding="utf-8") as f:
        scores_list = json.load(f)
    scores = {s["codigo"]: s for s in scores_list}

    # Load occupation info
    with open(os.path.join(DATA_DIR, "cbo_occupations.json"), encoding="utf-8") as f:
        occs = {o["codigo"]: o for o in json.load(f)}

    # Load RAIS stats for salary
    with open(os.path.join(DATA_DIR, "rais_stats.json"), encoding="utf-8") as f:
        rais_stats = {s["codigo_familia"]: s for s in json.load(f)}

    # Define "at risk" as exposure >= 7
    RISK_THRESHOLD = 7

    print("\n" + "=" * 80)
    print("ANÁLISE DEMOGRÁFICA: IMPACTO DA IA NO MERCADO DE TRABALHO BRASILEIRO")
    print("=" * 80)

    # ─── Question 4: Total jobs at risk ───
    total_workers = 0
    total_at_risk = 0
    risk_by_level = defaultdict(int)

    for cbo4, demo in demographics.items():
        score = scores.get(cbo4, {})
        exp = score.get("exposicao", 0)
        workers = sum(sum(genders.values()) for genders in demo.values())
        total_workers += workers
        if exp >= RISK_THRESHOLD:
            total_at_risk += workers
        # Tiers
        if exp >= 8:
            risk_by_level["Risco muito alto (8-10)"] += workers
        elif exp >= 6:
            risk_by_level["Risco alto (6-7)"] += workers
        elif exp >= 4:
            risk_by_level["Risco moderado (4-5)"] += workers
        else:
            risk_by_level["Risco baixo (0-3)"] += workers

    print(f"\n{'─' * 60}")
    print(f"4. NÚMERO DE EMPREGOS EM RISCO (exposição IA ≥ {RISK_THRESHOLD})")
    print(f"{'─' * 60}")
    print(f"  Total de trabalhadores formais: {total_workers:,.0f}")
    print(f"  Em risco (exposição ≥ {RISK_THRESHOLD}):    {total_at_risk:,.0f} ({total_at_risk/total_workers*100:.1f}%)")
    print(f"\n  Por nível de risco:")
    for level in ["Risco muito alto (8-10)", "Risco alto (6-7)", "Risco moderado (4-5)", "Risco baixo (0-3)"]:
        n = risk_by_level[level]
        print(f"    {level}: {n:>12,.0f} ({n/total_workers*100:.1f}%)")

    # ─── Question 1: Black workers at risk ───
    print(f"\n{'─' * 60}")
    print(f"1. VAGAS PRETAS EM RISCO")
    print(f"{'─' * 60}")
    _analyze_group(demographics, scores, occs, rais_stats, RISK_THRESHOLD,
                   race_filter=["4", "8"],  # Preta + Parda = population negra
                   group_label="Negra (Preta + Parda)")
    _analyze_group(demographics, scores, occs, rais_stats, RISK_THRESHOLD,
                   race_filter=["4"],
                   group_label="Preta")

    # ─── Question 2: Women at risk ───
    print(f"\n{'─' * 60}")
    print(f"2. VAGAS FEMININAS EM RISCO")
    print(f"{'─' * 60}")
    _analyze_group(demographics, scores, occs, rais_stats, RISK_THRESHOLD,
                   gender_filter=["2"],
                   group_label="Feminino")

    # Compare with men
    _analyze_group(demographics, scores, occs, rais_stats, RISK_THRESHOLD,
                   gender_filter=["1"],
                   group_label="Masculino")

    # ─── Question 3: Best entry points ───
    print(f"\n{'─' * 60}")
    print(f"3. MELHORES PONTOS DE ENTRADA (baixa disrupção + alto salário)")
    print(f"{'─' * 60}")
    entries = []
    for cbo4, occ in occs.items():
        score = scores.get(cbo4, {})
        rais = rais_stats.get(cbo4, {})
        exp = score.get("exposicao")
        sal = rais.get("salario_mediano_rais")
        ativos = rais.get("vinculos_ativos", 0)
        if exp is not None and sal and ativos >= 1000:
            entries.append({
                "codigo": cbo4,
                "titulo": occ["titulo"],
                "exposicao": exp,
                "salario": sal,
                "empregados": ativos,
                "escolaridade": rais.get("escolaridade_tipica", ""),
            })

    # Sort by low exposure + high salary (composite: salary / (exposure + 1))
    entries.sort(key=lambda x: x["salario"] / (x["exposicao"] + 1), reverse=True)

    print(f"\n  Top 20 ocupações: baixa exposição IA + alto salário (mín 1.000 empregados)")
    print(f"  {'Código':<8} {'Ocupação':<55} {'Exp':<5} {'Salário':>12} {'Empregados':>12} {'Escolaridade'}")
    print(f"  {'─'*8} {'─'*55} {'─'*5} {'─'*12} {'─'*12} {'─'*20}")
    for e in entries[:20]:
        print(f"  {e['codigo']:<8} {e['titulo'][:55]:<55} {e['exposicao']:<5} R${e['salario']:>10,.0f} {e['empregados']:>12,.0f} {e['escolaridade']}")

    # Also show entry-level (médio completo) options
    entry_level = [e for e in entries if "Médio" in e.get("escolaridade", "")]
    print(f"\n  Top 10 para nível médio:")
    print(f"  {'Código':<8} {'Ocupação':<55} {'Exp':<5} {'Salário':>12} {'Empregados':>12}")
    print(f"  {'─'*8} {'─'*55} {'─'*5} {'─'*12} {'─'*12}")
    for e in entry_level[:10]:
        print(f"  {e['codigo']:<8} {e['titulo'][:55]:<55} {e['exposicao']:<5} R${e['salario']:>10,.0f} {e['empregados']:>12,.0f}")


def _analyze_group(demographics, scores, occs, rais_stats, threshold,
                   race_filter=None, gender_filter=None, group_label=""):
    """Analyze a demographic group's risk exposure."""
    total_group = 0
    at_risk = 0
    top_risk_occs = []

    for cbo4, demo in demographics.items():
        score = scores.get(cbo4, {})
        exp = score.get("exposicao", 0)
        occ = occs.get(cbo4, {})
        rais = rais_stats.get(cbo4, {})

        count = 0
        for raca, genders in demo.items():
            for sexo, n in genders.items():
                race_ok = race_filter is None or raca in race_filter
                gender_ok = gender_filter is None or sexo in gender_filter
                if race_ok and gender_ok:
                    count += n

        if count == 0:
            continue

        total_group += count
        if exp >= threshold:
            at_risk += count
            top_risk_occs.append({
                "codigo": cbo4,
                "titulo": occ.get("titulo", cbo4),
                "exposicao": exp,
                "workers": count,
                "salario": rais.get("salario_mediano_rais"),
            })

    top_risk_occs.sort(key=lambda x: x["workers"], reverse=True)

    pct = (at_risk / total_group * 100) if total_group > 0 else 0
    print(f"\n  Grupo: {group_label}")
    print(f"  Total de trabalhadores: {total_group:>12,.0f}")
    print(f"  Em risco (exp ≥ {threshold}):   {at_risk:>12,.0f} ({pct:.1f}%)")
    if top_risk_occs:
        print(f"\n  Top 10 ocupações em risco para {group_label}:")
        print(f"  {'Código':<8} {'Ocupação':<50} {'Exp':<5} {'Trabalhadores':>14} {'Salário':>12}")
        print(f"  {'─'*8} {'─'*50} {'─'*5} {'─'*14} {'─'*12}")
        for o in top_risk_occs[:10]:
            sal = f"R${o['salario']:,.0f}" if o['salario'] else "N/A"
            print(f"  {o['codigo']:<8} {o['titulo'][:50]:<50} {o['exposicao']:<5} {o['workers']:>14,.0f} {sal:>12}")


def main():
    print("Aggregating RAIS demographics (race × gender × CBO)...")
    demographics = aggregate_demographics()

    # Save for reuse
    out_path = os.path.join(DATA_DIR, "rais_demographics.json")
    # Convert defaultdicts to regular dicts for JSON
    serializable = {
        cbo4: {raca: dict(genders) for raca, genders in races.items()}
        for cbo4, races in demographics.items()
    }
    with open(out_path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"Saved demographics to {out_path}")

    analyze(demographics)


if __name__ == "__main__":
    main()
