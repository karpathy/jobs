"""
Story templates for the journalist agent.

Each template defines:
- id, category, tags, chart_type
- analysis_fn(data, summary) → dict with headline_stat, headline_label, chart_data, details
- prompt_template: string with {findings} placeholder for the LLM
"""

import statistics


def _fmt_pct(v):
    """Format a float as Brazilian percentage string: 37,7%"""
    return f"{v:.1f}%".replace(".", ",")


def _fmt_num(v):
    """Format an integer with dot thousands separator (Brazilian style)."""
    return f"{v:,}".replace(",", ".")


def _safe_avg(values):
    """Return average of non-None numeric values, or 0."""
    clean = [v for v in values if v is not None]
    return statistics.mean(clean) if clean else 0


# ─── Template 1: Gender Risk Gap ────────────────────────────────────────────

def _gender_risk_gap(data, summary):
    dem = summary["demographics"]
    pct_f = dem["pct_high_risk_feminino"]
    pct_m = dem["pct_high_risk_masculino"]
    total_f = dem["total_feminino"]
    total_m = dem["total_masculino"]
    hr_f = dem["high_risk_feminino"]
    hr_m = dem["high_risk_masculino"]

    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "das mulheres em ocupações de alto risco de exposição à IA",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": pct_m, "formatted": _fmt_pct(pct_m)},
        ],
        "details": {
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "high_risk_feminino": _fmt_num(hr_f),
            "high_risk_masculino": _fmt_num(hr_m),
            "pct_feminino": _fmt_pct(pct_f),
            "pct_masculino": _fmt_pct(pct_m),
            "gap_pp": _fmt_pct(pct_f - pct_m),
        },
    }


# ─── Template 2: Race Risk Gap ──────────────────────────────────────────────

def _race_risk_gap(data, summary):
    dem = summary["demographics"]
    pct_b = dem["pct_high_risk_branca"]
    pct_n = dem["pct_high_risk_negra"]
    total_b = dem["total_branca"]
    total_n = dem["total_negra"]
    hr_b = dem["high_risk_branca"]
    hr_n = dem["high_risk_negra"]

    return {
        "headline_stat": _fmt_pct(pct_b),
        "headline_label": "dos trabalhadores brancos em alto risco vs " + _fmt_pct(pct_n) + " dos negros",
        "chart_data": [
            {"label": "Branca", "value": pct_b, "formatted": _fmt_pct(pct_b)},
            {"label": "Negra", "value": pct_n, "formatted": _fmt_pct(pct_n)},
        ],
        "details": {
            "total_branca": _fmt_num(total_b),
            "total_negra": _fmt_num(total_n),
            "high_risk_branca": _fmt_num(hr_b),
            "high_risk_negra": _fmt_num(hr_n),
            "pct_branca": _fmt_pct(pct_b),
            "pct_negra": _fmt_pct(pct_n),
            "gap_pp": _fmt_pct(pct_b - pct_n),
        },
    }


# ─── Template 3: State Exposure Ranking ─────────────────────────────────────

def _state_exposure_ranking(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        states.append({
            "uf": info["nome"],
            "avg_exposicao": info["avg_exposicao"],
            "total_workers": info["total_workers"],
        })
    states.sort(key=lambda s: s["avg_exposicao"], reverse=True)
    top10 = states[:10]

    return {
        "headline_stat": str(top10[0]["avg_exposicao"]).replace(".", ","),
        "headline_label": f"exposição média em {top10[0]['uf']} — líder nacional",
        "chart_data": [
            {
                "label": s["uf"],
                "value": s["avg_exposicao"],
                "formatted": str(s["avg_exposicao"]).replace(".", ","),
                "workers": _fmt_num(s["total_workers"]),
            }
            for s in top10
        ],
        "details": {
            "top_state": top10[0]["uf"],
            "top_score": str(top10[0]["avg_exposicao"]).replace(".", ","),
            "bottom_state": states[-1]["uf"],
            "bottom_score": str(states[-1]["avg_exposicao"]).replace(".", ","),
            "national_avg": str(round(_safe_avg([s["avg_exposicao"] for s in states]), 1)).replace(".", ","),
            "top10": [{"uf": s["uf"], "score": str(s["avg_exposicao"]).replace(".", ",")} for s in top10],
        },
    }


# ─── Template 4: Most Exposed Top 10 ────────────────────────────────────────

def _most_exposed_top10(data, summary):
    # Filter occupations with both exposicao and empregados
    valid = [
        occ for occ in data
        if occ.get("exposicao") is not None and occ.get("empregados") and occ["empregados"] > 0
    ]
    # Sort by exposicao desc, then by empregados desc as tiebreaker
    valid.sort(key=lambda o: (o["exposicao"], o["empregados"]), reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": str(top10[0]["exposicao"]).replace(".", ","),
        "headline_label": f"exposição máxima — {top10[0]['titulo']}",
        "chart_data": [
            {
                "label": occ["titulo"],
                "value": occ["exposicao"],
                "formatted": str(occ["exposicao"]).replace(".", ","),
                "workers": _fmt_num(occ["empregados"]),
                "salary": _fmt_num(round(occ["salario"])) if occ.get("salario") else "N/D",
            }
            for occ in top10
        ],
        "details": {
            "top10": [
                {
                    "titulo": occ["titulo"],
                    "exposicao": occ["exposicao"],
                    "empregados": _fmt_num(occ["empregados"]),
                    "salario": _fmt_num(round(occ["salario"])) if occ.get("salario") else "N/D",
                }
                for occ in top10
            ],
            "total_workers_top10": _fmt_num(sum(o["empregados"] for o in top10)),
        },
    }


# ─── Template 5: Grande Grupo Comparison ─────────────────────────────────────

def _grupo_comparison(data, summary):
    grupos = {}
    for occ in data:
        gg = occ.get("grande_grupo")
        if not gg:
            continue
        if gg not in grupos:
            grupos[gg] = {"exposicoes": [], "salarios": [], "workers": 0}
        if occ.get("exposicao") is not None:
            grupos[gg]["exposicoes"].append(occ["exposicao"])
        if occ.get("salario") is not None:
            grupos[gg]["salarios"].append(occ["salario"])
        if occ.get("empregados"):
            grupos[gg]["workers"] += occ["empregados"]

    results = []
    for gg, vals in grupos.items():
        avg_exp = _safe_avg(vals["exposicoes"])
        avg_sal = _safe_avg(vals["salarios"])
        results.append({
            "grupo": gg,
            "avg_exposicao": round(avg_exp, 1),
            "avg_salario": round(avg_sal),
            "total_workers": vals["workers"],
            "n_occupations": len(vals["exposicoes"]),
        })
    results.sort(key=lambda r: r["avg_exposicao"], reverse=True)

    # Shorten grupo names for chart labels
    short_names = {
        "MEMBROS SUPERIORES DO PODER PÚBLICO, DIRIGENTES DE ORGANIZAÇÕES DE INTERESSE PÚBLICO E DE EMPRESAS, GERENTES": "Dirigentes e Gerentes",
        "PROFISSIONAIS DAS CIÊNCIAS E DAS ARTES": "Profissionais das Ciências",
        "TÉCNICOS DE NIVEL MÉDIO": "Técnicos de Nível Médio",
        "TRABALHADORES DE SERVIÇOS ADMINISTRATIVOS": "Serviços Administrativos",
        "TRABALHADORES DOS SERVIÇOS, VENDEDORES DO COMÉRCIO EM LOJAS E MERCADOS": "Serviços e Comércio",
        "TRABALHADORES AGROPECUÁRIOS, FLORESTAIS E DA PESCA": "Agropecuária e Pesca",
        "TRABALHADORES DA PRODUÇÃO DE BENS E SERVIÇOS INDUSTRIAIS": "Produção Industrial",
        "TRABALHADORES EM SERVIÇOS DE REPARAÇÃO E MANUTENÇÃO": "Reparação e Manutenção",
        "MEMBROS DAS FORÇAS ARMADAS, POLICIAIS E BOMBEIROS MILITARES": "Forças Armadas e Polícia",
    }

    return {
        "headline_stat": str(results[0]["avg_exposicao"]).replace(".", ","),
        "headline_label": f"exposição média — {short_names.get(results[0]['grupo'], results[0]['grupo'])}",
        "chart_data": [
            {
                "label": short_names.get(r["grupo"], r["grupo"]),
                "value": r["avg_exposicao"],
                "formatted": str(r["avg_exposicao"]).replace(".", ","),
                "workers": _fmt_num(r["total_workers"]),
                "salary": "R$ " + _fmt_num(r["avg_salario"]),
            }
            for r in results
        ],
        "details": {
            "grupos": [
                {
                    "nome": short_names.get(r["grupo"], r["grupo"]),
                    "avg_exposicao": r["avg_exposicao"],
                    "avg_salario": _fmt_num(r["avg_salario"]),
                    "total_workers": _fmt_num(r["total_workers"]),
                    "n_occupations": r["n_occupations"],
                }
                for r in results
            ],
        },
    }


# ─── Template 6: Growth vs Decline ──────────────────────────────────────────

def _growth_vs_decline(data, summary):
    growing = []
    declining = []
    for occ in data:
        if occ.get("saldo") is None or occ.get("exposicao") is None:
            continue
        entry = {
            "titulo": occ["titulo"],
            "saldo": occ["saldo"],
            "exposicao": occ["exposicao"],
            "empregados": occ.get("empregados") or 0,
        }
        if occ["saldo"] > 0:
            growing.append(entry)
        elif occ["saldo"] < 0:
            declining.append(entry)

    growing.sort(key=lambda o: o["saldo"], reverse=True)
    declining.sort(key=lambda o: o["saldo"])

    top_growing = growing[:5]
    top_declining = declining[:5]

    avg_exp_growing = _safe_avg([o["exposicao"] for o in growing]) if growing else 0
    avg_exp_declining = _safe_avg([o["exposicao"] for o in declining]) if declining else 0

    total_saldo_pos = sum(o["saldo"] for o in growing)
    total_saldo_neg = sum(o["saldo"] for o in declining)

    return {
        "headline_stat": _fmt_num(len(growing)),
        "headline_label": f"ocupações em crescimento vs {len(declining)} em declínio",
        "chart_data": [
            {"label": "Em crescimento", "value": len(growing), "formatted": _fmt_num(len(growing)),
             "detail": f"saldo total: +{_fmt_num(total_saldo_pos)}"},
            {"label": "Em declínio", "value": len(declining), "formatted": _fmt_num(len(declining)),
             "detail": f"saldo total: {_fmt_num(total_saldo_neg)}"},
        ],
        "details": {
            "n_growing": len(growing),
            "n_declining": len(declining),
            "avg_exposicao_growing": str(round(avg_exp_growing, 1)).replace(".", ","),
            "avg_exposicao_declining": str(round(avg_exp_declining, 1)).replace(".", ","),
            "total_saldo_pos": "+" + _fmt_num(total_saldo_pos),
            "total_saldo_neg": _fmt_num(total_saldo_neg),
            "top_growing": [
                {"titulo": o["titulo"], "saldo": "+" + _fmt_num(o["saldo"]), "exposicao": o["exposicao"]}
                for o in top_growing
            ],
            "top_declining": [
                {"titulo": o["titulo"], "saldo": _fmt_num(o["saldo"]), "exposicao": o["exposicao"]}
                for o in top_declining
            ],
        },
    }


# ─── Template 7: Safest Large Occupations ───────────────────────────────────

def _safest_large_occupations(data, summary):
    valid = [
        o for o in data
        if o.get("exposicao") is not None and o.get("empregados") and o["empregados"] >= 5000
    ]
    valid.sort(key=lambda o: (o["exposicao"], -o["empregados"]))
    top10 = valid[:10]
    total = sum(o["empregados"] for o in top10)

    return {
        "headline_stat": str(top10[0]["exposicao"]).replace(".", ","),
        "headline_label": f"exposição mínima — {top10[0]['titulo']}",
        "chart_data": [
            {
                "label": o["titulo"],
                "value": o["exposicao"],
                "formatted": str(o["exposicao"]).replace(".", ","),
                "workers": _fmt_num(o["empregados"]),
            }
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o["titulo"], "exposicao": o["exposicao"], "empregados": _fmt_num(o["empregados"]),
                 "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in top10
            ],
            "total_workers": _fmt_num(total),
        },
    }


# ─── Template 8: Highest Opportunity ────────────────────────────────────────

def _highest_opportunity(data, summary):
    valid = [
        o for o in data
        if o.get("oportunidade") is not None and o.get("empregados") and o["empregados"] > 0
    ]
    valid.sort(key=lambda o: (o["oportunidade"], o["empregados"]), reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": str(top10[0]["oportunidade"]).replace(".", ","),
        "headline_label": f"oportunidade máxima — {top10[0]['titulo']}",
        "chart_data": [
            {
                "label": o["titulo"],
                "value": o["oportunidade"],
                "formatted": str(o["oportunidade"]).replace(".", ","),
                "workers": _fmt_num(o["empregados"]),
                "salary": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D",
            }
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o["titulo"], "oportunidade": o["oportunidade"],
                 "exposicao": o["exposicao"], "empregados": _fmt_num(o["empregados"]),
                 "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in top10
            ],
            "total_workers": _fmt_num(sum(o["empregados"] for o in top10)),
        },
    }


# ─── Template 9: Salary vs Exposure ─────────────────────────────────────────

def _salary_vs_exposure(data, summary):
    high_exp = [o for o in data if o.get("exposicao") and o["exposicao"] >= 7 and o.get("salario")]
    low_exp = [o for o in data if o.get("exposicao") is not None and o["exposicao"] <= 3 and o.get("salario")]

    avg_sal_high = round(_safe_avg([o["salario"] for o in high_exp]))
    avg_sal_low = round(_safe_avg([o["salario"] for o in low_exp]))

    return {
        "headline_stat": "R$ " + _fmt_num(avg_sal_high),
        "headline_label": f"salário médio nas ocupações de alta exposição vs R$ {_fmt_num(avg_sal_low)} nas de baixa",
        "chart_data": [
            {"label": "Alta exposição (≥7)", "value": avg_sal_high,
             "formatted": "R$ " + _fmt_num(avg_sal_high),
             "detail": f"{len(high_exp)} ocupações"},
            {"label": "Baixa exposição (≤3)", "value": avg_sal_low,
             "formatted": "R$ " + _fmt_num(avg_sal_low),
             "detail": f"{len(low_exp)} ocupações"},
        ],
        "details": {
            "avg_salary_high": "R$ " + _fmt_num(avg_sal_high),
            "avg_salary_low": "R$ " + _fmt_num(avg_sal_low),
            "n_high": len(high_exp),
            "n_low": len(low_exp),
            "ratio": str(round(avg_sal_high / avg_sal_low, 1)).replace(".", ",") if avg_sal_low else "N/D",
        },
    }


# ─── Template 10: Augmented vs Automated ────────────────────────────────────

def _augmented_vs_automated(data, summary):
    augmented = []  # high exposure + high advantage (AI helps workers)
    automated = []  # high exposure + low advantage (AI replaces workers)
    for o in data:
        if o.get("exposicao") is None or o["exposicao"] < 7:
            continue
        if o.get("vantagem") is None:
            continue
        entry = {
            "titulo": o["titulo"],
            "exposicao": o["exposicao"],
            "vantagem": o["vantagem"],
            "empregados": o.get("empregados") or 0,
            "salario": o.get("salario"),
        }
        if o["vantagem"] >= 7:
            augmented.append(entry)
        elif o["vantagem"] <= 4:
            automated.append(entry)

    augmented.sort(key=lambda o: o["empregados"], reverse=True)
    automated.sort(key=lambda o: o["empregados"], reverse=True)

    total_aug = sum(o["empregados"] for o in augmented)
    total_auto = sum(o["empregados"] for o in automated)

    return {
        "headline_stat": _fmt_num(len(augmented)),
        "headline_label": f"ocupações potencializadas pela IA vs {len(automated)} ameaçadas",
        "chart_data": [
            {"label": "Potencializadas", "value": len(augmented), "formatted": _fmt_num(len(augmented)),
             "detail": _fmt_num(total_aug) + " trabalhadores"},
            {"label": "Ameaçadas", "value": len(automated), "formatted": _fmt_num(len(automated)),
             "detail": _fmt_num(total_auto) + " trabalhadores"},
        ],
        "details": {
            "n_augmented": len(augmented),
            "n_automated": len(automated),
            "total_augmented": _fmt_num(total_aug),
            "total_automated": _fmt_num(total_auto),
            "top_augmented": [
                {"titulo": o["titulo"], "vantagem": o["vantagem"], "empregados": _fmt_num(o["empregados"])}
                for o in augmented[:5]
            ],
            "top_automated": [
                {"titulo": o["titulo"], "vantagem": o["vantagem"], "empregados": _fmt_num(o["empregados"])}
                for o in automated[:5]
            ],
        },
    }


# ─── Template 11: Female-Dominated High-Risk ────────────────────────────────

def _female_dominated_high_risk(data, summary):
    results = []
    for o in data:
        dem = o.get("demographics")
        if not dem or o.get("exposicao") is None or o["exposicao"] < 7:
            continue
        tf = dem.get("total_feminino", 0)
        tm = dem.get("total_masculino", 0)
        total = tf + tm
        if total < 100:
            continue
        pct_f = round(tf / total * 100, 1)
        if pct_f > 55:
            results.append({
                "titulo": o["titulo"],
                "pct_feminino": pct_f,
                "exposicao": o["exposicao"],
                "total_workers": total,
                "salario": o.get("salario"),
            })
    results.sort(key=lambda r: r["total_workers"], reverse=True)
    top10 = results[:10]
    total_workers = sum(r["total_workers"] for r in results)
    total_fem = sum(round(r["total_workers"] * r["pct_feminino"] / 100) for r in results)

    return {
        "headline_stat": _fmt_num(total_fem),
        "headline_label": "mulheres em ocupações feminizadas de alto risco de IA",
        "chart_data": [
            {
                "label": r["titulo"],
                "value": r["pct_feminino"],
                "formatted": _fmt_pct(r["pct_feminino"]),
                "workers": _fmt_num(r["total_workers"]),
            }
            for r in top10
        ],
        "details": {
            "total_occupations": len(results),
            "total_workers": _fmt_num(total_workers),
            "total_women": _fmt_num(total_fem),
            "top10": [
                {"titulo": r["titulo"], "pct_feminino": _fmt_pct(r["pct_feminino"]),
                 "exposicao": r["exposicao"], "workers": _fmt_num(r["total_workers"])}
                for r in top10
            ],
        },
    }


# ─── Template 12: Hiring Into Risk ──────────────────────────────────────────

def _hiring_into_risk(data, summary):
    risky = [
        o for o in data
        if o.get("saldo") and o["saldo"] > 0
        and o.get("exposicao") and o["exposicao"] >= 7
        and o.get("empregados")
    ]
    risky.sort(key=lambda o: o["saldo"], reverse=True)
    top10 = risky[:10]
    total_saldo = sum(o["saldo"] for o in risky)

    return {
        "headline_stat": _fmt_num(total_saldo),
        "headline_label": "contratações líquidas em ocupações de alto risco de IA",
        "chart_data": [
            {
                "label": o["titulo"],
                "value": o["saldo"],
                "formatted": "+" + _fmt_num(o["saldo"]),
                "workers": _fmt_num(o["empregados"]),
            }
            for o in top10
        ],
        "details": {
            "total_occupations": len(risky),
            "total_saldo": "+" + _fmt_num(total_saldo),
            "top10": [
                {"titulo": o["titulo"], "saldo": "+" + _fmt_num(o["saldo"]),
                 "exposicao": o["exposicao"], "empregados": _fmt_num(o["empregados"])}
                for o in top10
            ],
        },
    }


# ─── Template 13: State Salary vs Exposure ──────────────────────────────────

def _state_salary_exposure(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        states.append({
            "uf": info["nome"],
            "avg_exposicao": info["avg_exposicao"],
            "avg_salary": info["avg_salary"],
            "total_workers": info["total_workers"],
        })

    # "Worst positioned": high exposure + low salary
    states.sort(key=lambda s: s["avg_exposicao"] / max(s["avg_salary"], 1), reverse=True)
    worst = states[:10]

    return {
        "headline_stat": worst[0]["uf"],
        "headline_label": "estado mais vulnerável: alta exposição, baixo salário",
        "chart_data": [
            {
                "label": s["uf"],
                "value": s["avg_exposicao"],
                "formatted": str(s["avg_exposicao"]).replace(".", ","),
                "workers": "R$ " + _fmt_num(s["avg_salary"]),
            }
            for s in worst
        ],
        "details": {
            "worst10": [
                {"uf": s["uf"], "exposicao": str(s["avg_exposicao"]).replace(".", ","),
                 "salario": "R$ " + _fmt_num(s["avg_salary"]),
                 "workers": _fmt_num(s["total_workers"])}
                for s in worst
            ],
        },
    }


# ─── Template 14: Education and Exposure ─────────────────────────────────────

def _education_exposure(data, summary):
    edu_map = {
        "Analfabeto": 0, "Até 5ª Incompleto": 1, "6ª a 9ª Fundamental": 2,
        "Médio Completo": 3, "Superior Completo": 4, "Mestrado": 5, "Doutorado": 6,
    }
    buckets = {}
    for o in data:
        esc = o.get("escolaridade")
        if not esc or esc not in edu_map or o.get("exposicao") is None:
            continue
        if esc not in buckets:
            buckets[esc] = {"exposicoes": [], "salarios": [], "count": 0}
        buckets[esc]["exposicoes"].append(o["exposicao"])
        if o.get("salario"):
            buckets[esc]["salarios"].append(o["salario"])
        buckets[esc]["count"] += 1

    results = []
    for esc, vals in buckets.items():
        avg_exp = round(_safe_avg(vals["exposicoes"]), 1)
        avg_sal = round(_safe_avg(vals["salarios"]))
        results.append({"escolaridade": esc, "avg_exposicao": avg_exp,
                        "avg_salario": avg_sal, "n_occupations": vals["count"],
                        "order": edu_map[esc]})
    results.sort(key=lambda r: r["order"])

    highest = max(results, key=lambda r: r["avg_exposicao"])
    lowest = min(results, key=lambda r: r["avg_exposicao"])

    return {
        "headline_stat": str(highest["avg_exposicao"]).replace(".", ","),
        "headline_label": f"exposição média — {highest['escolaridade']} (maior nível)",
        "chart_data": [
            {
                "label": r["escolaridade"],
                "value": r["avg_exposicao"],
                "formatted": str(r["avg_exposicao"]).replace(".", ","),
                "workers": f"{r['n_occupations']} ocupações",
            }
            for r in results
        ],
        "details": {
            "levels": [
                {"escolaridade": r["escolaridade"], "avg_exposicao": r["avg_exposicao"],
                 "avg_salario": "R$ " + _fmt_num(r["avg_salario"]),
                 "n_occupations": r["n_occupations"]}
                for r in results
            ],
            "highest": highest["escolaridade"],
            "highest_score": str(highest["avg_exposicao"]).replace(".", ","),
            "lowest": lowest["escolaridade"],
            "lowest_score": str(lowest["avg_exposicao"]).replace(".", ","),
        },
    }


# ─── Template 15: Entry Salary Gap ──────────────────────────────────────────

def _entry_salary_gap(data, summary):
    high = [o for o in data if o.get("exposicao") and o["exposicao"] >= 7
            and o.get("salario_admissao") and o.get("salario")]
    low = [o for o in data if o.get("exposicao") is not None and o["exposicao"] <= 3
           and o.get("salario_admissao") and o.get("salario")]

    avg_entry_high = round(_safe_avg([o["salario_admissao"] for o in high]))
    avg_full_high = round(_safe_avg([o["salario"] for o in high]))
    avg_entry_low = round(_safe_avg([o["salario_admissao"] for o in low]))
    avg_full_low = round(_safe_avg([o["salario"] for o in low]))

    gap_high = round((avg_full_high - avg_entry_high) / avg_entry_high * 100, 1) if avg_entry_high else 0
    gap_low = round((avg_full_low - avg_entry_low) / avg_entry_low * 100, 1) if avg_entry_low else 0

    return {
        "headline_stat": "R$ " + _fmt_num(avg_entry_high),
        "headline_label": f"salário de entrada em ocupações de alta exposição à IA",
        "chart_data": [
            {"label": "Entrada (alta exp.)", "value": avg_entry_high,
             "formatted": "R$ " + _fmt_num(avg_entry_high)},
            {"label": "Mediano (alta exp.)", "value": avg_full_high,
             "formatted": "R$ " + _fmt_num(avg_full_high)},
            {"label": "Entrada (baixa exp.)", "value": avg_entry_low,
             "formatted": "R$ " + _fmt_num(avg_entry_low)},
            {"label": "Mediano (baixa exp.)", "value": avg_full_low,
             "formatted": "R$ " + _fmt_num(avg_full_low)},
        ],
        "details": {
            "entry_high": "R$ " + _fmt_num(avg_entry_high),
            "full_high": "R$ " + _fmt_num(avg_full_high),
            "gap_high_pct": _fmt_pct(gap_high),
            "entry_low": "R$ " + _fmt_num(avg_entry_low),
            "full_low": "R$ " + _fmt_num(avg_full_low),
            "gap_low_pct": _fmt_pct(gap_low),
            "n_high": len(high),
            "n_low": len(low),
        },
    }


# ─── Template 16: AI Winners (High Opportunity + High Salary) ───────────────

def _ai_winners(data, summary):
    valid = [
        o for o in data
        if o.get("oportunidade") and o["oportunidade"] >= 7
        and o.get("salario") and o["salario"] >= 5000
        and o.get("empregados") and o["empregados"] > 0
    ]
    valid.sort(key=lambda o: o["oportunidade"] * o["salario"], reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": _fmt_num(len(valid)),
        "headline_label": "ocupações com alta oportunidade e salário acima de R$ 5.000",
        "chart_data": [
            {
                "label": o["titulo"],
                "value": o["oportunidade"],
                "formatted": str(o["oportunidade"]).replace(".", ","),
                "workers": "R$ " + _fmt_num(round(o["salario"])),
            }
            for o in top10
        ],
        "details": {
            "total_occupations": len(valid),
            "total_workers": _fmt_num(sum(o["empregados"] for o in valid)),
            "top10": [
                {"titulo": o["titulo"], "oportunidade": o["oportunidade"],
                 "salario": "R$ " + _fmt_num(round(o["salario"])),
                 "empregados": _fmt_num(o["empregados"])}
                for o in top10
            ],
        },
    }


# ─── Template 17: North-South Divide ────────────────────────────────────────

def _north_south_divide(data, summary):
    por_uf = summary["por_uf"]
    north_ne = {"RO", "AC", "AM", "RR", "PA", "AP", "TO", "MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}
    south_se = {"MG", "ES", "RJ", "SP", "PR", "SC", "RS"}
    center = {"MS", "MT", "GO", "DF"}

    regions = {"Norte/Nordeste": [], "Sul/Sudeste": [], "Centro-Oeste": []}
    for code, info in por_uf.items():
        uf = info["nome"]
        if uf in north_ne:
            regions["Norte/Nordeste"].append(info)
        elif uf in south_se:
            regions["Sul/Sudeste"].append(info)
        elif uf in center:
            regions["Centro-Oeste"].append(info)

    results = []
    for region, states in regions.items():
        total_w = sum(s["total_workers"] for s in states)
        avg_exp = round(sum(s["avg_exposicao"] * s["total_workers"] for s in states) / total_w, 1) if total_w else 0
        avg_sal = round(sum(s["avg_salary"] * s["total_workers"] for s in states) / total_w) if total_w else 0
        results.append({"region": region, "avg_exposicao": avg_exp,
                        "avg_salary": avg_sal, "total_workers": total_w,
                        "n_states": len(states)})

    return {
        "headline_stat": str(results[0]["avg_exposicao"]).replace(".", ",") + " vs " + str(results[1]["avg_exposicao"]).replace(".", ","),
        "headline_label": "exposição média: Norte/Nordeste vs Sul/Sudeste",
        "chart_data": [
            {
                "label": r["region"],
                "value": r["avg_exposicao"],
                "formatted": str(r["avg_exposicao"]).replace(".", ","),
                "workers": "R$ " + _fmt_num(r["avg_salary"]),
            }
            for r in results
        ],
        "details": {
            "regions": [
                {"region": r["region"], "avg_exposicao": str(r["avg_exposicao"]).replace(".", ","),
                 "avg_salary": "R$ " + _fmt_num(r["avg_salary"]),
                 "total_workers": _fmt_num(r["total_workers"]),
                 "n_states": r["n_states"]}
                for r in results
            ],
        },
    }


# ─── Template 18: Telemarketing Deep Dive ───────────────────────────────────

def _telemarketing_spotlight(data, summary):
    tele = None
    for o in data:
        if "telemarketing" in o.get("titulo", "").lower():
            tele = o
            break
    if not tele:
        tele = max((o for o in data if o.get("exposicao") and o.get("empregados")),
                   key=lambda o: o["exposicao"] * (o["empregados"] or 0))

    dem = tele.get("demographics", {})
    tf = dem.get("total_feminino", 0)
    tm = dem.get("total_masculino", 0)
    total_dem = tf + tm
    pct_f = round(tf / total_dem * 100, 1) if total_dem else 0

    # Top 5 states
    por_uf = tele.get("por_uf", {})
    states = [{"uf": k, "ativos": v["ativos"], "salario": v.get("salario_mediano", 0)}
              for k, v in (por_uf or {}).items() if v.get("ativos")]
    states.sort(key=lambda s: s["ativos"], reverse=True)

    uf_names = summary.get("uf_codes", {})

    return {
        "headline_stat": _fmt_num(tele.get("empregados", 0)),
        "headline_label": f"trabalhadores em {tele['titulo'].lower()} — exposição {tele['exposicao']}/10",
        "chart_data": [
            {
                "label": uf_names.get(s["uf"], s["uf"]),
                "value": s["ativos"],
                "formatted": _fmt_num(s["ativos"]),
            }
            for s in states[:8]
        ],
        "details": {
            "titulo": tele["titulo"],
            "empregados": _fmt_num(tele.get("empregados", 0)),
            "exposicao": tele["exposicao"],
            "salario": "R$ " + _fmt_num(round(tele["salario"])) if tele.get("salario") else "N/D",
            "saldo": _fmt_num(tele.get("saldo", 0)),
            "pct_feminino": _fmt_pct(pct_f),
            "top_states": [{"uf": uf_names.get(s["uf"], s["uf"]), "ativos": _fmt_num(s["ativos"])} for s in states[:5]],
        },
    }


# ─── Template 19: Risk Tier Distribution ─────────────────────────────────────

def _risk_tier_distribution(data, summary):
    tiers = {"Baixo (0-3)": {"occs": 0, "workers": 0}, "Médio (4-6)": {"occs": 0, "workers": 0}, "Alto (7-10)": {"occs": 0, "workers": 0}}
    for o in data:
        if o.get("exposicao") is None:
            continue
        emp = o.get("empregados") or 0
        if o["exposicao"] <= 3:
            tiers["Baixo (0-3)"]["occs"] += 1
            tiers["Baixo (0-3)"]["workers"] += emp
        elif o["exposicao"] <= 6:
            tiers["Médio (4-6)"]["occs"] += 1
            tiers["Médio (4-6)"]["workers"] += emp
        else:
            tiers["Alto (7-10)"]["occs"] += 1
            tiers["Alto (7-10)"]["workers"] += emp

    total_w = sum(t["workers"] for t in tiers.values())
    chart = []
    details = []
    for label, vals in tiers.items():
        pct = round(vals["workers"] / total_w * 100, 1) if total_w else 0
        chart.append({"label": label, "value": vals["workers"], "formatted": _fmt_num(vals["workers"]),
                       "detail": f"{vals['occs']} ocupações"})
        details.append({"tier": label, "occs": vals["occs"], "workers": _fmt_num(vals["workers"]),
                        "pct": _fmt_pct(pct)})

    return {
        "headline_stat": _fmt_num(tiers["Alto (7-10)"]["workers"]),
        "headline_label": "trabalhadores em ocupações de alto risco de IA (exposição ≥7)",
        "chart_data": chart,
        "details": {"tiers": details, "total_workers": _fmt_num(total_w)},
    }


# ─── Template 20: Lowest Paid High Risk ─────────────────────────────────────

def _lowest_paid_high_risk(data, summary):
    worst = [
        o for o in data
        if o.get("exposicao") and o["exposicao"] >= 7
        and o.get("salario") and o["salario"] < 3000
        and o.get("empregados") and o["empregados"] > 0
    ]
    worst.sort(key=lambda o: o["empregados"], reverse=True)
    top10 = worst[:10]
    total = sum(o["empregados"] for o in worst)

    return {
        "headline_stat": _fmt_num(total),
        "headline_label": "trabalhadores com alto risco E salário abaixo de R$ 3.000",
        "chart_data": [
            {"label": o["titulo"], "value": o["empregados"], "formatted": _fmt_num(o["empregados"]),
             "workers": "R$ " + _fmt_num(round(o["salario"]))}
            for o in top10
        ],
        "details": {
            "total_occupations": len(worst),
            "total_workers": _fmt_num(total),
            "top10": [{"titulo": o["titulo"], "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "exposicao": o["exposicao"], "empregados": _fmt_num(o["empregados"])}
                      for o in top10],
        },
    }


# ─── Template 21: Healthcare Sector ─────────────────────────────────────────

def _healthcare_sector(data, summary):
    keywords = ["enferme", "médic", "saúde", "dentist", "farmac", "fisioter", "nutricion",
                "fonoaudiólog", "terapeut", "biomédic", "veterinár", "psicólog"]
    health = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
              and o.get("exposicao") is not None]
    health.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in health]), 1)
    total_w = sum(o.get("empregados") or 0 for o in health)
    top10 = health[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média na saúde — {len(health)} ocupações analisadas",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(health),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 22: Education Sector ──────────────────────────────────────────

def _education_sector(data, summary):
    teachers = [o for o in data if "professor" in o.get("titulo", "").lower()
                and o.get("exposicao") is not None]
    teachers.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in teachers]), 1)
    total_w = sum(o.get("empregados") or 0 for o in teachers)
    high_risk = [t for t in teachers if t["exposicao"] >= 7]
    high_risk_w = sum(o.get("empregados") or 0 for o in high_risk)

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"professores no Brasil — exposição média {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in teachers[:10]
        ],
        "details": {
            "n_teachers": len(teachers),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "high_risk_count": len(high_risk),
            "high_risk_workers": _fmt_num(high_risk_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in teachers[:10]],
        },
    }


# ─── Template 23: Tech Sector Paradox ────────────────────────────────────────

def _tech_sector(data, summary):
    keywords = ["tecnologia", "informação", "programa", "sistemas", "dados",
                "software", "desenvolvedor", "analista de ti"]
    tech = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None and o.get("oportunidade") is not None]
    tech.sort(key=lambda o: o["oportunidade"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in tech]), 1)
    avg_opp = round(_safe_avg([o["oportunidade"] for o in tech]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in tech if o.get("salario")]))
    total_w = sum(o.get("empregados") or 0 for o in tech)

    return {
        "headline_stat": str(avg_opp).replace(".", ","),
        "headline_label": f"oportunidade média em TI — exposição de {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": o["oportunidade"],
             "formatted": str(o["oportunidade"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in tech[:10]
        ],
        "details": {
            "n_occupations": len(tech),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_oportunidade": str(avg_opp).replace(".", ","),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "oportunidade": o["oportunidade"],
                       "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in tech[:10]],
        },
    }


# ─── Template 24: São Paulo Deep Dive ────────────────────────────────────────

def _sao_paulo_deep_dive(data, summary):
    sp = summary["por_uf"].get("35", {})
    total = sp.get("total_workers", 0)
    national = sum(v["total_workers"] for v in summary["por_uf"].values())
    pct_national = round(total / national * 100, 1) if national else 0

    top_occs = sp.get("top_occupations", [])

    return {
        "headline_stat": _fmt_num(total),
        "headline_label": f"trabalhadores em SP — {_fmt_pct(pct_national)} do total nacional",
        "chart_data": [
            {"label": o["titulo"], "value": o["workers"], "formatted": _fmt_num(o["workers"])}
            for o in top_occs[:8]
        ],
        "details": {
            "total_workers": _fmt_num(total),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(sp.get("avg_salary", 0)),
            "avg_exposicao": str(sp.get("avg_exposicao", 0)).replace(".", ","),
            "top_occupations": [{"titulo": o["titulo"], "workers": _fmt_num(o["workers"])} for o in top_occs],
        },
    }


# ─── Template 25: Admin Jobs Crisis ──────────────────────────────────────────

def _admin_jobs_crisis(data, summary):
    admin = [o for o in data if o.get("grande_grupo", "").startswith("TRABALHADORES DE SERVIÇOS ADMINISTRATIVOS")
             and o.get("exposicao") is not None]
    admin.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    total_w = sum(o.get("empregados") or 0 for o in admin)
    avg_exp = round(_safe_avg([o["exposicao"] for o in admin]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in admin if o.get("salario")]))
    total_saldo = sum(o.get("saldo") or 0 for o in admin)

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores administrativos — exposição média {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in admin[:10]
        ],
        "details": {
            "n_occupations": len(admin),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "total_saldo": _fmt_num(total_saldo),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0),
                       "saldo": _fmt_num(o.get("saldo") or 0)}
                      for o in admin[:10]],
        },
    }


# ─── Template 26: Middle Class Squeeze ───────────────────────────────────────

def _middle_class_squeeze(data, summary):
    middle = [
        o for o in data
        if o.get("salario") and 2500 <= o["salario"] <= 5000
        and o.get("exposicao") and o["exposicao"] >= 7
        and o.get("empregados") and o["empregados"] > 0
    ]
    middle.sort(key=lambda o: o["empregados"], reverse=True)
    total_w = sum(o["empregados"] for o in middle)
    top10 = middle[:10]

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores de classe média (R$ 2,5-5K) em alto risco de IA",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": "R$ " + _fmt_num(round(o["salario"]))}
            for o in top10
        ],
        "details": {
            "n_occupations": len(middle),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "exposicao": o["exposicao"], "empregados": _fmt_num(o["empregados"])}
                      for o in top10],
        },
    }


# ─── Template 27: Opportunity Desert ─────────────────────────────────────────

def _opportunity_desert(data, summary):
    desert = [
        o for o in data
        if o.get("oportunidade") is not None and o["oportunidade"] <= 3
        and o.get("exposicao") and o["exposicao"] >= 6
        and o.get("empregados") and o["empregados"] > 0
    ]
    desert.sort(key=lambda o: o["empregados"], reverse=True)
    total_w = sum(o["empregados"] for o in desert)
    top10 = desert[:10]

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores em {len(desert)} ocupações sem saída: alta exposição, baixa oportunidade",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o["empregados"])}
            for o in top10
        ],
        "details": {
            "n_occupations": len(desert),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "oportunidade": o["oportunidade"], "empregados": _fmt_num(o["empregados"])}
                      for o in top10],
        },
    }


# ─── Template 28: Crescimento Leaders ────────────────────────────────────────

def _crescimento_leaders(data, summary):
    valid = [o for o in data if o.get("crescimento") is not None and o.get("empregados") and o["empregados"] > 0]
    valid.sort(key=lambda o: (o["crescimento"], o["empregados"]), reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": str(top10[0]["crescimento"]).replace(".", ","),
        "headline_label": f"crescimento máximo — {top10[0]['titulo']}",
        "chart_data": [
            {"label": o["titulo"], "value": o["crescimento"],
             "formatted": str(o["crescimento"]).replace(".", ","),
             "workers": _fmt_num(o["empregados"])}
            for o in top10
        ],
        "details": {
            "top10": [{"titulo": o["titulo"], "crescimento": o["crescimento"],
                       "exposicao": o.get("exposicao"), "empregados": _fmt_num(o["empregados"])}
                      for o in top10],
        },
    }


# ─── Template 29: Biggest Job Losses ─────────────────────────────────────────

def _biggest_job_losses(data, summary):
    losing = [o for o in data if o.get("saldo") and o["saldo"] < 0 and o.get("empregados")]
    losing.sort(key=lambda o: o["saldo"])
    top10 = losing[:10]
    total_loss = sum(o["saldo"] for o in losing)

    high_exp = [o for o in losing if o.get("exposicao") and o["exposicao"] >= 7]
    pct_high_exp = round(len(high_exp) / len(losing) * 100, 1) if losing else 0

    return {
        "headline_stat": _fmt_num(abs(total_loss)),
        "headline_label": f"empregos perdidos em {len(losing)} ocupações em declínio",
        "chart_data": [
            {"label": o["titulo"], "value": abs(o["saldo"]),
             "formatted": _fmt_num(o["saldo"]),
             "workers": f"exp: {o.get('exposicao', 'N/D')}"}
            for o in top10
        ],
        "details": {
            "total_losing": len(losing),
            "total_loss": _fmt_num(total_loss),
            "pct_high_exposure": _fmt_pct(pct_high_exp),
            "top10": [{"titulo": o["titulo"], "saldo": _fmt_num(o["saldo"]),
                       "exposicao": o.get("exposicao"), "empregados": _fmt_num(o["empregados"])}
                      for o in top10],
        },
    }


# ─── Template 30: Agriculture Resilience ─────────────────────────────────────

def _agriculture_resilience(data, summary):
    agro = [o for o in data if o.get("grande_grupo", "").startswith("TRABALHADORES AGROPECUÁRIOS")
            and o.get("exposicao") is not None]
    agro.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in agro]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in agro if o.get("salario")]))
    total_w = sum(o.get("empregados") or 0 for o in agro)

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média na agropecuária — a mais baixa entre os setores",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in agro[:10]
        ],
        "details": {
            "n_occupations": len(agro),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in agro[:10]],
        },
    }


# ─── Template 31: Public Sector Exposure ─────────────────────────────────────

def _public_sector(data, summary):
    keywords = ["dirigent", "serviço público", "gestor", "magistrad", "legislador",
                "promotor", "defensor", "procurador"]
    pub = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
           and o.get("exposicao") is not None]
    pub.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in pub]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in pub if o.get("salario")]))
    total_w = sum(o.get("empregados") or 0 for o in pub)

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"servidores públicos analisados — exposição média {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in pub[:10]
        ],
        "details": {
            "n_occupations": len(pub),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0),
                       "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                      for o in pub[:10]],
        },
    }


# ─── Template 32: High Salary Low Advantage ──────────────────────────────────

def _high_salary_low_advantage(data, summary):
    at_risk_elite = [
        o for o in data
        if o.get("salario") and o["salario"] >= 8000
        and o.get("exposicao") and o["exposicao"] >= 7
        and o.get("vantagem") is not None and o["vantagem"] <= 5
        and o.get("empregados")
    ]
    at_risk_elite.sort(key=lambda o: o["salario"], reverse=True)
    top10 = at_risk_elite[:10]
    total_w = sum(o["empregados"] for o in at_risk_elite)

    return {
        "headline_stat": _fmt_num(len(at_risk_elite)),
        "headline_label": "ocupações de alto salário ameaçadas pela IA (salário ≥R$ 8K, vantagem ≤5)",
        "chart_data": [
            {"label": o["titulo"], "value": o["salario"],
             "formatted": "R$ " + _fmt_num(round(o["salario"])),
             "workers": f"exp: {o['exposicao']}, vant: {o['vantagem']}"}
            for o in top10
        ],
        "details": {
            "n_occupations": len(at_risk_elite),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "exposicao": o["exposicao"], "vantagem": o["vantagem"],
                       "empregados": _fmt_num(o["empregados"])}
                      for o in top10],
        },
    }


# ─── Template 33: Vantagem Leaders ───────────────────────────────────────────

def _vantagem_leaders(data, summary):
    valid = [o for o in data if o.get("vantagem") is not None and o.get("empregados") and o["empregados"] > 0]
    valid.sort(key=lambda o: (o["vantagem"], o["empregados"]), reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": str(top10[0]["vantagem"]).replace(".", ","),
        "headline_label": f"vantagem máxima — {top10[0]['titulo']}",
        "chart_data": [
            {"label": o["titulo"], "value": o["vantagem"],
             "formatted": str(o["vantagem"]).replace(".", ","),
             "workers": _fmt_num(o["empregados"])}
            for o in top10
        ],
        "details": {
            "top10": [{"titulo": o["titulo"], "vantagem": o["vantagem"],
                       "exposicao": o.get("exposicao"), "empregados": _fmt_num(o["empregados"]),
                       "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                      for o in top10],
        },
    }


# ─── Template 34: Young Workers Entry ────────────────────────────────────────

def _young_workers_entry(data, summary):
    hiring = [o for o in data if o.get("admissoes") and o["admissoes"] > 1000
              and o.get("exposicao") is not None and o.get("salario_admissao")]
    hiring.sort(key=lambda o: o["admissoes"], reverse=True)
    top10 = hiring[:10]
    total_admissoes = sum(o["admissoes"] for o in hiring)

    high_risk = [o for o in hiring if o["exposicao"] >= 7]
    pct_high = round(sum(o["admissoes"] for o in high_risk) / total_admissoes * 100, 1) if total_admissoes else 0

    return {
        "headline_stat": _fmt_num(total_admissoes),
        "headline_label": f"admissões nos últimos 12 meses — {_fmt_pct(pct_high)} em ocupações de alto risco",
        "chart_data": [
            {"label": o["titulo"], "value": o["admissoes"],
             "formatted": _fmt_num(o["admissoes"]),
             "workers": "R$ " + _fmt_num(round(o["salario_admissao"]))}
            for o in top10
        ],
        "details": {
            "total_admissoes": _fmt_num(total_admissoes),
            "pct_high_risk": _fmt_pct(pct_high),
            "n_high_risk": len(high_risk),
            "top10": [{"titulo": o["titulo"], "admissoes": _fmt_num(o["admissoes"]),
                       "salario_admissao": "R$ " + _fmt_num(round(o["salario_admissao"])),
                       "exposicao": o["exposicao"]}
                      for o in top10],
        },
    }


# ─── Template 35: Exposure Inequality Index ──────────────────────────────────

def _exposure_inequality(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        states.append({
            "uf": info["nome"],
            "avg_exposicao": info["avg_exposicao"],
            "avg_salary": info["avg_salary"],
            "total_workers": info["total_workers"],
        })
    states.sort(key=lambda s: s["avg_salary"])

    poorest5 = states[:5]
    richest5 = states[-5:]
    avg_exp_poor = round(_safe_avg([s["avg_exposicao"] for s in poorest5]), 1)
    avg_exp_rich = round(_safe_avg([s["avg_exposicao"] for s in richest5]), 1)
    avg_sal_poor = round(_safe_avg([s["avg_salary"] for s in poorest5]))
    avg_sal_rich = round(_safe_avg([s["avg_salary"] for s in richest5]))

    return {
        "headline_stat": str(avg_exp_poor).replace(".", ",") + " vs " + str(avg_exp_rich).replace(".", ","),
        "headline_label": "exposição: 5 estados mais pobres vs 5 mais ricos",
        "chart_data": [
            {"label": "5 mais pobres", "value": avg_exp_poor,
             "formatted": str(avg_exp_poor).replace(".", ","),
             "detail": "sal. médio R$ " + _fmt_num(avg_sal_poor)},
            {"label": "5 mais ricos", "value": avg_exp_rich,
             "formatted": str(avg_exp_rich).replace(".", ","),
             "detail": "sal. médio R$ " + _fmt_num(avg_sal_rich)},
        ],
        "details": {
            "poorest5": [{"uf": s["uf"], "exp": str(s["avg_exposicao"]).replace(".", ","),
                          "sal": "R$ " + _fmt_num(s["avg_salary"])} for s in poorest5],
            "richest5": [{"uf": s["uf"], "exp": str(s["avg_exposicao"]).replace(".", ","),
                          "sal": "R$ " + _fmt_num(s["avg_salary"])} for s in richest5],
            "avg_exp_poor": str(avg_exp_poor).replace(".", ","),
            "avg_exp_rich": str(avg_exp_rich).replace(".", ","),
        },
    }


# ─── Template 36: Race x Gender Intersection ─────────────────────────────────

def _race_gender_intersection(data, summary):
    dem = summary["demographics"]

    # Compute cross stats
    total_f = dem["total_feminino"]
    total_m = dem["total_masculino"]
    hr_f = dem["high_risk_feminino"]
    hr_m = dem["high_risk_masculino"]
    total_n = dem["total_negra"]
    total_b = dem["total_branca"]
    hr_n = dem["high_risk_negra"]
    hr_b = dem["high_risk_branca"]

    # Estimate: Black women are at the intersection
    # Use available aggregate data for the story
    pct_f = dem["pct_high_risk_feminino"]
    pct_m = dem["pct_high_risk_masculino"]
    pct_b = dem["pct_high_risk_branca"]
    pct_n = dem["pct_high_risk_negra"]

    groups = [
        {"label": "Mulheres brancas", "pct": round((pct_f + pct_b) / 2, 1)},
        {"label": "Mulheres negras", "pct": round((pct_f + pct_n) / 2, 1)},
        {"label": "Homens brancos", "pct": round((pct_m + pct_b) / 2, 1)},
        {"label": "Homens negros", "pct": round((pct_m + pct_n) / 2, 1)},
    ]
    groups.sort(key=lambda g: g["pct"], reverse=True)

    return {
        "headline_stat": _fmt_pct(groups[0]["pct"]),
        "headline_label": f"risco estimado para {groups[0]['label'].lower()} — o grupo mais exposto",
        "chart_data": [
            {"label": g["label"], "value": g["pct"], "formatted": _fmt_pct(g["pct"])}
            for g in groups
        ],
        "details": {
            "groups": [{"label": g["label"], "pct": _fmt_pct(g["pct"])} for g in groups],
            "pct_feminino": _fmt_pct(pct_f),
            "pct_masculino": _fmt_pct(pct_m),
            "pct_branca": _fmt_pct(pct_b),
            "pct_negra": _fmt_pct(pct_n),
            "note": "Estimativa cruzada baseada em médias de gênero e raça",
        },
    }


# ─── Template 37: Rio de Janeiro Deep Dive ─────────────────────────────────

def _rio_de_janeiro_deep_dive(data, summary):
    rj = summary["por_uf"].get("33", {})
    total = rj.get("total_workers", 0)
    national = sum(v["total_workers"] for v in summary["por_uf"].values())
    pct_national = round(total / national * 100, 1) if national else 0
    top_occs = rj.get("top_occupations", [])

    return {
        "headline_stat": _fmt_num(total),
        "headline_label": f"trabalhadores no RJ — {_fmt_pct(pct_national)} do total nacional",
        "chart_data": [
            {"label": o["titulo"], "value": o["workers"], "formatted": _fmt_num(o["workers"])}
            for o in top_occs[:8]
        ],
        "details": {
            "total_workers": _fmt_num(total),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(rj.get("avg_salary", 0)),
            "avg_exposicao": str(rj.get("avg_exposicao", 0)).replace(".", ","),
            "top_occupations": [{"titulo": o["titulo"], "workers": _fmt_num(o["workers"])} for o in top_occs],
        },
    }


# ─── Template 38: Minas Gerais Deep Dive ──────────────────────────────────

def _minas_gerais_deep_dive(data, summary):
    mg = summary["por_uf"].get("31", {})
    total = mg.get("total_workers", 0)
    national = sum(v["total_workers"] for v in summary["por_uf"].values())
    pct_national = round(total / national * 100, 1) if national else 0
    top_occs = mg.get("top_occupations", [])

    return {
        "headline_stat": _fmt_num(total),
        "headline_label": f"trabalhadores em MG — {_fmt_pct(pct_national)} do total nacional",
        "chart_data": [
            {"label": o["titulo"], "value": o["workers"], "formatted": _fmt_num(o["workers"])}
            for o in top_occs[:8]
        ],
        "details": {
            "total_workers": _fmt_num(total),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(mg.get("avg_salary", 0)),
            "avg_exposicao": str(mg.get("avg_exposicao", 0)).replace(".", ","),
            "top_occupations": [{"titulo": o["titulo"], "workers": _fmt_num(o["workers"])} for o in top_occs],
        },
    }


# ─── Template 39: Bahia Deep Dive ─────────────────────────────────────────

def _bahia_deep_dive(data, summary):
    ba = summary["por_uf"].get("29", {})
    total = ba.get("total_workers", 0)
    national = sum(v["total_workers"] for v in summary["por_uf"].values())
    pct_national = round(total / national * 100, 1) if national else 0
    top_occs = ba.get("top_occupations", [])

    return {
        "headline_stat": _fmt_num(total),
        "headline_label": f"trabalhadores na BA — {_fmt_pct(pct_national)} do total nacional",
        "chart_data": [
            {"label": o["titulo"], "value": o["workers"], "formatted": _fmt_num(o["workers"])}
            for o in top_occs[:8]
        ],
        "details": {
            "total_workers": _fmt_num(total),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(ba.get("avg_salary", 0)),
            "avg_exposicao": str(ba.get("avg_exposicao", 0)).replace(".", ","),
            "top_occupations": [{"titulo": o["titulo"], "workers": _fmt_num(o["workers"])} for o in top_occs],
        },
    }


# ─── Template 40: Rio Grande do Sul Deep Dive ─────────────────────────────

def _rio_grande_sul_deep_dive(data, summary):
    rs = summary["por_uf"].get("43", {})
    total = rs.get("total_workers", 0)
    national = sum(v["total_workers"] for v in summary["por_uf"].values())
    pct_national = round(total / national * 100, 1) if national else 0
    top_occs = rs.get("top_occupations", [])

    return {
        "headline_stat": _fmt_num(total),
        "headline_label": f"trabalhadores no RS — {_fmt_pct(pct_national)} do total nacional",
        "chart_data": [
            {"label": o["titulo"], "value": o["workers"], "formatted": _fmt_num(o["workers"])}
            for o in top_occs[:8]
        ],
        "details": {
            "total_workers": _fmt_num(total),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(rs.get("avg_salary", 0)),
            "avg_exposicao": str(rs.get("avg_exposicao", 0)).replace(".", ","),
            "top_occupations": [{"titulo": o["titulo"], "workers": _fmt_num(o["workers"])} for o in top_occs],
        },
    }


# ─── Template 41: Paraná Deep Dive ────────────────────────────────────────

def _parana_deep_dive(data, summary):
    pr = summary["por_uf"].get("41", {})
    total = pr.get("total_workers", 0)
    national = sum(v["total_workers"] for v in summary["por_uf"].values())
    pct_national = round(total / national * 100, 1) if national else 0
    top_occs = pr.get("top_occupations", [])

    return {
        "headline_stat": _fmt_num(total),
        "headline_label": f"trabalhadores no PR — {_fmt_pct(pct_national)} do total nacional",
        "chart_data": [
            {"label": o["titulo"], "value": o["workers"], "formatted": _fmt_num(o["workers"])}
            for o in top_occs[:8]
        ],
        "details": {
            "total_workers": _fmt_num(total),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(pr.get("avg_salary", 0)),
            "avg_exposicao": str(pr.get("avg_exposicao", 0)).replace(".", ","),
            "top_occupations": [{"titulo": o["titulo"], "workers": _fmt_num(o["workers"])} for o in top_occs],
        },
    }


# ─── Template 42: Distrito Federal Deep Dive ──────────────────────────────

def _distrito_federal_deep_dive(data, summary):
    df = summary["por_uf"].get("53", {})
    total = df.get("total_workers", 0)
    national = sum(v["total_workers"] for v in summary["por_uf"].values())
    pct_national = round(total / national * 100, 1) if national else 0
    top_occs = df.get("top_occupations", [])

    return {
        "headline_stat": _fmt_num(total),
        "headline_label": f"trabalhadores no DF — {_fmt_pct(pct_national)} do total nacional",
        "chart_data": [
            {"label": o["titulo"], "value": o["workers"], "formatted": _fmt_num(o["workers"])}
            for o in top_occs[:8]
        ],
        "details": {
            "total_workers": _fmt_num(total),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(df.get("avg_salary", 0)),
            "avg_exposicao": str(df.get("avg_exposicao", 0)).replace(".", ","),
            "top_occupations": [{"titulo": o["titulo"], "workers": _fmt_num(o["workers"])} for o in top_occs],
        },
    }


# ─── Template 43: Nordeste Workforce ──────────────────────────────────────

def _nordeste_workforce(data, summary):
    ne_codes = ["21", "22", "23", "24", "25", "26", "27", "28", "29"]
    por_uf = summary["por_uf"]
    national = sum(v["total_workers"] for v in por_uf.values())

    states = []
    total_ne = 0
    salaries = []
    exposicoes = []
    for code in ne_codes:
        info = por_uf.get(code, {})
        w = info.get("total_workers", 0)
        total_ne += w
        if info.get("avg_salary"):
            salaries.append(info["avg_salary"])
        if info.get("avg_exposicao"):
            exposicoes.append(info["avg_exposicao"])
        states.append({"uf": info.get("nome", code), "workers": w,
                        "avg_salary": info.get("avg_salary", 0),
                        "avg_exposicao": info.get("avg_exposicao", 0)})
    states.sort(key=lambda s: s["workers"], reverse=True)
    pct_national = round(total_ne / national * 100, 1) if national else 0

    return {
        "headline_stat": _fmt_num(total_ne),
        "headline_label": f"trabalhadores no Nordeste — {_fmt_pct(pct_national)} do Brasil",
        "chart_data": [
            {"label": s["uf"], "value": s["workers"], "formatted": _fmt_num(s["workers"])}
            for s in states
        ],
        "details": {
            "total_workers": _fmt_num(total_ne),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(round(_safe_avg(salaries))),
            "avg_exposicao": str(round(_safe_avg(exposicoes), 1)).replace(".", ","),
            "states": [{"uf": s["uf"], "workers": _fmt_num(s["workers"]),
                        "avg_salary": "R$ " + _fmt_num(round(s["avg_salary"])),
                        "avg_exposicao": str(round(s["avg_exposicao"], 1)).replace(".", ",")}
                       for s in states],
        },
    }


# ─── Template 44: Amazônia States ─────────────────────────────────────────

def _amazonia_states(data, summary):
    n_codes = ["11", "12", "13", "14", "15", "16", "17"]
    por_uf = summary["por_uf"]
    national = sum(v["total_workers"] for v in por_uf.values())

    states = []
    total_n = 0
    salaries = []
    exposicoes = []
    for code in n_codes:
        info = por_uf.get(code, {})
        w = info.get("total_workers", 0)
        total_n += w
        if info.get("avg_salary"):
            salaries.append(info["avg_salary"])
        if info.get("avg_exposicao"):
            exposicoes.append(info["avg_exposicao"])
        states.append({"uf": info.get("nome", code), "workers": w,
                        "avg_salary": info.get("avg_salary", 0),
                        "avg_exposicao": info.get("avg_exposicao", 0)})
    states.sort(key=lambda s: s["workers"], reverse=True)
    pct_national = round(total_n / national * 100, 1) if national else 0

    return {
        "headline_stat": _fmt_num(total_n),
        "headline_label": f"trabalhadores na Amazônia Legal — {_fmt_pct(pct_national)} do Brasil",
        "chart_data": [
            {"label": s["uf"], "value": s["workers"], "formatted": _fmt_num(s["workers"])}
            for s in states
        ],
        "details": {
            "total_workers": _fmt_num(total_n),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(round(_safe_avg(salaries))),
            "avg_exposicao": str(round(_safe_avg(exposicoes), 1)).replace(".", ","),
            "states": [{"uf": s["uf"], "workers": _fmt_num(s["workers"]),
                        "avg_salary": "R$ " + _fmt_num(round(s["avg_salary"])),
                        "avg_exposicao": str(round(s["avg_exposicao"], 1)).replace(".", ",")}
                       for s in states],
        },
    }


# ─── Template 45: Financial Sector ────────────────────────────────────────

def _financial_sector(data, summary):
    keywords = ["contab", "financ", "banc", "audit", "segur"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média no setor financeiro — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 46: Legal Sector ────────────────────────────────────────────

def _legal_sector(data, summary):
    keywords = ["advogad", "jurídic", "juiz", "cartorár", "tabeliã"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média no setor jurídico — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 47: Engineering Sector ──────────────────────────────────────

def _engineering_sector(data, summary):
    keywords = ["engenheir"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in occs if o.get("salario")]))
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média em engenharia — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0),
                       "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                      for o in top10],
        },
    }


# ─── Template 48: Construction Sector ─────────────────────────────────────

def _construction_sector(data, summary):
    keywords = ["constru", "pedreiro", "eletricist", "encanad", "pintor de obra"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média na construção — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 49: Transport & Logistics ───────────────────────────────────

def _transport_logistics(data, summary):
    keywords = ["motorist", "transport", "logístic", "caminhoneir"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média em transporte/logística — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 50: Tourism & Hospitality ───────────────────────────────────

def _tourism_hospitality(data, summary):
    keywords = ["hotel", "turism", "cozinheir", "garçon", "recepcion", "camareira"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média em turismo/hotelaria — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 51: Creative Industries ─────────────────────────────────────

def _creative_industries(data, summary):
    keywords = ["artist", "design", "músic", "cinema", "jornalist", "fotógraf", "publicit"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média nas indústrias criativas — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 52: Security Sector ─────────────────────────────────────────

def _security_sector(data, summary):
    keywords = ["vigilant", "seguranç", "polici", "bombeir", "guarda"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média em segurança — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 53: Manufacturing Detailed ──────────────────────────────────

def _manufacturing_detailed(data, summary):
    occs = [o for o in data
            if o.get("grande_grupo", "").startswith("TRABALHADORES DA PRODUÇÃO")
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    avg_sal = round(_safe_avg([o["salario"] for o in occs if o.get("salario")]))
    total_saldo = sum(o.get("saldo") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores na produção industrial — exposição média {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(total_w),
            "total_saldo": _fmt_num(total_saldo),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 54: Commerce & Retail ───────────────────────────────────────

def _commerce_retail(data, summary):
    occs = [o for o in data
            if o.get("grande_grupo", "").startswith("TRABALHADORES DOS SERVIÇOS, VENDEDORES")
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    avg_sal = round(_safe_avg([o["salario"] for o in occs if o.get("salario")]))
    total_saldo = sum(o.get("saldo") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores em comércio/serviços — exposição média {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(total_w),
            "total_saldo": _fmt_num(total_saldo),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 55: Care Economy ────────────────────────────────────────────

def _care_economy(data, summary):
    keywords = ["cuidador", "assistência social", "doméstic", "babá", "diarist"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    avg_sal = round(_safe_avg([o["salario"] for o in occs if o.get("salario")]))
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média na economia do cuidado — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 56: Food Industry ───────────────────────────────────────────

def _food_industry(data, summary):
    keywords = ["aliment", "açougueir", "padeiro", "confeit", "frigoríf"]
    occs = [o for o in data if any(k in o.get("titulo", "").lower() for k in keywords)
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição média na indústria alimentícia — {len(occs)} ocupações",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "workers": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 57: Exposure 10 Spotlight ───────────────────────────────────

def _exposure_10_spotlight(data, summary):
    max_exp = [o for o in data if o.get("exposicao") == 10]
    max_exp.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    total_w = sum(o.get("empregados") or 0 for o in max_exp)
    avg_sal = round(_safe_avg([o["salario"] for o in max_exp if o.get("salario")]))
    top10 = max_exp[:10]

    return {
        "headline_stat": str(len(max_exp)),
        "headline_label": "ocupações com exposição máxima (10) à IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0,
             "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(max_exp),
            "total_workers": _fmt_num(total_w),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "top10": [{"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                       "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                      for o in top10],
        },
    }


# ─── Template 58: Exposure 1 Spotlight ────────────────────────────────────

def _exposure_1_spotlight(data, summary):
    low_exp = [o for o in data if o.get("exposicao") is not None and o["exposicao"] <= 2]
    low_exp.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    total_w = sum(o.get("empregados") or 0 for o in low_exp)
    avg_sal = round(_safe_avg([o["salario"] for o in low_exp if o.get("salario")]))
    top10 = low_exp[:10]

    return {
        "headline_stat": str(len(low_exp)),
        "headline_label": "ocupações com exposição mínima (≤2) à IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0,
             "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(low_exp),
            "total_workers": _fmt_num(total_w),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "top10": [{"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                       "exposicao": o["exposicao"],
                       "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                      for o in top10],
        },
    }


# ─── Template 59: Largest Occupations ─────────────────────────────────────

def _largest_occupations(data, summary):
    valid = [o for o in data if o.get("empregados") and o["empregados"] > 0]
    valid.sort(key=lambda o: o["empregados"], reverse=True)
    top10 = valid[:10]

    total_top10 = sum(o["empregados"] for o in top10)
    total_all = sum(o.get("empregados") or 0 for o in data)
    pct = round(total_top10 / total_all * 100, 1) if total_all else 0

    return {
        "headline_stat": _fmt_num(total_top10),
        "headline_label": f"trabalhadores nas 10 maiores ocupações — {_fmt_pct(pct)} do total",
        "chart_data": [
            {"label": o["titulo"], "value": o["empregados"],
             "formatted": _fmt_num(o["empregados"]),
             "exposicao": o.get("exposicao")}
            for o in top10
        ],
        "details": {
            "total_top10": _fmt_num(total_top10),
            "pct_total": _fmt_pct(pct),
            "top10": [{"titulo": o["titulo"], "empregados": _fmt_num(o["empregados"]),
                       "exposicao": o.get("exposicao"),
                       "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                      for o in top10],
        },
    }


# ─── Template 60: Highest Paid Top 10 ─────────────────────────────────────

def _highest_paid_top10(data, summary):
    valid = [o for o in data if o.get("salario") and o.get("empregados") and o["empregados"] > 0]
    valid.sort(key=lambda o: o["salario"], reverse=True)
    top10 = valid[:10]

    avg_exp = round(_safe_avg([o["exposicao"] for o in top10 if o.get("exposicao") is not None]), 1)

    return {
        "headline_stat": "R$ " + _fmt_num(round(top10[0]["salario"])),
        "headline_label": f"salário médio mais alto — {top10[0]['titulo']}",
        "chart_data": [
            {"label": o["titulo"], "value": round(o["salario"]),
             "formatted": "R$ " + _fmt_num(round(o["salario"])),
             "workers": _fmt_num(o["empregados"])}
            for o in top10
        ],
        "details": {
            "avg_exposicao_top10": str(avg_exp).replace(".", ","),
            "top10": [{"titulo": o["titulo"], "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "empregados": _fmt_num(o["empregados"]),
                       "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 61: Gender Imbalance Top ────────────────────────────────────

def _gender_imbalance_top(data, summary):
    results = []
    for o in data:
        dem = o.get("demographics")
        if not dem:
            continue
        tf = dem.get("total_feminino", 0)
        tm = dem.get("total_masculino", 0)
        total = tf + tm
        if total < 500:
            continue
        pct_f = round(tf / total * 100, 1)
        ratio = max(pct_f, 100 - pct_f)
        results.append({
            "titulo": o["titulo"],
            "pct_feminino": pct_f,
            "pct_masculino": round(100 - pct_f, 1),
            "dominant": "Feminino" if pct_f > 50 else "Masculino",
            "ratio": ratio,
            "total_workers": total,
            "exposicao": o.get("exposicao"),
        })
    results.sort(key=lambda r: r["ratio"], reverse=True)
    top10 = results[:10]

    return {
        "headline_stat": _fmt_pct(top10[0]["ratio"]),
        "headline_label": f"concentração de gênero mais extrema — {top10[0]['titulo']}",
        "chart_data": [
            {"label": r["titulo"], "value": r["ratio"],
             "formatted": _fmt_pct(r["ratio"]),
             "dominant": r["dominant"]}
            for r in top10
        ],
        "details": {
            "top10": [{"titulo": r["titulo"], "pct_feminino": _fmt_pct(r["pct_feminino"]),
                       "pct_masculino": _fmt_pct(r["pct_masculino"]),
                       "dominant": r["dominant"], "workers": _fmt_num(r["total_workers"]),
                       "exposicao": r["exposicao"]}
                      for r in top10],
        },
    }


# ─── Template 62: Salary Progression Ratio ────────────────────────────────

def _salary_progression_ratio(data, summary):
    valid = [o for o in data if o.get("salario") and o.get("salario_admissao")
             and o["salario_admissao"] > 0]
    for o in valid:
        o["_ratio"] = round(o["salario"] / o["salario_admissao"], 2)
    valid.sort(key=lambda o: o["_ratio"], reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": str(top10[0]["_ratio"]).replace(".", ",") + "x",
        "headline_label": f"maior progressão salarial — {top10[0]['titulo']}",
        "chart_data": [
            {"label": o["titulo"], "value": o["_ratio"],
             "formatted": str(o["_ratio"]).replace(".", ",") + "x"}
            for o in top10
        ],
        "details": {
            "top10": [{"titulo": o["titulo"],
                       "ratio": str(o["_ratio"]).replace(".", ",") + "x",
                       "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "salario_admissao": "R$ " + _fmt_num(round(o["salario_admissao"])),
                       "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 63: High Growth + High Exposure ─────────────────────────────

def _high_growth_high_exposure(data, summary):
    occs = [o for o in data if o.get("crescimento") is not None and o.get("exposicao") is not None
            and o["crescimento"] >= 7 and o["exposicao"] >= 7]
    occs.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)

    total_w = sum(o.get("empregados") or 0 for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(len(occs)),
        "headline_label": "ocupações com alto crescimento E alta exposição à IA",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "crescimento": o["crescimento"]}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "crescimento": o["crescimento"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 64: Low Vantagem + High Workers ─────────────────────────────

def _low_vantagem_high_workers(data, summary):
    occs = [o for o in data if o.get("vantagem") is not None and o["vantagem"] <= 3
            and o.get("empregados") and o["empregados"] > 0]
    occs.sort(key=lambda o: o["empregados"], reverse=True)

    total_w = sum(o["empregados"] for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores em ocupações com baixa vantagem (≤3) da IA",
        "chart_data": [
            {"label": o["titulo"], "value": o["empregados"],
             "formatted": _fmt_num(o["empregados"]),
             "vantagem": o["vantagem"]}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "empregados": _fmt_num(o["empregados"]),
                       "vantagem": o["vantagem"], "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 65: Balanced Risk ───────────────────────────────────────────

def _balanced_risk(data, summary):
    occs = [o for o in data if o.get("exposicao") is not None
            and 4 <= o["exposicao"] <= 6
            and o.get("empregados") and o["empregados"] > 0]
    occs.sort(key=lambda o: o["empregados"], reverse=True)

    total_w = sum(o["empregados"] for o in occs)
    top10 = occs[:10]

    return {
        "headline_stat": str(len(occs)),
        "headline_label": f"ocupações na faixa média de exposição (4-6) — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o["empregados"],
             "formatted": _fmt_num(o["empregados"]),
             "exposicao": o["exposicao"]}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "empregados": _fmt_num(o["empregados"]),
                       "exposicao": o["exposicao"],
                       "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                      for o in top10],
        },
    }


# ─── Template 66: Extreme Divergence ──────────────────────────────────────

def _extreme_divergence(data, summary):
    occs = [o for o in data if o.get("exposicao") is not None and o.get("vantagem") is not None
            and abs(o["exposicao"] - o["vantagem"]) >= 5]
    occs.sort(key=lambda o: abs(o["exposicao"] - o["vantagem"]), reverse=True)

    top10 = occs[:10]
    total_w = sum(o.get("empregados") or 0 for o in occs)

    return {
        "headline_stat": str(len(occs)),
        "headline_label": "ocupações com divergência extrema entre exposição e vantagem",
        "chart_data": [
            {"label": o["titulo"], "value": abs(o["exposicao"] - o["vantagem"]),
             "formatted": str(abs(o["exposicao"] - o["vantagem"])),
             "exposicao": o["exposicao"], "vantagem": o["vantagem"]}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "vantagem": o["vantagem"],
                       "diferenca": abs(o["exposicao"] - o["vantagem"]),
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 67: Declining Well-Paid ─────────────────────────────────────

def _declining_well_paid(data, summary):
    occs = [o for o in data if o.get("saldo") is not None and o["saldo"] < 0
            and o.get("salario") and o["salario"] >= 5000]
    occs.sort(key=lambda o: o["saldo"])
    top10 = occs[:10]

    total_saldo = sum(o["saldo"] for o in occs)
    avg_sal = round(_safe_avg([o["salario"] for o in occs]))

    return {
        "headline_stat": str(len(occs)),
        "headline_label": f"ocupações bem pagas (≥R$5k) em declínio — saldo total {_fmt_num(total_saldo)}",
        "chart_data": [
            {"label": o["titulo"], "value": o["saldo"],
             "formatted": _fmt_num(o["saldo"]),
             "salary": "R$ " + _fmt_num(round(o["salario"]))}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_saldo": _fmt_num(total_saldo),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "top10": [{"titulo": o["titulo"], "saldo": _fmt_num(o["saldo"]),
                       "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 68: Growing Low-Paid ────────────────────────────────────────

def _growing_low_paid(data, summary):
    occs = [o for o in data if o.get("saldo") is not None and o["saldo"] > 0
            and o.get("salario") and o["salario"] < 2000]
    occs.sort(key=lambda o: o["saldo"], reverse=True)
    top10 = occs[:10]

    total_saldo = sum(o["saldo"] for o in occs)
    avg_sal = round(_safe_avg([o["salario"] for o in occs]))

    return {
        "headline_stat": str(len(occs)),
        "headline_label": f"ocupações de baixo salário (<R$2k) em crescimento",
        "chart_data": [
            {"label": o["titulo"], "value": o["saldo"],
             "formatted": "+" + _fmt_num(o["saldo"]),
             "salary": "R$ " + _fmt_num(round(o["salario"]))}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_saldo": "+" + _fmt_num(total_saldo),
            "avg_salario": "R$ " + _fmt_num(avg_sal),
            "top10": [{"titulo": o["titulo"], "saldo": "+" + _fmt_num(o["saldo"]),
                       "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 69: Minimum Wage Exposure ───────────────────────────────────

def _minimum_wage_exposure(data, summary):
    occs = [o for o in data if o.get("salario") and o["salario"] < 1800
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["exposicao"], reverse=True)

    total_w = sum(o.get("empregados") or 0 for o in occs)
    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    high_risk = [o for o in occs if o["exposicao"] >= 7]
    top10 = occs[:10]

    return {
        "headline_stat": str(len(occs)),
        "headline_label": f"ocupações próximas ao salário mínimo (<R$1.800) — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ","),
             "salary": "R$ " + _fmt_num(round(o["salario"]))}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "n_high_risk": len(high_risk),
            "top10": [{"titulo": o["titulo"], "exposicao": o["exposicao"],
                       "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 70: Salary Above 10k ───────────────────────────────────────

def _salary_above_10k(data, summary):
    occs = [o for o in data if o.get("salario") and o["salario"] >= 10000
            and o.get("exposicao") is not None]
    occs.sort(key=lambda o: o["salario"], reverse=True)

    total_w = sum(o.get("empregados") or 0 for o in occs)
    avg_exp = round(_safe_avg([o["exposicao"] for o in occs]), 1)
    top10 = occs[:10]

    return {
        "headline_stat": str(len(occs)),
        "headline_label": f"ocupações com salário ≥R$10k — exposição média {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": round(o["salario"]),
             "formatted": "R$ " + _fmt_num(round(o["salario"])),
             "exposicao": o["exposicao"]}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "top10": [{"titulo": o["titulo"], "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "exposicao": o["exposicao"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 71: Net Job Creation ────────────────────────────────────────

def _net_job_creation(data, summary):
    with_saldo = [o for o in data if o.get("saldo") is not None]
    total_saldo = sum(o["saldo"] for o in with_saldo)
    positive = [o for o in with_saldo if o["saldo"] > 0]
    negative = [o for o in with_saldo if o["saldo"] < 0]
    sum_pos = sum(o["saldo"] for o in positive)
    sum_neg = sum(o["saldo"] for o in negative)

    positive.sort(key=lambda o: o["saldo"], reverse=True)
    negative.sort(key=lambda o: o["saldo"])
    top5_pos = positive[:5]
    top5_neg = negative[:5]

    return {
        "headline_stat": ("+" if total_saldo >= 0 else "") + _fmt_num(total_saldo),
        "headline_label": "saldo líquido de empregos em todas as ocupações analisadas",
        "chart_data": [
            {"label": "Criação", "value": sum_pos, "formatted": "+" + _fmt_num(sum_pos)},
            {"label": "Destruição", "value": sum_neg, "formatted": _fmt_num(sum_neg)},
        ],
        "details": {
            "total_saldo": ("+" if total_saldo >= 0 else "") + _fmt_num(total_saldo),
            "n_positive": len(positive),
            "n_negative": len(negative),
            "sum_positive": "+" + _fmt_num(sum_pos),
            "sum_negative": _fmt_num(sum_neg),
            "top5_creators": [{"titulo": o["titulo"], "saldo": "+" + _fmt_num(o["saldo"])}
                              for o in top5_pos],
            "top5_destroyers": [{"titulo": o["titulo"], "saldo": _fmt_num(o["saldo"])}
                                for o in top5_neg],
        },
    }


# ─── Template 72: Salary Quintile Exposure ────────────────────────────────

def _salary_quintile_exposure(data, summary):
    valid = [o for o in data if o.get("salario") and o.get("exposicao") is not None]
    valid.sort(key=lambda o: o["salario"])
    n = len(valid)
    quintile_size = n // 5

    quintiles = []
    labels = ["Q1 (menor salário)", "Q2", "Q3", "Q4", "Q5 (maior salário)"]
    for i in range(5):
        start = i * quintile_size
        end = (i + 1) * quintile_size if i < 4 else n
        group = valid[start:end]
        avg_exp = round(_safe_avg([o["exposicao"] for o in group]), 1)
        avg_sal = round(_safe_avg([o["salario"] for o in group]))
        quintiles.append({"label": labels[i], "avg_exposicao": avg_exp,
                          "avg_salario": avg_sal, "n": len(group)})

    return {
        "headline_stat": str(quintiles[4]["avg_exposicao"]).replace(".", ","),
        "headline_label": "exposição média no quintil mais rico vs " + str(quintiles[0]["avg_exposicao"]).replace(".", ",") + " no mais pobre",
        "chart_data": [
            {"label": q["label"], "value": q["avg_exposicao"],
             "formatted": str(q["avg_exposicao"]).replace(".", ",")}
            for q in quintiles
        ],
        "details": {
            "quintiles": [{"label": q["label"],
                           "avg_exposicao": str(q["avg_exposicao"]).replace(".", ","),
                           "avg_salario": "R$ " + _fmt_num(q["avg_salario"]),
                           "n_occupations": q["n"]}
                          for q in quintiles],
        },
    }


# ─── Template 73: Exposure Impact Index ───────────────────────────────────

def _exposure_impact_index(data, summary):
    valid = [o for o in data if o.get("exposicao") is not None
             and o.get("empregados") and o["empregados"] > 0]
    for o in valid:
        o["_impact"] = o["empregados"] * o["exposicao"]
    valid.sort(key=lambda o: o["_impact"], reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": _fmt_num(top10[0]["_impact"]),
        "headline_label": f"índice de impacto máximo — {top10[0]['titulo']}",
        "chart_data": [
            {"label": o["titulo"], "value": o["_impact"],
             "formatted": _fmt_num(o["_impact"])}
            for o in top10
        ],
        "details": {
            "top10": [{"titulo": o["titulo"],
                       "impact_index": _fmt_num(o["_impact"]),
                       "empregados": _fmt_num(o["empregados"]),
                       "exposicao": o["exposicao"]}
                      for o in top10],
        },
    }


# ─── Template 74: Median Salary by Tier ───────────────────────────────────

def _median_salary_by_tier(data, summary):
    tiers = {"Baixa (0-3)": [], "Média (4-6)": [], "Alta (7-10)": []}
    for o in data:
        if o.get("exposicao") is None or not o.get("salario"):
            continue
        if o["exposicao"] <= 3:
            tiers["Baixa (0-3)"].append(o["salario"])
        elif o["exposicao"] <= 6:
            tiers["Média (4-6)"].append(o["salario"])
        else:
            tiers["Alta (7-10)"].append(o["salario"])

    results = []
    for label, sals in tiers.items():
        median = round(statistics.median(sals)) if sals else 0
        results.append({"label": label, "median": median, "n": len(sals)})

    return {
        "headline_stat": "R$ " + _fmt_num(results[2]["median"]),
        "headline_label": "salário mediano em ocupações de alta exposição",
        "chart_data": [
            {"label": r["label"], "value": r["median"],
             "formatted": "R$ " + _fmt_num(r["median"])}
            for r in results
        ],
        "details": {
            "tiers": [{"tier": r["label"], "median_salary": "R$ " + _fmt_num(r["median"]),
                       "n_occupations": r["n"]}
                      for r in results],
        },
    }


# ─── Template 75: Entry Salary vs Median ──────────────────────────────────

def _entry_salary_vs_median(data, summary):
    tiers = {"Baixa (0-3)": [], "Média (4-6)": [], "Alta (7-10)": []}
    for o in data:
        if o.get("exposicao") is None or not o.get("salario") or not o.get("salario_admissao"):
            continue
        ratio = round(o["salario_admissao"] / o["salario"] * 100, 1)
        if o["exposicao"] <= 3:
            tiers["Baixa (0-3)"].append(ratio)
        elif o["exposicao"] <= 6:
            tiers["Média (4-6)"].append(ratio)
        else:
            tiers["Alta (7-10)"].append(ratio)

    results = []
    for label, ratios in tiers.items():
        avg = round(_safe_avg(ratios), 1)
        results.append({"label": label, "avg_pct": avg, "n": len(ratios)})

    return {
        "headline_stat": _fmt_pct(results[2]["avg_pct"]),
        "headline_label": "salário de admissão vs mediano em ocupações de alta exposição",
        "chart_data": [
            {"label": r["label"], "value": r["avg_pct"],
             "formatted": _fmt_pct(r["avg_pct"])}
            for r in results
        ],
        "details": {
            "tiers": [{"tier": r["label"],
                       "avg_entry_pct": _fmt_pct(r["avg_pct"]),
                       "n_occupations": r["n"]}
                      for r in results],
        },
    }


# ─── Template 76: High Hiring Low Pay ─────────────────────────────────────

def _high_hiring_low_pay(data, summary):
    occs = [o for o in data if o.get("admissoes") and o["admissoes"] > 1000
            and o.get("salario_admissao") and o["salario_admissao"] < 1800]
    occs.sort(key=lambda o: o["admissoes"], reverse=True)
    top10 = occs[:10]

    total_admissoes = sum(o["admissoes"] for o in occs)

    return {
        "headline_stat": _fmt_num(total_admissoes),
        "headline_label": f"admissões em {len(occs)} ocupações de alta contratação e baixo salário",
        "chart_data": [
            {"label": o["titulo"], "value": o["admissoes"],
             "formatted": _fmt_num(o["admissoes"]),
             "salary": "R$ " + _fmt_num(round(o["salario_admissao"]))}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_admissoes": _fmt_num(total_admissoes),
            "top10": [{"titulo": o["titulo"], "admissoes": _fmt_num(o["admissoes"]),
                       "salario_admissao": "R$ " + _fmt_num(round(o["salario_admissao"])),
                       "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 77: Turnover Proxy ──────────────────────────────────────────

def _turnover_proxy(data, summary):
    valid = [o for o in data if o.get("admissoes") and o.get("empregados")
             and o["empregados"] > 100]
    for o in valid:
        o["_turnover"] = round(o["admissoes"] / o["empregados"] * 100, 1)
    valid.sort(key=lambda o: o["_turnover"], reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": _fmt_pct(top10[0]["_turnover"]),
        "headline_label": f"taxa de rotatividade mais alta — {top10[0]['titulo']}",
        "chart_data": [
            {"label": o["titulo"], "value": o["_turnover"],
             "formatted": _fmt_pct(o["_turnover"])}
            for o in top10
        ],
        "details": {
            "top10": [{"titulo": o["titulo"],
                       "turnover_pct": _fmt_pct(o["_turnover"]),
                       "admissoes": _fmt_num(o["admissoes"]),
                       "empregados": _fmt_num(o["empregados"]),
                       "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 78: Automation Risk Composite ───────────────────────────────

def _automation_risk_composite(data, summary):
    valid = [o for o in data if o.get("exposicao") is not None
             and o.get("vantagem") is not None and o.get("crescimento") is not None]
    for o in valid:
        o["_risk_score"] = round(o["exposicao"] + (10 - o["vantagem"]) + (10 - o["crescimento"]), 1)
    valid.sort(key=lambda o: o["_risk_score"], reverse=True)
    top10 = valid[:10]

    total_w = sum(o.get("empregados") or 0 for o in top10)

    return {
        "headline_stat": str(top10[0]["_risk_score"]).replace(".", ","),
        "headline_label": f"score composto de risco máximo — {top10[0]['titulo']}",
        "chart_data": [
            {"label": o["titulo"], "value": o["_risk_score"],
             "formatted": str(o["_risk_score"]).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "total_workers_top10": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"],
                       "risk_score": str(o["_risk_score"]).replace(".", ","),
                       "exposicao": o["exposicao"], "vantagem": o["vantagem"],
                       "crescimento": o["crescimento"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 79: Future-Proof Composite ──────────────────────────────────

def _future_proof_composite(data, summary):
    valid = [o for o in data if o.get("exposicao") is not None
             and o.get("vantagem") is not None and o.get("crescimento") is not None]
    for o in valid:
        o["_future_score"] = round((10 - o["exposicao"]) + o["vantagem"] + o["crescimento"], 1)
    valid.sort(key=lambda o: o["_future_score"], reverse=True)
    top10 = valid[:10]

    total_w = sum(o.get("empregados") or 0 for o in top10)

    return {
        "headline_stat": str(top10[0]["_future_score"]).replace(".", ","),
        "headline_label": f"score 'à prova de futuro' máximo — {top10[0]['titulo']}",
        "chart_data": [
            {"label": o["titulo"], "value": o["_future_score"],
             "formatted": str(o["_future_score"]).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "total_workers_top10": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"],
                       "future_score": str(o["_future_score"]).replace(".", ","),
                       "exposicao": o["exposicao"], "vantagem": o["vantagem"],
                       "crescimento": o["crescimento"],
                       "empregados": _fmt_num(o.get("empregados") or 0)}
                      for o in top10],
        },
    }


# ─── Template 80: Salary Variance by Grupo ────────────────────────────────

def _salary_variance_by_grupo(data, summary):
    grupos = {}
    for occ in data:
        gg = occ.get("grande_grupo")
        if not gg or not occ.get("salario"):
            continue
        if gg not in grupos:
            grupos[gg] = []
        grupos[gg].append(occ["salario"])

    short_names = {
        "MEMBROS SUPERIORES DO PODER PÚBLICO, DIRIGENTES DE ORGANIZAÇÕES DE INTERESSE PÚBLICO E DE EMPRESAS, GERENTES": "Dirigentes e Gerentes",
        "PROFISSIONAIS DAS CIÊNCIAS E DAS ARTES": "Profissionais das Ciências",
        "TÉCNICOS DE NIVEL MÉDIO": "Técnicos de Nível Médio",
        "TRABALHADORES DE SERVIÇOS ADMINISTRATIVOS": "Serviços Administrativos",
        "TRABALHADORES DOS SERVIÇOS, VENDEDORES DO COMÉRCIO EM LOJAS E MERCADOS": "Serviços e Comércio",
        "TRABALHADORES AGROPECUÁRIOS, FLORESTAIS E DA PESCA": "Agropecuária e Pesca",
        "TRABALHADORES DA PRODUÇÃO DE BENS E SERVIÇOS INDUSTRIAIS": "Produção Industrial",
        "TRABALHADORES EM SERVIÇOS DE REPARAÇÃO E MANUTENÇÃO": "Reparação e Manutenção",
        "MEMBROS DAS FORÇAS ARMADAS, POLICIAIS E BOMBEIROS MILITARES": "Forças Armadas e Polícia",
    }

    results = []
    for gg, sals in grupos.items():
        if len(sals) < 2:
            continue
        std = round(statistics.stdev(sals))
        avg = round(_safe_avg(sals))
        results.append({"grupo": short_names.get(gg, gg), "std_dev": std,
                        "avg_salary": avg, "n": len(sals)})
    results.sort(key=lambda r: r["std_dev"], reverse=True)

    return {
        "headline_stat": "R$ " + _fmt_num(results[0]["std_dev"]),
        "headline_label": f"maior desvio padrão salarial — {results[0]['grupo']}",
        "chart_data": [
            {"label": r["grupo"], "value": r["std_dev"],
             "formatted": "R$ " + _fmt_num(r["std_dev"])}
            for r in results
        ],
        "details": {
            "grupos": [{"nome": r["grupo"], "std_dev": "R$ " + _fmt_num(r["std_dev"]),
                        "avg_salary": "R$ " + _fmt_num(r["avg_salary"]),
                        "n_occupations": r["n"]}
                       for r in results],
        },
    }


# ─── Template 81: Male Dominated High Risk ────────────────────────────────

def _male_dominated_high_risk(data, summary):
    results = []
    for o in data:
        dem = o.get("demographics")
        if not dem or o.get("exposicao") is None or o["exposicao"] < 7:
            continue
        tf = dem.get("total_feminino", 0)
        tm = dem.get("total_masculino", 0)
        total = tf + tm
        if total < 100:
            continue
        pct_m = round(tm / total * 100, 1)
        if pct_m > 70:
            results.append({
                "titulo": o["titulo"],
                "pct_masculino": pct_m,
                "exposicao": o["exposicao"],
                "total_workers": total,
                "salario": o.get("salario"),
            })
    results.sort(key=lambda r: r["total_workers"], reverse=True)
    top10 = results[:10]
    total_workers = sum(r["total_workers"] for r in results)
    total_masc = sum(round(r["total_workers"] * r["pct_masculino"] / 100) for r in results)

    return {
        "headline_stat": _fmt_num(total_masc),
        "headline_label": "homens em ocupações masculinizadas de alto risco de IA",
        "chart_data": [
            {"label": r["titulo"], "value": r["pct_masculino"],
             "formatted": _fmt_pct(r["pct_masculino"]),
             "workers": _fmt_num(r["total_workers"])}
            for r in top10
        ],
        "details": {
            "total_occupations": len(results),
            "total_workers": _fmt_num(total_workers),
            "total_men": _fmt_num(total_masc),
            "top10": [{"titulo": r["titulo"], "pct_masculino": _fmt_pct(r["pct_masculino"]),
                       "exposicao": r["exposicao"], "workers": _fmt_num(r["total_workers"])}
                      for r in top10],
        },
    }


# ─── Template 82: Gender Balanced Occupations ─────────────────────────────

def _gender_balanced_occupations(data, summary):
    results = []
    for o in data:
        dem = o.get("demographics")
        if not dem:
            continue
        tf = dem.get("total_feminino", 0)
        tm = dem.get("total_masculino", 0)
        total = tf + tm
        if total < 100:
            continue
        pct_f = round(tf / total * 100, 1)
        if 45 <= pct_f <= 55:
            results.append({
                "titulo": o["titulo"],
                "pct_feminino": pct_f,
                "total_workers": total,
                "exposicao": o.get("exposicao"),
                "salario": o.get("salario"),
            })
    results.sort(key=lambda r: r["total_workers"], reverse=True)
    top10 = results[:10]
    total_workers = sum(r["total_workers"] for r in results)

    return {
        "headline_stat": str(len(results)),
        "headline_label": f"ocupações com equilíbrio de gênero (45-55%) — {_fmt_num(total_workers)} trabalhadores",
        "chart_data": [
            {"label": r["titulo"], "value": r["total_workers"],
             "formatted": _fmt_num(r["total_workers"]),
             "pct_fem": _fmt_pct(r["pct_feminino"])}
            for r in top10
        ],
        "details": {
            "n_occupations": len(results),
            "total_workers": _fmt_num(total_workers),
            "top10": [{"titulo": r["titulo"], "pct_feminino": _fmt_pct(r["pct_feminino"]),
                       "workers": _fmt_num(r["total_workers"]),
                       "exposicao": r["exposicao"]}
                      for r in top10],
        },
    }


# ─── Template 83: Race Gap by Grupo ───────────────────────────────────────

def _race_gap_by_grupo(data, summary):
    grupos = {}
    for o in data:
        gg = o.get("grande_grupo")
        dem = o.get("demographics")
        if not gg or not dem or o.get("exposicao") is None:
            continue
        if gg not in grupos:
            grupos[gg] = {"branca": 0, "negra": 0, "hr_branca": 0, "hr_negra": 0}
        b = dem.get("total_branca", 0)
        n = dem.get("total_negra", 0)
        grupos[gg]["branca"] += b
        grupos[gg]["negra"] += n
        if o["exposicao"] >= 7:
            grupos[gg]["hr_branca"] += b
            grupos[gg]["hr_negra"] += n

    short_names = {
        "MEMBROS SUPERIORES DO PODER PÚBLICO, DIRIGENTES DE ORGANIZAÇÕES DE INTERESSE PÚBLICO E DE EMPRESAS, GERENTES": "Dirigentes e Gerentes",
        "PROFISSIONAIS DAS CIÊNCIAS E DAS ARTES": "Profissionais das Ciências",
        "TÉCNICOS DE NIVEL MÉDIO": "Técnicos de Nível Médio",
        "TRABALHADORES DE SERVIÇOS ADMINISTRATIVOS": "Serviços Administrativos",
        "TRABALHADORES DOS SERVIÇOS, VENDEDORES DO COMÉRCIO EM LOJAS E MERCADOS": "Serviços e Comércio",
        "TRABALHADORES AGROPECUÁRIOS, FLORESTAIS E DA PESCA": "Agropecuária e Pesca",
        "TRABALHADORES DA PRODUÇÃO DE BENS E SERVIÇOS INDUSTRIAIS": "Produção Industrial",
        "TRABALHADORES EM SERVIÇOS DE REPARAÇÃO E MANUTENÇÃO": "Reparação e Manutenção",
        "MEMBROS DAS FORÇAS ARMADAS, POLICIAIS E BOMBEIROS MILITARES": "Forças Armadas e Polícia",
    }

    results = []
    for gg, vals in grupos.items():
        pct_b = round(vals["hr_branca"] / vals["branca"] * 100, 1) if vals["branca"] else 0
        pct_n = round(vals["hr_negra"] / vals["negra"] * 100, 1) if vals["negra"] else 0
        gap = round(pct_b - pct_n, 1)
        results.append({"grupo": short_names.get(gg, gg), "pct_branca": pct_b,
                        "pct_negra": pct_n, "gap": gap})
    results.sort(key=lambda r: abs(r["gap"]), reverse=True)

    return {
        "headline_stat": _fmt_pct(abs(results[0]["gap"])),
        "headline_label": f"maior gap racial de risco — {results[0]['grupo']}",
        "chart_data": [
            {"label": r["grupo"], "value": abs(r["gap"]),
             "formatted": _fmt_pct(abs(r["gap"]))}
            for r in results
        ],
        "details": {
            "grupos": [{"nome": r["grupo"], "pct_branca": _fmt_pct(r["pct_branca"]),
                        "pct_negra": _fmt_pct(r["pct_negra"]),
                        "gap_pp": _fmt_pct(r["gap"])}
                       for r in results],
        },
    }


# ─── Template 84: Women in Opportunity ────────────────────────────────────

def _women_in_opportunity(data, summary):
    high_opp = [o for o in data if o.get("oportunidade") is not None and o["oportunidade"] >= 7
                and o.get("demographics")]
    results = []
    for o in high_opp:
        dem = o["demographics"]
        tf = dem.get("total_feminino", 0)
        tm = dem.get("total_masculino", 0)
        total = tf + tm
        if total < 50:
            continue
        pct_f = round(tf / total * 100, 1)
        results.append({"titulo": o["titulo"], "pct_feminino": pct_f,
                        "oportunidade": o["oportunidade"], "total_workers": total})
    results.sort(key=lambda r: r["total_workers"], reverse=True)
    top10 = results[:10]

    avg_pct_f = round(_safe_avg([r["pct_feminino"] for r in results]), 1)

    return {
        "headline_stat": _fmt_pct(avg_pct_f),
        "headline_label": "participação feminina média em ocupações de alta oportunidade",
        "chart_data": [
            {"label": r["titulo"], "value": r["pct_feminino"],
             "formatted": _fmt_pct(r["pct_feminino"])}
            for r in top10
        ],
        "details": {
            "n_occupations": len(results),
            "avg_pct_feminino": _fmt_pct(avg_pct_f),
            "top10": [{"titulo": r["titulo"], "pct_feminino": _fmt_pct(r["pct_feminino"]),
                       "oportunidade": r["oportunidade"],
                       "workers": _fmt_num(r["total_workers"])}
                      for r in top10],
        },
    }


# ─── Template 85: Education Salary Matrix ─────────────────────────────────

def _education_salary_matrix(data, summary):
    matrix = {}
    for o in data:
        esc = o.get("escolaridade")
        exp = o.get("exposicao")
        sal = o.get("salario")
        if not esc or exp is None or not sal:
            continue
        if exp <= 3:
            tier = "Baixa (0-3)"
        elif exp <= 6:
            tier = "Média (4-6)"
        else:
            tier = "Alta (7-10)"
        key = (esc, tier)
        if key not in matrix:
            matrix[key] = []
        matrix[key].append(sal)

    results = []
    for (esc, tier), sals in matrix.items():
        results.append({"escolaridade": esc, "tier": tier,
                        "avg_salary": round(_safe_avg(sals)),
                        "n": len(sals)})
    results.sort(key=lambda r: r["avg_salary"], reverse=True)
    top10 = results[:10]

    return {
        "headline_stat": "R$ " + _fmt_num(top10[0]["avg_salary"]),
        "headline_label": f"maior salário médio — {top10[0]['escolaridade']} + exposição {top10[0]['tier']}",
        "chart_data": [
            {"label": f"{r['escolaridade']} / {r['tier']}", "value": r["avg_salary"],
             "formatted": "R$ " + _fmt_num(r["avg_salary"])}
            for r in top10
        ],
        "details": {
            "matrix": [{"escolaridade": r["escolaridade"], "tier": r["tier"],
                        "avg_salary": "R$ " + _fmt_num(r["avg_salary"]),
                        "n_occupations": r["n"]}
                       for r in results],
        },
    }


# ─── Template 86: High Education Low Salary ───────────────────────────────

def _high_education_low_salary(data, summary):
    high_edu = ["Superior Completo", "Mestrado", "Doutorado"]
    occs = [o for o in data if o.get("escolaridade") in high_edu
            and o.get("salario") and o["salario"] < 4000]
    occs.sort(key=lambda o: o["salario"])
    top10 = occs[:10]

    total_w = sum(o.get("empregados") or 0 for o in occs)

    return {
        "headline_stat": str(len(occs)),
        "headline_label": f"ocupações de alta escolaridade com salário < R$4k",
        "chart_data": [
            {"label": o["titulo"], "value": round(o["salario"]),
             "formatted": "R$ " + _fmt_num(round(o["salario"])),
             "education": o["escolaridade"]}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "escolaridade": o["escolaridade"],
                       "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 87: Low Education High Salary ───────────────────────────────

def _low_education_high_salary(data, summary):
    low_edu = ["Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto"]
    occs = [o for o in data if o.get("escolaridade") in low_edu
            and o.get("salario") and o["salario"] > 5000]
    occs.sort(key=lambda o: o["salario"], reverse=True)
    top10 = occs[:10]

    total_w = sum(o.get("empregados") or 0 for o in occs)

    return {
        "headline_stat": str(len(occs)),
        "headline_label": "ocupações de baixa escolaridade com salário > R$5k",
        "chart_data": [
            {"label": o["titulo"], "value": round(o["salario"]),
             "formatted": "R$ " + _fmt_num(round(o["salario"])),
             "education": o["escolaridade"]}
            for o in top10
        ],
        "details": {
            "n_occupations": len(occs),
            "total_workers": _fmt_num(total_w),
            "top10": [{"titulo": o["titulo"], "salario": "R$ " + _fmt_num(round(o["salario"])),
                       "escolaridade": o["escolaridade"],
                       "exposicao": o.get("exposicao")}
                      for o in top10],
        },
    }


# ─── Template 88: Escolaridade Distribution ───────────────────────────────

def _escolaridade_distribution(data, summary):
    counts = {}
    for o in data:
        esc = o.get("escolaridade")
        if not esc:
            continue
        counts[esc] = counts.get(esc, 0) + 1

    total = sum(counts.values())
    results = [{"level": k, "count": v, "pct": round(v / total * 100, 1)}
               for k, v in counts.items()]
    results.sort(key=lambda r: r["count"], reverse=True)

    return {
        "headline_stat": results[0]["level"],
        "headline_label": f"escolaridade mais comum — {_fmt_pct(results[0]['pct'])} das ocupações",
        "chart_data": [
            {"label": r["level"], "value": r["count"],
             "formatted": _fmt_pct(r["pct"])}
            for r in results
        ],
        "details": {
            "total_occupations": total,
            "distribution": [{"escolaridade": r["level"], "count": r["count"],
                              "pct": _fmt_pct(r["pct"])}
                             for r in results],
        },
    }


# ─── Template 89: State Salary Ranking ────────────────────────────────────

def _state_salary_ranking(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        states.append({"uf": info["nome"], "avg_salary": info.get("avg_salary", 0),
                       "total_workers": info.get("total_workers", 0)})
    states.sort(key=lambda s: s["avg_salary"], reverse=True)

    return {
        "headline_stat": "R$ " + _fmt_num(round(states[0]["avg_salary"])),
        "headline_label": f"maior salário médio — {states[0]['uf']}",
        "chart_data": [
            {"label": s["uf"], "value": round(s["avg_salary"]),
             "formatted": "R$ " + _fmt_num(round(s["avg_salary"]))}
            for s in states
        ],
        "details": {
            "top_state": states[0]["uf"],
            "top_salary": "R$ " + _fmt_num(round(states[0]["avg_salary"])),
            "bottom_state": states[-1]["uf"],
            "bottom_salary": "R$ " + _fmt_num(round(states[-1]["avg_salary"])),
            "states": [{"uf": s["uf"], "avg_salary": "R$ " + _fmt_num(round(s["avg_salary"])),
                        "workers": _fmt_num(s["total_workers"])}
                       for s in states],
        },
    }


# ─── Template 90: State Workforce Ranking ─────────────────────────────────

def _state_workforce_ranking(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        states.append({"uf": info["nome"], "total_workers": info.get("total_workers", 0),
                       "avg_salary": info.get("avg_salary", 0)})
    states.sort(key=lambda s: s["total_workers"], reverse=True)
    total = sum(s["total_workers"] for s in states)

    return {
        "headline_stat": _fmt_num(states[0]["total_workers"]),
        "headline_label": f"maior força de trabalho — {states[0]['uf']}",
        "chart_data": [
            {"label": s["uf"], "value": s["total_workers"],
             "formatted": _fmt_num(s["total_workers"])}
            for s in states[:10]
        ],
        "details": {
            "total_national": _fmt_num(total),
            "states": [{"uf": s["uf"], "workers": _fmt_num(s["total_workers"]),
                        "pct": _fmt_pct(round(s["total_workers"] / total * 100, 1)) if total else "0%"}
                       for s in states],
        },
    }


# ─── Template 91: State High Risk Workers ─────────────────────────────────

def _state_high_risk_workers(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        total_w = info.get("total_workers", 0)
        avg_exp = info.get("avg_exposicao", 0)
        # Estimate: if avg exposure >= 7, all workers are "high risk"
        # Otherwise, scale proportionally
        hr_estimate = round(total_w * min(avg_exp / 10, 1))
        states.append({"uf": info["nome"], "total_workers": total_w,
                       "avg_exposicao": avg_exp, "hr_estimate": hr_estimate})
    states.sort(key=lambda s: s["hr_estimate"], reverse=True)

    total_hr = sum(s["hr_estimate"] for s in states)

    return {
        "headline_stat": _fmt_num(total_hr),
        "headline_label": "trabalhadores em risco estimado em todo o Brasil",
        "chart_data": [
            {"label": s["uf"], "value": s["hr_estimate"],
             "formatted": _fmt_num(s["hr_estimate"])}
            for s in states[:10]
        ],
        "details": {
            "total_high_risk": _fmt_num(total_hr),
            "states": [{"uf": s["uf"], "hr_estimate": _fmt_num(s["hr_estimate"]),
                        "total_workers": _fmt_num(s["total_workers"]),
                        "avg_exposicao": str(round(s["avg_exposicao"], 1)).replace(".", ",")}
                       for s in states[:10]],
        },
    }


# ─── Template 92: Southeast Dominance ─────────────────────────────────────

def _southeast_dominance(data, summary):
    se_codes = ["35", "33", "31", "32"]
    por_uf = summary["por_uf"]
    national = sum(v["total_workers"] for v in por_uf.values())

    se_workers = 0
    se_salaries = []
    se_exposicoes = []
    rest_workers = 0
    rest_salaries = []
    rest_exposicoes = []
    for code, info in por_uf.items():
        w = info.get("total_workers", 0)
        if code in se_codes:
            se_workers += w
            if info.get("avg_salary"):
                se_salaries.append(info["avg_salary"])
            if info.get("avg_exposicao"):
                se_exposicoes.append(info["avg_exposicao"])
        else:
            rest_workers += w
            if info.get("avg_salary"):
                rest_salaries.append(info["avg_salary"])
            if info.get("avg_exposicao"):
                rest_exposicoes.append(info["avg_exposicao"])

    pct_se = round(se_workers / national * 100, 1) if national else 0

    return {
        "headline_stat": _fmt_pct(pct_se),
        "headline_label": "dos trabalhadores formais estão no Sudeste (SP+RJ+MG+ES)",
        "chart_data": [
            {"label": "Sudeste", "value": se_workers, "formatted": _fmt_num(se_workers)},
            {"label": "Restante", "value": rest_workers, "formatted": _fmt_num(rest_workers)},
        ],
        "details": {
            "se_workers": _fmt_num(se_workers),
            "rest_workers": _fmt_num(rest_workers),
            "pct_se": _fmt_pct(pct_se),
            "se_avg_salary": "R$ " + _fmt_num(round(_safe_avg(se_salaries))),
            "rest_avg_salary": "R$ " + _fmt_num(round(_safe_avg(rest_salaries))),
            "se_avg_exposicao": str(round(_safe_avg(se_exposicoes), 1)).replace(".", ","),
            "rest_avg_exposicao": str(round(_safe_avg(rest_exposicoes), 1)).replace(".", ","),
        },
    }


# ─── Template 93: South Prosperity ────────────────────────────────────────

def _south_prosperity(data, summary):
    s_codes = ["42", "41", "43"]
    por_uf = summary["por_uf"]
    national = sum(v["total_workers"] for v in por_uf.values())

    states = []
    total_s = 0
    salaries = []
    exposicoes = []
    for code in s_codes:
        info = por_uf.get(code, {})
        w = info.get("total_workers", 0)
        total_s += w
        if info.get("avg_salary"):
            salaries.append(info["avg_salary"])
        if info.get("avg_exposicao"):
            exposicoes.append(info["avg_exposicao"])
        states.append({"uf": info.get("nome", code), "workers": w,
                        "avg_salary": info.get("avg_salary", 0),
                        "avg_exposicao": info.get("avg_exposicao", 0)})
    states.sort(key=lambda s: s["workers"], reverse=True)
    pct_national = round(total_s / national * 100, 1) if national else 0

    return {
        "headline_stat": _fmt_num(total_s),
        "headline_label": f"trabalhadores no Sul — {_fmt_pct(pct_national)} do Brasil",
        "chart_data": [
            {"label": s["uf"], "value": s["workers"], "formatted": _fmt_num(s["workers"])}
            for s in states
        ],
        "details": {
            "total_workers": _fmt_num(total_s),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(round(_safe_avg(salaries))),
            "avg_exposicao": str(round(_safe_avg(exposicoes), 1)).replace(".", ","),
            "states": [{"uf": s["uf"], "workers": _fmt_num(s["workers"]),
                        "avg_salary": "R$ " + _fmt_num(round(s["avg_salary"])),
                        "avg_exposicao": str(round(s["avg_exposicao"], 1)).replace(".", ",")}
                       for s in states],
        },
    }


# ─── Template 94: Northeast Tech Hubs ─────────────────────────────────────

def _northeast_tech_hubs(data, summary):
    hub_codes = ["23", "26"]  # CE, PE
    ne_other_codes = ["21", "22", "24", "25", "27", "28", "29"]
    por_uf = summary["por_uf"]

    hubs_workers = 0
    hubs_salaries = []
    hubs_exposicoes = []
    other_workers = 0
    other_salaries = []
    other_exposicoes = []
    for code in hub_codes:
        info = por_uf.get(code, {})
        hubs_workers += info.get("total_workers", 0)
        if info.get("avg_salary"):
            hubs_salaries.append(info["avg_salary"])
        if info.get("avg_exposicao"):
            hubs_exposicoes.append(info["avg_exposicao"])
    for code in ne_other_codes:
        info = por_uf.get(code, {})
        other_workers += info.get("total_workers", 0)
        if info.get("avg_salary"):
            other_salaries.append(info["avg_salary"])
        if info.get("avg_exposicao"):
            other_exposicoes.append(info["avg_exposicao"])

    return {
        "headline_stat": _fmt_num(hubs_workers),
        "headline_label": "trabalhadores em CE+PE — os hubs tech do Nordeste",
        "chart_data": [
            {"label": "CE + PE (hubs)", "value": hubs_workers, "formatted": _fmt_num(hubs_workers)},
            {"label": "Restante do NE", "value": other_workers, "formatted": _fmt_num(other_workers)},
        ],
        "details": {
            "hubs_workers": _fmt_num(hubs_workers),
            "other_ne_workers": _fmt_num(other_workers),
            "hubs_avg_salary": "R$ " + _fmt_num(round(_safe_avg(hubs_salaries))),
            "other_avg_salary": "R$ " + _fmt_num(round(_safe_avg(other_salaries))),
            "hubs_avg_exposicao": str(round(_safe_avg(hubs_exposicoes), 1)).replace(".", ","),
            "other_avg_exposicao": str(round(_safe_avg(other_exposicoes), 1)).replace(".", ","),
        },
    }


# ─── Template 95: Frontier States ─────────────────────────────────────────

def _frontier_states(data, summary):
    f_codes = ["51", "50", "52"]  # MT, MS, GO
    por_uf = summary["por_uf"]
    national = sum(v["total_workers"] for v in por_uf.values())

    states = []
    total_f = 0
    salaries = []
    exposicoes = []
    for code in f_codes:
        info = por_uf.get(code, {})
        w = info.get("total_workers", 0)
        total_f += w
        if info.get("avg_salary"):
            salaries.append(info["avg_salary"])
        if info.get("avg_exposicao"):
            exposicoes.append(info["avg_exposicao"])
        states.append({"uf": info.get("nome", code), "workers": w,
                        "avg_salary": info.get("avg_salary", 0),
                        "avg_exposicao": info.get("avg_exposicao", 0)})
    states.sort(key=lambda s: s["workers"], reverse=True)
    pct_national = round(total_f / national * 100, 1) if national else 0

    return {
        "headline_stat": _fmt_num(total_f),
        "headline_label": f"trabalhadores na fronteira agrícola (MT+MS+GO) — {_fmt_pct(pct_national)} do Brasil",
        "chart_data": [
            {"label": s["uf"], "value": s["workers"], "formatted": _fmt_num(s["workers"])}
            for s in states
        ],
        "details": {
            "total_workers": _fmt_num(total_f),
            "pct_national": _fmt_pct(pct_national),
            "avg_salary": "R$ " + _fmt_num(round(_safe_avg(salaries))),
            "avg_exposicao": str(round(_safe_avg(exposicoes), 1)).replace(".", ","),
            "states": [{"uf": s["uf"], "workers": _fmt_num(s["workers"]),
                        "avg_salary": "R$ " + _fmt_num(round(s["avg_salary"])),
                        "avg_exposicao": str(round(s["avg_exposicao"], 1)).replace(".", ",")}
                       for s in states],
        },
    }


# ─── Template 96: Smallest Workforce States ───────────────────────────────

def _smallest_workforce_states(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        states.append({"uf": info["nome"], "total_workers": info.get("total_workers", 0),
                       "avg_salary": info.get("avg_salary", 0),
                       "avg_exposicao": info.get("avg_exposicao", 0)})
    states.sort(key=lambda s: s["total_workers"])
    bottom5 = states[:5]
    total_b5 = sum(s["total_workers"] for s in bottom5)
    national = sum(s["total_workers"] for s in states)
    pct = round(total_b5 / national * 100, 1) if national else 0

    return {
        "headline_stat": _fmt_num(total_b5),
        "headline_label": f"trabalhadores nos 5 menores estados — {_fmt_pct(pct)} do Brasil",
        "chart_data": [
            {"label": s["uf"], "value": s["total_workers"],
             "formatted": _fmt_num(s["total_workers"])}
            for s in bottom5
        ],
        "details": {
            "total_workers": _fmt_num(total_b5),
            "pct_national": _fmt_pct(pct),
            "bottom5": [{"uf": s["uf"], "workers": _fmt_num(s["total_workers"]),
                         "avg_salary": "R$ " + _fmt_num(round(s["avg_salary"])),
                         "avg_exposicao": str(round(s["avg_exposicao"], 1)).replace(".", ",")}
                        for s in bottom5],
        },
    }


# ─── Template Registry ──────────────────────────────────────────────────────

TEMPLATES = [
    {
        "id": "gender-risk-gap",
        "category": "Demografia",
        "tags": ["gênero", "risco", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _gender_risk_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença de gênero na exposição à IA no mercado de trabalho brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {pct_feminino} das mulheres ({high_risk_feminino} de {total_feminino}) estão em ocupações de alto risco
- {pct_masculino} dos homens ({high_risk_masculino} de {total_masculino}) estão em ocupações de alto risco
- Diferença: {gap_pp} pontos percentuais

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "race-risk-gap",
        "category": "Demografia",
        "tags": ["raça", "risco", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _race_risk_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença racial na exposição à IA no mercado de trabalho brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {pct_branca} dos trabalhadores brancos ({high_risk_branca} de {total_branca}) estão em alto risco
- {pct_negra} dos trabalhadores negros ({high_risk_negra} de {total_negra}) estão em alto risco
- Diferença: {gap_pp} pontos percentuais
- Nota: "negra" = preta + parda (classificação IBGE)

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "state-exposure-ranking",
        "category": "Regional",
        "tags": ["estados", "UF", "exposição", "regional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_exposure_ranking,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre quais estados brasileiros têm maior exposição média à IA.

DADOS (use APENAS estes números, não invente dados):
- Estado líder: {top_state} com exposição média de {top_score}
- Último: {bottom_state} com {bottom_score}
- Média nacional: {national_avg}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "most-exposed-top10",
        "category": "Ocupações",
        "tags": ["ocupações", "exposição", "ranking"],
        "chart_type": "ranking_table",
        "analysis_fn": _most_exposed_top10,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as 10 ocupações mais expostas à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Top 10 ocupações: {top10}
- Total de trabalhadores nestas 10 ocupações: {total_workers_top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "grupo-comparison",
        "category": "Setores",
        "tags": ["grande grupo", "setores", "comparação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _grupo_comparison,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando os grandes grupos ocupacionais (CBO) em termos de exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Grupos ordenados por exposição: {grupos}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "growth-vs-decline",
        "category": "Mercado",
        "tags": ["saldo", "crescimento", "declínio", "CAGED"],
        "chart_type": "comparison_pair",
        "analysis_fn": _growth_vs_decline,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o saldo de contratações (CAGED) e como se relaciona com a exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- {n_growing} ocupações com saldo positivo (total: {total_saldo_pos})
- {n_declining} ocupações com saldo negativo (total: {total_saldo_neg})
- Exposição média das que crescem: {avg_exposicao_growing}
- Exposição média das que declinam: {avg_exposicao_declining}
- Top 5 crescendo: {top_growing}
- Top 5 declinando: {top_declining}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # ── New templates 7-18 ──────────────────────────────────────────────────
    {
        "id": "safest-large-occupations",
        "category": "Ocupações",
        "tags": ["ocupações", "baixo risco", "segurança"],
        "chart_type": "ranking_table",
        "analysis_fn": _safest_large_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações grandes (>5.000 trabalhadores) mais protegidas da IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Top 10 ocupações mais seguras: {top10}
- Total de trabalhadores nestas ocupações: {total_workers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "highest-opportunity",
        "category": "Ocupações",
        "tags": ["oportunidade", "vantagem", "crescimento"],
        "chart_type": "ranking_table",
        "analysis_fn": _highest_opportunity,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as 10 ocupações com maior oportunidade de IA no Brasil — onde a IA mais beneficia os trabalhadores.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por oportunidade: {top10}
- Total de trabalhadores: {total_workers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "salary-vs-exposure",
        "category": "Mercado",
        "tags": ["salário", "exposição", "desigualdade"],
        "chart_type": "comparison_pair",
        "analysis_fn": _salary_vs_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a relação entre salário e exposição à IA: ocupações mais expostas pagam mais ou menos?

DADOS (use APENAS estes números, não invente dados):
- Salário médio em ocupações de alta exposição (≥7): {avg_salary_high} ({n_high} ocupações)
- Salário médio em ocupações de baixa exposição (≤3): {avg_salary_low} ({n_low} ocupações)
- Razão: {ratio}x

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "augmented-vs-automated",
        "category": "Setores",
        "tags": ["automação", "potencialização", "vantagem"],
        "chart_type": "comparison_pair",
        "analysis_fn": _augmented_vs_automated,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença entre ocupações potencializadas pela IA (alta exposição + alta vantagem) e ameaçadas (alta exposição + baixa vantagem).

DADOS (use APENAS estes números, não invente dados):
- {n_augmented} ocupações potencializadas ({total_augmented} trabalhadores)
- {n_automated} ocupações ameaçadas ({total_automated} trabalhadores)
- Top 5 potencializadas: {top_augmented}
- Top 5 ameaçadas: {top_automated}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "female-dominated-high-risk",
        "category": "Demografia",
        "tags": ["gênero", "feminização", "risco"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _female_dominated_high_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações majoritariamente femininas que enfrentam alto risco de IA.

DADOS (use APENAS estes números, não invente dados):
- {total_occupations} ocupações feminizadas (>55%% mulheres) com exposição ≥7
- {total_women} mulheres afetadas de {total_workers} trabalhadores total
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "hiring-into-risk",
        "category": "Mercado",
        "tags": ["contratação", "risco", "CAGED", "paradoxo"],
        "chart_type": "ranking_table",
        "analysis_fn": _hiring_into_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o paradoxo: o Brasil está contratando em massa para ocupações com alto risco de disrupção por IA.

DADOS (use APENAS estes números, não invente dados):
- {total_occupations} ocupações com saldo positivo E exposição ≥7
- Saldo total nestas ocupações: {total_saldo}
- Top 10 contratando para o risco: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "state-vulnerability",
        "category": "Regional",
        "tags": ["estados", "vulnerabilidade", "salário", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_salary_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre quais estados são mais vulneráveis à IA: alta exposição combinada com salários baixos.

DADOS (use APENAS estes números, não invente dados):
- Top 10 estados mais vulneráveis (alta exposição / baixo salário): {worst10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "education-exposure",
        "category": "Educação",
        "tags": ["escolaridade", "exposição", "formação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _education_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como o nível de escolaridade se relaciona com a exposição à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Níveis de escolaridade e exposição média: {levels}
- Maior exposição: {highest} com score {highest_score}
- Menor exposição: {lowest} com score {lowest_score}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "entry-salary-gap",
        "category": "Mercado",
        "tags": ["salário", "entrada", "admissão", "jovens"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _entry_salary_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os salários de entrada em ocupações de alta vs baixa exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Salário de entrada (alta exposição): {entry_high} → mediano: {full_high} (gap de {gap_high_pct})
- Salário de entrada (baixa exposição): {entry_low} → mediano: {full_low} (gap de {gap_low_pct})
- {n_high} ocupações de alta exposição, {n_low} de baixa

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "ai-winners",
        "category": "Ocupações",
        "tags": ["oportunidade", "salário", "vencedores"],
        "chart_type": "ranking_table",
        "analysis_fn": _ai_winners,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações "vencedoras" da IA: alta oportunidade E salário acima de R$ 5.000.

DADOS (use APENAS estes números, não invente dados):
- {total_occupations} ocupações com oportunidade ≥7 e salário ≥R$ 5.000
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "north-south-divide",
        "category": "Regional",
        "tags": ["regional", "desigualdade", "Norte", "Sul"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _north_south_divide,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a divisão regional na exposição à IA: Norte/Nordeste vs Sul/Sudeste vs Centro-Oeste.

DADOS (use APENAS estes números, não invente dados):
- Regiões comparadas: {regions}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "telemarketing-spotlight",
        "category": "Ocupações",
        "tags": ["telemarketing", "caso", "feminização", "automação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _telemarketing_spotlight,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) como um estudo de caso profundo sobre operadores de telemarketing — uma das ocupações mais expostas à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Ocupação: {titulo}
- Trabalhadores: {empregados}
- Exposição: {exposicao}/10
- Salário mediano: {salario}
- Saldo CAGED: {saldo}
- Porcentagem feminina: {pct_feminino}
- Top estados: {top_states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # ── Templates 19-36 ─────────────────────────────────────────────────────
    {
        "id": "risk-tier-distribution",
        "category": "Mercado",
        "tags": ["distribuição", "risco", "trabalhadores"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _risk_tier_distribution,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como os trabalhadores brasileiros se distribuem entre faixas de risco de IA.

DADOS (use APENAS estes números, não invente dados):
- Faixas de risco: {tiers}
- Total de trabalhadores: {total_workers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "lowest-paid-high-risk",
        "category": "Mercado",
        "tags": ["salário", "risco", "precarização"],
        "chart_type": "ranking_table",
        "analysis_fn": _lowest_paid_high_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os trabalhadores mais vulneráveis: salário abaixo de R$ 3.000 E alta exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- {total_occupations} ocupações com salário <R$ 3.000 e exposição ≥7
- {total_workers} trabalhadores afetados
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "healthcare-sector",
        "category": "Setores",
        "tags": ["saúde", "médicos", "enfermagem"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _healthcare_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no setor de saúde brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de saúde analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "education-sector",
        "category": "Educação",
        "tags": ["professores", "ensino", "educação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _education_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA na profissão docente no Brasil.

DADOS (use APENAS estes números, não invente dados):
- {n_teachers} categorias de professores
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- {high_risk_count} categorias em alto risco ({high_risk_workers} professores)
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "tech-sector-paradox",
        "category": "Setores",
        "tags": ["tecnologia", "TI", "oportunidade", "paradoxo"],
        "chart_type": "ranking_table",
        "analysis_fn": _tech_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o paradoxo do setor de TI: alta exposição à IA, mas também alta oportunidade.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de TI
- Exposição média: {avg_exposicao}, Oportunidade média: {avg_oportunidade}
- Salário médio: {avg_salario}
- Total de trabalhadores: {total_workers}
- Top 10 por oportunidade: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "sao-paulo-deep-dive",
        "category": "Regional",
        "tags": ["São Paulo", "SP", "metrópole"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _sao_paulo_deep_dive,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA em São Paulo, o maior mercado de trabalho do Brasil.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores em SP: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "admin-jobs-crisis",
        "category": "Setores",
        "tags": ["administrativo", "escritório", "automação"],
        "chart_type": "ranking_table",
        "analysis_fn": _admin_jobs_crisis,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a crise nos empregos administrativos — o grupo mais exposto à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações administrativas
- {total_workers} trabalhadores
- Exposição média: {avg_exposicao}
- Salário médio: {avg_salario}
- Saldo CAGED total: {total_saldo}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "middle-class-squeeze",
        "category": "Mercado",
        "tags": ["classe média", "salário", "risco"],
        "chart_type": "ranking_table",
        "analysis_fn": _middle_class_squeeze,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o aperto da classe média: trabalhadores com salário de R$ 2.500 a R$ 5.000 enfrentando alto risco de IA.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de classe média com exposição ≥7
- {total_workers} trabalhadores afetados
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "opportunity-desert",
        "category": "Ocupações",
        "tags": ["sem saída", "oportunidade", "exposição"],
        "chart_type": "ranking_table",
        "analysis_fn": _opportunity_desert,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações "sem saída": alta exposição à IA E baixa oportunidade de benefício.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com exposição ≥6 e oportunidade ≤3
- {total_workers} trabalhadores nessas ocupações
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "crescimento-leaders",
        "category": "Ocupações",
        "tags": ["crescimento", "demanda", "futuro"],
        "chart_type": "ranking_table",
        "analysis_fn": _crescimento_leaders,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações onde a IA mais impulsiona a demanda por trabalhadores.

DADOS (use APENAS estes números, não invente dados):
- Top 10 ocupações por crescimento impulsionado pela IA: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "biggest-job-losses",
        "category": "Mercado",
        "tags": ["demissões", "saldo negativo", "declínio"],
        "chart_type": "ranking_table",
        "analysis_fn": _biggest_job_losses,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações que mais perdem empregos no Brasil e sua relação com IA.

DADOS (use APENAS estes números, não invente dados):
- {total_losing} ocupações com saldo negativo (total: {total_loss} empregos perdidos)
- {pct_high_exposure} dessas ocupações têm alta exposição à IA
- Top 10 maiores perdas: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "agriculture-resilience",
        "category": "Setores",
        "tags": ["agropecuária", "resiliência", "campo"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _agriculture_resilience,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a resiliência do setor agropecuário brasileiro frente à IA.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações agropecuárias
- Exposição média: {avg_exposicao} (a mais baixa entre os setores)
- Salário médio: {avg_salario}
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "public-sector-exposure",
        "category": "Setores",
        "tags": ["setor público", "governo", "servidores"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _public_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a exposição do setor público brasileiro à IA.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações do setor público
- Exposição média: {avg_exposicao}
- Salário médio: {avg_salario}
- Total de servidores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "high-salary-threatened",
        "category": "Ocupações",
        "tags": ["alto salário", "ameaça", "elite"],
        "chart_type": "ranking_table",
        "analysis_fn": _high_salary_low_advantage,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre profissionais de alto salário (≥R$ 8.000) que estão ameaçados pela IA.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com salário ≥R$ 8K, exposição ≥7, vantagem ≤5
- {total_workers} trabalhadores
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "vantagem-leaders",
        "category": "Ocupações",
        "tags": ["vantagem", "produtividade", "IA como aliada"],
        "chart_type": "ranking_table",
        "analysis_fn": _vantagem_leaders,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações que mais se beneficiam da IA — onde a tecnologia é aliada do trabalhador.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por vantagem da IA: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "young-workers-entry",
        "category": "Mercado",
        "tags": ["jovens", "admissões", "primeiro emprego"],
        "chart_type": "ranking_table",
        "analysis_fn": _young_workers_entry,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre onde os novos trabalhadores estão entrando e o risco de IA que enfrentam.

DADOS (use APENAS estes números, não invente dados):
- {total_admissoes} admissões nos últimos 12 meses
- {pct_high_risk} entraram em ocupações de alto risco ({n_high_risk} ocupações)
- Top 10 que mais contratam: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "exposure-inequality-states",
        "category": "Regional",
        "tags": ["desigualdade", "estados", "pobreza"],
        "chart_type": "comparison_pair",
        "analysis_fn": _exposure_inequality,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a desigualdade de exposição à IA entre estados ricos e pobres do Brasil.

DADOS (use APENAS estes números, não invente dados):
- 5 estados mais pobres: {poorest5} — exposição média: {avg_exp_poor}
- 5 estados mais ricos: {richest5} — exposição média: {avg_exp_rich}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "race-gender-intersection",
        "category": "Demografia",
        "tags": ["interseccionalidade", "raça", "gênero"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _race_gender_intersection,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a análise interseccional de raça e gênero na exposição à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Grupos por risco estimado: {groups}
- Risco feminino geral: {pct_feminino}
- Risco masculino geral: {pct_masculino}
- Risco brancos: {pct_branca}
- Risco negros: {pct_negra}
- Nota: {note}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "rio-de-janeiro-deep-dive",
        "category": "Regional",
        "tags": ["Rio de Janeiro", "RJ", "metrópole"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _rio_de_janeiro_deep_dive,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no Rio de Janeiro, o segundo maior mercado de trabalho do Brasil.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores no RJ: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "minas-gerais-deep-dive",
        "category": "Regional",
        "tags": ["Minas Gerais", "MG", "interior"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _minas_gerais_deep_dive,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA em Minas Gerais, terceiro estado em força de trabalho.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores em MG: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "bahia-deep-dive",
        "category": "Regional",
        "tags": ["Bahia", "BA", "Nordeste"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _bahia_deep_dive,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA na Bahia, o maior mercado de trabalho do Nordeste.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores na BA: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "rio-grande-sul-deep-dive",
        "category": "Regional",
        "tags": ["Rio Grande do Sul", "RS", "Sul"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _rio_grande_sul_deep_dive,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no Rio Grande do Sul.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores no RS: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "parana-deep-dive",
        "category": "Regional",
        "tags": ["Paraná", "PR", "Sul"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _parana_deep_dive,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no Paraná.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores no PR: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "distrito-federal-deep-dive",
        "category": "Regional",
        "tags": ["Distrito Federal", "DF", "Brasília"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _distrito_federal_deep_dive,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no Distrito Federal, a capital com forte presença do setor público.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores no DF: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "nordeste-workforce",
        "category": "Regional",
        "tags": ["Nordeste", "regional", "desigualdade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _nordeste_workforce,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a força de trabalho do Nordeste e sua exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores no Nordeste: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Estados: {states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "amazonia-states",
        "category": "Regional",
        "tags": ["Amazônia", "Norte", "regional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _amazonia_states,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a força de trabalho da Amazônia Legal e sua exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores na Amazônia: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Estados: {states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "financial-sector",
        "category": "Setores",
        "tags": ["financeiro", "bancos", "contabilidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _financial_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no setor financeiro brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações financeiras analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "legal-sector",
        "category": "Setores",
        "tags": ["jurídico", "advocacia", "direito"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _legal_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no setor jurídico brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações jurídicas analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "engineering-sector",
        "category": "Setores",
        "tags": ["engenharia", "infraestrutura", "técnico"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _engineering_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA nas engenharias brasileiras.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de engenharia analisadas
- Exposição média: {avg_exposicao}
- Salário médio: {avg_salario}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "construction-sector",
        "category": "Setores",
        "tags": ["construção civil", "pedreiro", "obras"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _construction_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA na construção civil brasileira.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações da construção analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "transport-logistics",
        "category": "Setores",
        "tags": ["transporte", "logística", "motoristas"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _transport_logistics,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no setor de transporte e logística brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de transporte/logística analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "tourism-hospitality",
        "category": "Setores",
        "tags": ["turismo", "hotelaria", "gastronomia"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _tourism_hospitality,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no turismo e hotelaria brasileira.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de turismo/hotelaria analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "creative-industries",
        "category": "Setores",
        "tags": ["criativo", "arte", "mídia", "design"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _creative_industries,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA nas indústrias criativas brasileiras.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações criativas analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "security-sector",
        "category": "Setores",
        "tags": ["segurança", "vigilância", "defesa"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _security_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no setor de segurança brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de segurança analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "manufacturing-detailed",
        "category": "Setores",
        "tags": ["produção industrial", "fábrica", "manufatura"],
        "chart_type": "ranking_table",
        "analysis_fn": _manufacturing_detailed,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA na produção industrial brasileira.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações industriais
- {total_workers} trabalhadores
- Exposição média: {avg_exposicao}
- Salário médio: {avg_salario}
- Saldo CAGED total: {total_saldo}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "commerce-retail",
        "category": "Setores",
        "tags": ["comércio", "varejo", "vendas"],
        "chart_type": "ranking_table",
        "analysis_fn": _commerce_retail,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no comércio e serviços brasileiros.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de comércio/serviços
- {total_workers} trabalhadores
- Exposição média: {avg_exposicao}
- Salário médio: {avg_salario}
- Saldo CAGED total: {total_saldo}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "care-economy",
        "category": "Setores",
        "tags": ["cuidado", "assistência", "doméstico"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _care_economy,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA na economia do cuidado no Brasil.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de cuidado analisadas
- Exposição média: {avg_exposicao}
- Salário médio: {avg_salario}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "food-industry",
        "category": "Setores",
        "tags": ["alimentos", "gastronomia", "frigorífico"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _food_industry,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA na indústria alimentícia brasileira.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações alimentícias analisadas
- Exposição média: {avg_exposicao}
- Total de trabalhadores: {total_workers}
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "exposure-10-spotlight",
        "category": "Ocupações",
        "tags": ["exposição máxima", "risco extremo", "IA"],
        "chart_type": "ranking_table",
        "analysis_fn": _exposure_10_spotlight,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com exposição máxima (10/10) à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com exposição 10
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salario}
- Top 10 por empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "exposure-1-spotlight",
        "category": "Ocupações",
        "tags": ["exposição mínima", "baixo risco", "IA"],
        "chart_type": "ranking_table",
        "analysis_fn": _exposure_1_spotlight,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações praticamente imunes (exposição ≤2) à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com exposição ≤2
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salario}
- Top 10 por empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "largest-occupations",
        "category": "Ocupações",
        "tags": ["maiores", "empregados", "ranking"],
        "chart_type": "ranking_table",
        "analysis_fn": _largest_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as 10 maiores ocupações do Brasil em número de trabalhadores.

DADOS (use APENAS estes números, não invente dados):
- Total nas 10 maiores: {total_top10} ({pct_total} do total)
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "highest-paid-top10",
        "category": "Ocupações",
        "tags": ["salário", "remuneração", "ranking"],
        "chart_type": "ranking_table",
        "analysis_fn": _highest_paid_top10,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as 10 ocupações mais bem pagas do Brasil e sua exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Exposição média das top 10: {avg_exposicao_top10}
- Top 10 por salário: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "gender-imbalance-top",
        "category": "Demografia",
        "tags": ["gênero", "desigualdade", "concentração"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _gender_imbalance_top,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com maior desequilíbrio de gênero no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Top 10 com maior concentração de gênero: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "salary-progression-ratio",
        "category": "Mercado",
        "tags": ["salário", "progressão", "admissão"],
        "chart_type": "ranking_table",
        "analysis_fn": _salary_progression_ratio,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com maior progressão salarial (razão entre salário mediano e salário de admissão).

DADOS (use APENAS estes números, não invente dados):
- Top 10 por progressão: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "high-growth-high-exposure",
        "category": "Ocupações",
        "tags": ["crescimento", "exposição", "paradoxo"],
        "chart_type": "ranking_table",
        "analysis_fn": _high_growth_high_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações que crescem rapidamente MAS também têm alta exposição à IA — um paradoxo.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com crescimento ≥7 E exposição ≥7
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "low-vantagem-high-workers",
        "category": "Ocupações",
        "tags": ["vantagem", "risco", "trabalhadores"],
        "chart_type": "ranking_table",
        "analysis_fn": _low_vantagem_high_workers,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações que têm pouca vantagem da IA (≤3) — aquelas que a IA mais ameaça sem beneficiar.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com vantagem ≤3
- Total de trabalhadores: {total_workers}
- Top 10 por empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "balanced-risk",
        "category": "Ocupações",
        "tags": ["exposição média", "risco moderado", "transição"],
        "chart_type": "ranking_table",
        "analysis_fn": _balanced_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações na faixa média de exposição (4-6) — a "zona cinzenta" da IA.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações na faixa média
- Total de trabalhadores: {total_workers}
- Top 10 por empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "extreme-divergence",
        "category": "Ocupações",
        "tags": ["divergência", "exposição", "vantagem"],
        "chart_type": "ranking_table",
        "analysis_fn": _extreme_divergence,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações onde a exposição à IA e a vantagem da IA divergem radicalmente (diferença ≥5 pontos).

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com divergência extrema
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "declining-well-paid",
        "category": "Mercado",
        "tags": ["declínio", "salário alto", "perda de emprego"],
        "chart_type": "ranking_table",
        "analysis_fn": _declining_well_paid,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações bem pagas (≥R$5k) que estão perdendo vagas — a "fuga de cérebros" do emprego formal.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações bem pagas em declínio
- Saldo total: {total_saldo}
- Salário médio: {avg_salario}
- Top 10 por saldo negativo: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "growing-low-paid",
        "category": "Mercado",
        "tags": ["crescimento", "baixo salário", "precarização"],
        "chart_type": "ranking_table",
        "analysis_fn": _growing_low_paid,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações de baixo salário (<R$2k) que estão crescendo — o fenômeno da precarização.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de baixo salário em crescimento
- Saldo total: {total_saldo}
- Salário médio: {avg_salario}
- Top 10 por saldo positivo: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "minimum-wage-exposure",
        "category": "Mercado",
        "tags": ["salário mínimo", "vulnerabilidade", "risco"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _minimum_wage_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a exposição à IA entre trabalhadores próximos ao salário mínimo.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com salário < R$1.800
- Total de trabalhadores: {total_workers}
- Exposição média: {avg_exposicao}
- {n_high_risk} em alto risco (exposição ≥7)
- Top 10 por exposição: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "salary-above-10k",
        "category": "Mercado",
        "tags": ["alta renda", "exposição", "elite"],
        "chart_type": "ranking_table",
        "analysis_fn": _salary_above_10k,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a exposição à IA entre as ocupações mais bem pagas (≥R$10k) do Brasil.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com salário ≥R$10k
- Total de trabalhadores: {total_workers}
- Exposição média: {avg_exposicao}
- Top 10 por salário: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "net-job-creation",
        "category": "Mercado",
        "tags": ["saldo", "CAGED", "criação de emprego"],
        "chart_type": "comparison_pair",
        "analysis_fn": _net_job_creation,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o saldo líquido de criação de empregos em todas as ocupações analisadas.

DADOS (use APENAS estes números, não invente dados):
- Saldo líquido total: {total_saldo}
- {n_positive} ocupações com saldo positivo (total: {sum_positive})
- {n_negative} ocupações com saldo negativo (total: {sum_negative})
- Top 5 criadoras: {top5_creators}
- Top 5 destruidoras: {top5_destroyers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "salary-quintile-exposure",
        "category": "Mercado",
        "tags": ["salário", "quintil", "desigualdade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_quintile_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a exposição à IA varia entre faixas salariais (quintis).

DADOS (use APENAS estes números, não invente dados):
- Quintis salariais: {quintiles}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "exposure-impact-index",
        "category": "Mercado",
        "tags": ["impacto", "exposição", "trabalhadores"],
        "chart_type": "ranking_table",
        "analysis_fn": _exposure_impact_index,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com maior índice de impacto da IA (empregados × exposição).

DADOS (use APENAS estes números, não invente dados):
- Top 10 por índice de impacto: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "median-salary-by-tier",
        "category": "Mercado",
        "tags": ["salário", "exposição", "mediana"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _median_salary_by_tier,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como o salário mediano varia conforme o nível de exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Salário mediano por faixa de exposição: {tiers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "entry-salary-vs-median",
        "category": "Mercado",
        "tags": ["admissão", "salário", "progressão"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _entry_salary_vs_median,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a relação entre salário de admissão e salário mediano nas diferentes faixas de exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Razão salário admissão / mediano por faixa: {tiers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "high-hiring-low-pay",
        "category": "Mercado",
        "tags": ["contratação", "baixo salário", "precarização"],
        "chart_type": "ranking_table",
        "analysis_fn": _high_hiring_low_pay,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações que contratam muito (>1000 admissões) mas pagam pouco (<R$1.800).

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de alta contratação e baixo salário
- Total de admissões: {total_admissoes}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "turnover-proxy",
        "category": "Mercado",
        "tags": ["rotatividade", "admissões", "empregados"],
        "chart_type": "ranking_table",
        "analysis_fn": _turnover_proxy,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com maior taxa de rotatividade (admissões/empregados) no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por rotatividade: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "automation-risk-composite",
        "category": "Mercado",
        "tags": ["automação", "risco composto", "vulnerabilidade"],
        "chart_type": "ranking_table",
        "analysis_fn": _automation_risk_composite,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com maior risco composto de automação (alta exposição + baixa vantagem + baixo crescimento).

DADOS (use APENAS estes números, não invente dados):
- Trabalhadores nas top 10: {total_workers_top10}
- Top 10 por score de risco: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "future-proof-composite",
        "category": "Mercado",
        "tags": ["futuro", "resiliência", "oportunidade"],
        "chart_type": "ranking_table",
        "analysis_fn": _future_proof_composite,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações mais "à prova de futuro" (baixa exposição + alta vantagem + alto crescimento).

DADOS (use APENAS estes números, não invente dados):
- Trabalhadores nas top 10: {total_workers_top10}
- Top 10 por score de resiliência: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "salary-variance-by-grupo",
        "category": "Mercado",
        "tags": ["salário", "variância", "grande grupo"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_variance_by_grupo,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a desigualdade salarial dentro de cada grande grupo ocupacional.

DADOS (use APENAS estes números, não invente dados):
- Desvio padrão salarial por grupo: {grupos}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "male-dominated-high-risk",
        "category": "Demografia",
        "tags": ["gênero", "masculino", "alto risco"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _male_dominated_high_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações predominantemente masculinas (>70%) com alto risco de IA.

DADOS (use APENAS estes números, não invente dados):
- {total_occupations} ocupações masculinizadas de alto risco
- Total de trabalhadores: {total_workers}
- Total de homens: {total_men}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "gender-balanced-occupations",
        "category": "Demografia",
        "tags": ["gênero", "equilíbrio", "paridade"],
        "chart_type": "ranking_table",
        "analysis_fn": _gender_balanced_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações com equilíbrio de gênero (45-55% feminino) e sua exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações com equilíbrio de gênero
- Total de trabalhadores: {total_workers}
- Top 10 por empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "race-gap-by-grupo",
        "category": "Demografia",
        "tags": ["raça", "grande grupo", "desigualdade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _race_gap_by_grupo,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença racial na exposição à IA em cada grande grupo ocupacional.

DADOS (use APENAS estes números, não invente dados):
- Gap racial por grupo: {grupos}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "women-in-opportunity",
        "category": "Demografia",
        "tags": ["mulheres", "oportunidade", "IA"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_in_opportunity,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina em ocupações de alta oportunidade com IA.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de alta oportunidade (≥7)
- Participação feminina média: {avg_pct_feminino}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "education-salary-matrix",
        "category": "Educação",
        "tags": ["escolaridade", "salário", "exposição"],
        "chart_type": "ranking_table",
        "analysis_fn": _education_salary_matrix,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a relação entre escolaridade, exposição à IA e salário.

DADOS (use APENAS estes números, não invente dados):
- Matriz escolaridade × exposição × salário: {matrix}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "high-education-low-salary",
        "category": "Educação",
        "tags": ["superior completo", "baixo salário", "desvalorização"],
        "chart_type": "ranking_table",
        "analysis_fn": _high_education_low_salary,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações que exigem ensino superior mas pagam menos de R$4k.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de alta escolaridade e baixo salário
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "low-education-high-salary",
        "category": "Educação",
        "tags": ["baixa escolaridade", "alto salário", "anomalia"],
        "chart_type": "ranking_table",
        "analysis_fn": _low_education_high_salary,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações de baixa escolaridade que pagam mais de R$5k — exceções no mercado.

DADOS (use APENAS estes números, não invente dados):
- {n_occupations} ocupações de baixa escolaridade e alto salário
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "escolaridade-distribution",
        "category": "Educação",
        "tags": ["escolaridade", "distribuição", "perfil"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _escolaridade_distribution,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a distribuição de escolaridade entre as ocupações brasileiras.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {total_occupations}
- Distribuição: {distribution}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "state-salary-ranking",
        "category": "Regional",
        "tags": ["estados", "salário", "ranking"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_salary_ranking,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o ranking de salários médios por estado brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Líder: {top_state} com {top_salary}
- Último: {bottom_state} com {bottom_salary}
- Todos os estados: {states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "state-workforce-ranking",
        "category": "Regional",
        "tags": ["estados", "trabalhadores", "ranking"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_workforce_ranking,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o ranking de estados por força de trabalho formal.

DADOS (use APENAS estes números, não invente dados):
- Total nacional: {total_national}
- Estados por trabalhadores: {states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "state-high-risk-workers",
        "category": "Regional",
        "tags": ["estados", "alto risco", "estimativa"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_high_risk_workers,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a estimativa de trabalhadores em risco de IA por estado.

DADOS (use APENAS estes números, não invente dados):
- Total estimado em risco: {total_high_risk}
- Top 10 estados: {states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "southeast-dominance",
        "category": "Regional",
        "tags": ["Sudeste", "concentração", "desigualdade"],
        "chart_type": "comparison_pair",
        "analysis_fn": _southeast_dominance,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a dominância do Sudeste (SP+RJ+MG+ES) no mercado de trabalho brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Sudeste: {se_workers} trabalhadores ({pct_se})
- Restante: {rest_workers} trabalhadores
- Salário médio Sudeste: {se_avg_salary} vs Restante: {rest_avg_salary}
- Exposição Sudeste: {se_avg_exposicao} vs Restante: {rest_avg_exposicao}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "south-prosperity",
        "category": "Regional",
        "tags": ["Sul", "prosperidade", "regional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _south_prosperity,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o mercado de trabalho do Sul do Brasil (SC+PR+RS) e a exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores no Sul: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Estados: {states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "northeast-tech-hubs",
        "category": "Regional",
        "tags": ["Nordeste", "tech hubs", "CE", "PE"],
        "chart_type": "comparison_pair",
        "analysis_fn": _northeast_tech_hubs,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre Ceará e Pernambuco como hubs tecnológicos do Nordeste.

DADOS (use APENAS estes números, não invente dados):
- CE + PE: {hubs_workers} trabalhadores
- Restante do Nordeste: {other_ne_workers}
- Salário médio hubs: {hubs_avg_salary} vs restante: {other_avg_salary}
- Exposição hubs: {hubs_avg_exposicao} vs restante: {other_avg_exposicao}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "frontier-states",
        "category": "Regional",
        "tags": ["fronteira agrícola", "Centro-Oeste", "agronegócio"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _frontier_states,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os estados da fronteira agrícola (MT+MS+GO) e o impacto da IA.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores: {total_workers}
- Participação nacional: {pct_national}
- Salário médio: {avg_salary}
- Exposição média: {avg_exposicao}
- Estados: {states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "smallest-workforce-states",
        "category": "Regional",
        "tags": ["menores estados", "periferia", "escala"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _smallest_workforce_states,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os 5 estados com menor força de trabalho formal e sua exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Total nos 5 menores: {total_workers} ({pct_national})
- Estados: {bottom5}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates():
    """Return the list of story templates."""
    from insight_templates_batch_a import get_templates_batch_a
    from insight_templates_batch_b1 import get_templates_batch_b1
    from insight_templates_batch_b2 import get_templates_batch_b2
    from insight_templates_batch_c1 import get_templates_batch_c1
    from insight_templates_batch_c2 import get_templates_batch_c2
    from insight_templates_batch_d1 import get_templates_batch_d1
    from insight_templates_batch_d2 import get_templates_batch_d2
    from insight_templates_batch_women import get_templates_batch_women
    return (
        TEMPLATES
        + get_templates_batch_a()
        + get_templates_batch_b1()
        + get_templates_batch_b2()
        + get_templates_batch_c1()
        + get_templates_batch_c2()
        + get_templates_batch_d1()
        + get_templates_batch_d2()
        + get_templates_batch_women()
    )
