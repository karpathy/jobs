"""Insight templates batch C2: workforce analyses + thematic."""
import statistics
from insight_templates import _fmt_pct, _fmt_num, _safe_avg


# ─── Template 222: AI-Resilient Workforce ────────────────────────────────────

def _ai_resilient_workforce(data, summary):
    resilient = [o for o in data if o.get("exposicao") is not None and o["exposicao"] <= 2]
    total_w = sum(o.get("empregados") or 0 for o in resilient)
    all_w = sum(o.get("empregados") or 0 for o in data if o.get("empregados"))
    pct = round(total_w / all_w * 100, 1) if all_w else 0
    sal_vals = [o["salario"] for o in resilient if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    grupos = {}
    for o in resilient:
        gg = o.get("grande_grupo", "Outros")
        grupos[gg] = grupos.get(gg, 0) + (o.get("empregados") or 0)
    top_grupos = sorted(grupos.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores resilientes a IA — {_fmt_pct(pct)} da forca de trabalho",
        "chart_data": [
            {"label": g[0][:50], "value": g[1], "formatted": _fmt_num(g[1])}
            for g in top_grupos
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "pct_workforce": _fmt_pct(pct),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "n_occupations": len(resilient),
            "top_sectors": [{"sector": g[0], "workers": _fmt_num(g[1])} for g in top_grupos],
        },
    }


# ─── Template 223: AI-Transformed Workforce ──────────────────────────────────

def _ai_transformed_workforce(data, summary):
    transformed = [o for o in data if o.get("exposicao") is not None and 5 <= o["exposicao"] <= 7]
    total_w = sum(o.get("empregados") or 0 for o in transformed)
    sal_vals = [o["salario"] for o in transformed if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    transformed.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = transformed[:10]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores sendo transformados pela IA (exposicao 5-7)",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "n_occupations": len(transformed),
            "top_occupations": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"]}
                for o in top10
            ],
        },
    }


# ─── Template 224: AI-Disrupted Workforce ────────────────────────────────────

def _ai_disrupted_workforce(data, summary):
    disrupted = [o for o in data if o.get("exposicao") is not None and o["exposicao"] >= 8]
    total_w = sum(o.get("empregados") or 0 for o in disrupted)
    sal_vals = [o["salario"] for o in disrupted if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    disrupted.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = disrupted[:10]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores em ocupacoes altamente disruptadas (exposicao >= 8)",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "n_occupations": len(disrupted),
            "top_occupations": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"]}
                for o in top10
            ],
        },
    }


# ─── Template 225: Minimum Wage At Risk ──────────────────────────────────────

def _minimum_wage_at_risk(data, summary):
    at_risk = [
        o for o in data
        if o.get("salario") is not None and o["salario"] < 1600
        and o.get("exposicao") is not None and o["exposicao"] >= 7
    ]
    total_w = sum(o.get("empregados") or 0 for o in at_risk)
    at_risk.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = at_risk[:10]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores com salario minimo e alta exposicao a IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "n_occupations": len(at_risk),
            "occupations": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "salario": "R$ " + _fmt_num(round(o["salario"])), "exposicao": o["exposicao"]}
                for o in top10
            ],
        },
    }


# ─── Template 226: Middle Management Exposure ────────────────────────────────

def _middle_management_exposure(data, summary):
    keywords = ["gerente", "supervisor", "coordenador", "chefi"]
    matches = [
        o for o in data
        if o.get("exposicao") is not None
        and any(kw in o.get("titulo", "").lower() for kw in keywords)
    ]
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposicao media da gestao intermediaria — {len(matches)} ocupacoes",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"], "formatted": str(o["exposicao"]).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "n_occupations": len(matches),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(sum(o.get("empregados") or 0 for o in matches)),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in top10
            ],
        },
    }


# ─── Template 227: Specialist Occupations ────────────────────────────────────

def _specialist_occupations(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None
        and ("especialist" in o.get("titulo", "").lower() or "técnico" in o.get("titulo", "").lower())
    ]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupacoes de especialistas e tecnicos — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(matches),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"]}
                for o in top10
            ],
        },
    }


# ─── Template 228: Regulated Professions ─────────────────────────────────────

def _regulated_professions(data, summary):
    keywords = ["médic", "engenheir", "advogad", "contad", "arquitet", "dentist", "farmac", "psicólog", "veterinári"]
    matches = [
        o for o in data
        if o.get("exposicao") is not None
        and any(kw in o.get("titulo", "").lower() for kw in keywords)
    ]
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposicao media das profissoes regulamentadas — {len(matches)} ocupacoes",
        "chart_data": [
            {"label": o["titulo"], "value": o["exposicao"], "formatted": str(o["exposicao"]).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "n_occupations": len(matches),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "total_workers": _fmt_num(total_w),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in top10
            ],
        },
    }


# ─── Template 229: Education Premium At Risk ─────────────────────────────────

def _education_premium_at_risk(data, summary):
    superior = [o for o in data if o.get("escolaridade") == "Superior Completo" and o.get("exposicao") is not None]
    high_exp = [o for o in superior if o["exposicao"] >= 7]
    low_exp = [o for o in superior if o["exposicao"] <= 3]
    sal_high = [o["salario"] for o in high_exp if o.get("salario")]
    sal_low = [o["salario"] for o in low_exp if o.get("salario")]
    avg_sal_high = round(_safe_avg(sal_high)) if sal_high else 0
    avg_sal_low = round(_safe_avg(sal_low)) if sal_low else 0
    diff_pct = round((avg_sal_high - avg_sal_low) / avg_sal_low * 100, 1) if avg_sal_low else 0
    return {
        "headline_stat": "R$ " + _fmt_num(avg_sal_high),
        "headline_label": "salario medio de graduados com alta exposicao a IA",
        "chart_data": [
            {"label": "Alta exposicao (>=7)", "value": avg_sal_high, "formatted": "R$ " + _fmt_num(avg_sal_high)},
            {"label": "Baixa exposicao (<=3)", "value": avg_sal_low, "formatted": "R$ " + _fmt_num(avg_sal_low)},
        ],
        "details": {
            "avg_salary_high_exp": "R$ " + _fmt_num(avg_sal_high),
            "avg_salary_low_exp": "R$ " + _fmt_num(avg_sal_low),
            "n_high_exp": len(high_exp),
            "n_low_exp": len(low_exp),
            "diff_pct": _fmt_pct(diff_pct),
            "total_superior": len(superior),
        },
    }


# ─── Template 230: Youth Entry Risk ──────────────────────────────────────────

def _youth_entry_risk(data, summary):
    with_admissoes = [o for o in data if o.get("admissoes") is not None and o.get("exposicao") is not None]
    with_admissoes.sort(key=lambda o: o["admissoes"], reverse=True)
    top20 = with_admissoes[:20]
    high_risk = [o for o in top20 if o["exposicao"] >= 7]
    pct_risky = round(len(high_risk) / len(top20) * 100, 1) if top20 else 0
    total_admissoes = sum(o["admissoes"] for o in top20)
    risky_admissoes = sum(o["admissoes"] for o in high_risk)
    return {
        "headline_stat": _fmt_pct(pct_risky),
        "headline_label": "das top 20 ocupacoes por admissoes tem alta exposicao a IA",
        "chart_data": [
            {"label": o["titulo"], "value": o["admissoes"], "formatted": _fmt_num(o["admissoes"]),
             "exposicao": o["exposicao"], "risk": "alto" if o["exposicao"] >= 7 else "moderado/baixo"}
            for o in top20
        ],
        "details": {
            "pct_risky": _fmt_pct(pct_risky),
            "n_risky": len(high_risk),
            "total_admissoes_top20": _fmt_num(total_admissoes),
            "risky_admissoes": _fmt_num(risky_admissoes),
            "top20": [
                {"titulo": o["titulo"], "admissoes": _fmt_num(o["admissoes"]), "exposicao": o["exposicao"]}
                for o in top20
            ],
        },
    }


# ─── Template 231: Stable Large Occupations ──────────────────────────────────

def _stable_large_occupations(data, summary):
    stable = [
        o for o in data
        if o.get("empregados") is not None and o["empregados"] >= 50000
        and o.get("saldo") is not None and abs(o["saldo"]) < 1000
    ]
    stable.sort(key=lambda o: o["empregados"], reverse=True)
    total_w = sum(o["empregados"] for o in stable)
    return {
        "headline_stat": str(len(stable)),
        "headline_label": f"grandes ocupacoes estaveis — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o["empregados"], "formatted": _fmt_num(o["empregados"])}
            for o in stable[:10]
        ],
        "details": {
            "n_stable": len(stable),
            "total_workers": _fmt_num(total_w),
            "occupations": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o["empregados"]),
                 "saldo": _fmt_num(o["saldo"]),
                 "exposicao": o.get("exposicao", "N/D")}
                for o in stable
            ],
        },
    }


# ─── Template 232: Concentration Index ───────────────────────────────────────

def _concentration_index(data, summary):
    with_emp = [o for o in data if o.get("empregados") and o["empregados"] > 0]
    with_emp.sort(key=lambda o: o["empregados"], reverse=True)
    total_all = sum(o["empregados"] for o in with_emp)
    top10 = with_emp[:10]
    top50 = with_emp[:50]
    top10_w = sum(o["empregados"] for o in top10)
    top50_w = sum(o["empregados"] for o in top50)
    pct10 = round(top10_w / total_all * 100, 1) if total_all else 0
    pct50 = round(top50_w / total_all * 100, 1) if total_all else 0
    return {
        "headline_stat": _fmt_pct(pct10),
        "headline_label": "da forca de trabalho concentrada nas 10 maiores ocupacoes",
        "chart_data": [
            {"label": o["titulo"], "value": o["empregados"], "formatted": _fmt_num(o["empregados"])}
            for o in top10
        ],
        "details": {
            "pct_top10": _fmt_pct(pct10),
            "pct_top50": _fmt_pct(pct50),
            "top10_workers": _fmt_num(top10_w),
            "top50_workers": _fmt_num(top50_w),
            "total_workers": _fmt_num(total_all),
            "n_occupations": len(with_emp),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o["empregados"])}
                for o in top10
            ],
        },
    }


# ─── Template 233: Micro Occupations ─────────────────────────────────────────

def _micro_occupations(data, summary):
    micro = [o for o in data if o.get("empregados") is not None and 1 <= o["empregados"] <= 500 and o.get("exposicao") is not None]
    large = [o for o in data if o.get("empregados") is not None and o["empregados"] >= 10000 and o.get("exposicao") is not None]
    avg_exp_micro = round(_safe_avg([o["exposicao"] for o in micro]), 1)
    avg_exp_large = round(_safe_avg([o["exposicao"] for o in large]), 1)
    total_micro = sum(o["empregados"] for o in micro)
    return {
        "headline_stat": str(len(micro)),
        "headline_label": f"micro-ocupacoes (1-500 trabalhadores) — exposicao media {str(avg_exp_micro).replace('.', ',')}",
        "chart_data": [
            {"label": "Micro (1-500)", "value": avg_exp_micro, "formatted": str(avg_exp_micro).replace(".", ",")},
            {"label": "Grandes (>=10k)", "value": avg_exp_large, "formatted": str(avg_exp_large).replace(".", ",")},
        ],
        "details": {
            "n_micro": len(micro),
            "n_large": len(large),
            "avg_exp_micro": str(avg_exp_micro).replace(".", ","),
            "avg_exp_large": str(avg_exp_large).replace(".", ","),
            "total_micro_workers": _fmt_num(total_micro),
        },
    }


# ─── Template 234: Large Occupation Profile ──────────────────────────────────

def _large_occupation_profile(data, summary):
    large = [o for o in data if o.get("empregados") is not None and o["empregados"] >= 100000]
    large.sort(key=lambda o: o["empregados"], reverse=True)
    total_w = sum(o["empregados"] for o in large)
    return {
        "headline_stat": str(len(large)),
        "headline_label": f"ocupacoes com mais de 100 mil trabalhadores — {_fmt_num(total_w)} no total",
        "chart_data": [
            {"label": o["titulo"], "value": o["empregados"], "formatted": _fmt_num(o["empregados"])}
            for o in large[:10]
        ],
        "details": {
            "n_large": len(large),
            "total_workers": _fmt_num(total_w),
            "occupations": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o["empregados"]),
                 "exposicao": o.get("exposicao", "N/D"),
                 "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in large
            ],
        },
    }


# ─── Template 235: Salary Compression Jobs ───────────────────────────────────

def _salary_compression_jobs(data, summary):
    compressed = [
        o for o in data
        if o.get("salario_admissao") and o.get("salario") and o["salario"] > 0
        and o["salario_admissao"] / o["salario"] > 0.85
    ]
    compressed.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = compressed[:10]
    return {
        "headline_stat": str(len(compressed)),
        "headline_label": "ocupacoes com pouca margem de crescimento salarial",
        "chart_data": [
            {"label": o["titulo"], "value": round(o["salario_admissao"] / o["salario"] * 100, 1),
             "formatted": _fmt_pct(round(o["salario_admissao"] / o["salario"] * 100, 1))}
            for o in top10
        ],
        "details": {
            "n_compressed": len(compressed),
            "total_workers": _fmt_num(sum(o.get("empregados") or 0 for o in compressed)),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "salario": "R$ " + _fmt_num(round(o["salario"])),
                 "salario_admissao": "R$ " + _fmt_num(round(o["salario_admissao"])),
                 "ratio": _fmt_pct(round(o["salario_admissao"] / o["salario"] * 100, 1))}
                for o in top10
            ],
        },
    }


# ─── Template 236: Salary Expansion Jobs ─────────────────────────────────────

def _salary_expansion_jobs(data, summary):
    expanded = [
        o for o in data
        if o.get("salario") and o.get("salario_admissao") and o["salario_admissao"] > 0
        and o["salario"] / o["salario_admissao"] > 2.0
    ]
    expanded.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = expanded[:10]
    return {
        "headline_stat": str(len(expanded)),
        "headline_label": "ocupacoes onde o salario mais que dobra ao longo da carreira",
        "chart_data": [
            {"label": o["titulo"], "value": round(o["salario"] / o["salario_admissao"], 1),
             "formatted": str(round(o["salario"] / o["salario_admissao"], 1)).replace(".", ",") + "x"}
            for o in top10
        ],
        "details": {
            "n_expanded": len(expanded),
            "total_workers": _fmt_num(sum(o.get("empregados") or 0 for o in expanded)),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "salario": "R$ " + _fmt_num(round(o["salario"])),
                 "salario_admissao": "R$ " + _fmt_num(round(o["salario_admissao"])),
                 "multiplier": str(round(o["salario"] / o["salario_admissao"], 1)).replace(".", ",") + "x"}
                for o in top10
            ],
        },
    }


# ─── Template 237: Masters/Doctorate Profile ─────────────────────────────────

def _masters_doctorate_profile(data, summary):
    matches = [
        o for o in data
        if o.get("escolaridade") in ("Mestrado", "Doutorado") and o.get("exposicao") is not None
    ]
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    oport_vals = [o["oportunidade"] for o in matches if o.get("oportunidade") is not None]
    avg_oport = round(_safe_avg(oport_vals), 1) if oport_vals else 0
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupacoes exigindo mestrado ou doutorado — exposicao media {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(matches),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_oportunidade": str(avg_oport).replace(".", ","),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "escolaridade": o.get("escolaridade", "N/D")}
                for o in top10
            ],
        },
    }


# ─── Template 238: Medio Completo Risk ───────────────────────────────────────

def _medio_completo_risk(data, summary):
    matches = [
        o for o in data
        if o.get("escolaridade") == "Médio Completo"
        and o.get("exposicao") is not None and o["exposicao"] >= 7
    ]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores com ensino medio em alto risco de IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "n_occupations": len(matches),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"]}
                for o in top10
            ],
        },
    }


# ─── Template 239: Fundamental Workers ───────────────────────────────────────

def _fundamental_workers(data, summary):
    keywords = ["5ª", "6ª", "Fundamental", "Analfabeto"]
    matches = [
        o for o in data
        if o.get("escolaridade") and any(kw in o["escolaridade"] for kw in keywords)
        and o.get("exposicao") is not None
    ]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores com baixa escolaridade — exposicao media {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "n_occupations": len(matches),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "escolaridade": o.get("escolaridade", "N/D")}
                for o in top10
            ],
        },
    }


# ─── Template 240: Digital Literacy Demand ───────────────────────────────────

def _digital_literacy_demand(data, summary):
    high_exp = [o for o in data if o.get("exposicao") is not None and o["exposicao"] >= 6]
    total_w = sum(o.get("empregados") or 0 for o in high_exp)
    grupos = {}
    for o in high_exp:
        gg = o.get("grande_grupo", "Outros")
        grupos[gg] = grupos.get(gg, 0) + (o.get("empregados") or 0)
    sorted_grupos = sorted(grupos.items(), key=lambda x: x[1], reverse=True)
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores que precisam de competencias digitais (exposicao >= 6)",
        "chart_data": [
            {"label": g[0][:50], "value": g[1], "formatted": _fmt_num(g[1])}
            for g in sorted_grupos[:8]
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "n_occupations": len(high_exp),
            "by_grande_grupo": [
                {"grupo": g[0], "workers": _fmt_num(g[1])}
                for g in sorted_grupos
            ],
        },
    }


# ─── Template 241: AI Copilot Potential ──────────────────────────────────────

def _ai_copilot_potential(data, summary):
    matches = [
        o for o in data
        if o.get("vantagem") is not None and o["vantagem"] >= 8
        and o.get("exposicao") is not None and 4 <= o["exposicao"] <= 7
    ]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupacoes com alto potencial de IA como copiloto — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(matches),
            "total_workers": _fmt_num(total_w),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "vantagem": o["vantagem"]}
                for o in top10
            ],
        },
    }


# ─── Template 242: Full Automation Candidates ────────────────────────────────

def _full_automation_candidates(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o["exposicao"] >= 9
        and o.get("vantagem") is not None and o["vantagem"] <= 4
    ]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupacoes candidatas a automacao total — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "n_occupations": len(matches),
            "total_workers": _fmt_num(total_w),
            "occupations": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "vantagem": o["vantagem"]}
                for o in matches
            ],
        },
    }


# ─── Template 243: Human-AI Collaboration ────────────────────────────────────

def _human_ai_collaboration(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and 6 <= o["exposicao"] <= 8
        and o.get("vantagem") is not None and 6 <= o["vantagem"] <= 8
    ]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupacoes no sweet spot humano-IA — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(matches),
            "total_workers": _fmt_num(total_w),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "vantagem": o["vantagem"]}
                for o in top10
            ],
        },
    }


# ─── Template 244: Untouched By AI ───────────────────────────────────────────

def _untouched_by_ai(data, summary):
    matches = [o for o in data if o.get("exposicao") is not None and o["exposicao"] <= 1]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    grupos = {}
    for o in matches:
        gg = o.get("grande_grupo", "Outros")
        grupos[gg] = grupos.get(gg, 0) + 1
    top_grupos = sorted(grupos.items(), key=lambda x: x[1], reverse=True)[:5]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupacoes praticamente intocadas pela IA — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(matches),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_sectors": [{"sector": g[0], "count": g[1]} for g in top_grupos],
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
        },
    }


# ─── Template 245: Creative Destruction ──────────────────────────────────────

def _creative_destruction(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o["exposicao"] >= 7
        and o.get("crescimento") is not None and o["crescimento"] >= 7
    ]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupacoes em destruicao criativa — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "n_occupations": len(matches),
            "total_workers": _fmt_num(total_w),
            "top10": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "crescimento": o["crescimento"]}
                for o in top10
            ],
        },
    }


# ─── Template 246: Structural Unemployment Risk ──────────────────────────────

def _structural_unemployment_risk(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o["exposicao"] >= 7
        and o.get("crescimento") is not None and o["crescimento"] <= 3
        and o.get("saldo") is not None and o["saldo"] < 0
    ]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupacoes com risco de desemprego estrutural — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "n_occupations": len(matches),
            "total_workers": _fmt_num(total_w),
            "occupations": [
                {"titulo": o["titulo"], "empregados": _fmt_num(o.get("empregados") or 0),
                 "exposicao": o["exposicao"], "crescimento": o["crescimento"],
                 "saldo": _fmt_num(o["saldo"])}
                for o in matches
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template definitions
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES_BATCH_C2 = [
    # 222
    {
        "id": "ai-resilient-workforce",
        "category": "Mercado",
        "tags": ["resiliencia", "baixa exposicao", "workforce"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _ai_resilient_workforce,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a forca de trabalho resiliente a IA no Brasil — ocupacoes com exposicao <= 2.

DADOS (use APENAS estes numeros, nao invente dados):
- Total de trabalhadores resilientes: {total_workers} ({pct_workforce} da forca de trabalho)
- Salario medio: {avg_salary}
- Numero de ocupacoes: {n_occupations}
- Principais setores: {top_sectors}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 223
    {
        "id": "ai-transformed-workforce",
        "category": "Mercado",
        "tags": ["transformacao", "exposicao media", "workforce"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _ai_transformed_workforce,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre trabalhadores sendo transformados (nao substituidos) pela IA — exposicao 5-7.

DADOS (use APENAS estes numeros, nao invente dados):
- Total de trabalhadores: {total_workers}
- Salario medio: {avg_salary}
- Numero de ocupacoes: {n_occupations}
- Top ocupacoes: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 224
    {
        "id": "ai-disrupted-workforce",
        "category": "Mercado",
        "tags": ["disrupcao", "alta exposicao", "workforce"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _ai_disrupted_workforce,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a forca de trabalho altamente disruptada pela IA — exposicao >= 8.

DADOS (use APENAS estes numeros, nao invente dados):
- Total de trabalhadores: {total_workers}
- Salario medio: {avg_salary}
- Numero de ocupacoes: {n_occupations}
- Top ocupacoes: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 225
    {
        "id": "minimum-wage-at-risk",
        "category": "Mercado",
        "tags": ["salario minimo", "vulnerabilidade", "desigualdade"],
        "chart_type": "ranking_table",
        "analysis_fn": _minimum_wage_at_risk,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os trabalhadores mais vulneraveis: salario abaixo de R$ 1.600 e alta exposicao a IA (>= 7). Os mais pobres e mais expostos.

DADOS (use APENAS estes numeros, nao invente dados):
- Total de trabalhadores: {total_workers}
- Numero de ocupacoes: {n_occupations}
- Ocupacoes: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 226
    {
        "id": "middle-management-exposure",
        "category": "Setores",
        "tags": ["gestao", "gerencia", "supervisao"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _middle_management_exposure,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a exposicao da gestao intermediaria (gerentes, supervisores, coordenadores, chefias) a IA.

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Exposicao media: {avg_exposicao}
- Salario medio: {avg_salary}
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 227
    {
        "id": "specialist-occupations",
        "category": "Ocupacoes",
        "tags": ["especialistas", "tecnicos", "qualificacao"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _specialist_occupations,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre especialistas e tecnicos diante da IA.

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Total de trabalhadores: {total_workers}
- Exposicao media: {avg_exposicao}
- Salario medio: {avg_salary}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 228
    {
        "id": "regulated-professions",
        "category": "Setores",
        "tags": ["regulamentacao", "profissoes liberais", "protecao"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _regulated_professions,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre profissoes regulamentadas (medicos, engenheiros, advogados, contadores, etc.) e sua protecao regulatoria diante da IA.

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Exposicao media: {avg_exposicao}
- Salario medio: {avg_salary}
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 229
    {
        "id": "education-premium-at-risk",
        "category": "Educacao",
        "tags": ["educacao superior", "premio salarial", "risco"],
        "chart_type": "comparison_pair",
        "analysis_fn": _education_premium_at_risk,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o premio salarial da educacao superior diante da IA. O diploma ainda protege?

DADOS (use APENAS estes numeros, nao invente dados):
- Salario medio graduados com alta exposicao (>=7): {avg_salary_high_exp}
- Salario medio graduados com baixa exposicao (<=3): {avg_salary_low_exp}
- Ocupacoes alta exposicao: {n_high_exp}
- Ocupacoes baixa exposicao: {n_low_exp}
- Diferenca: {diff_pct}
- Total ocupacoes com superior completo: {total_superior}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 230
    {
        "id": "youth-entry-risk",
        "category": "Mercado",
        "tags": ["jovens", "admissoes", "entrada", "risco"],
        "chart_type": "ranking_table",
        "analysis_fn": _youth_entry_risk,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os jovens entrando no mercado de trabalho: as ocupacoes que mais contratam sao seguras?

DADOS (use APENAS estes numeros, nao invente dados):
- Percentual das top 20 ocupacoes por admissoes com alta exposicao: {pct_risky}
- Ocupacoes de risco entre top 20: {n_risky}
- Total de admissoes top 20: {total_admissoes_top20}
- Admissoes em ocupacoes de risco: {risky_admissoes}
- Top 20: {top20}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 231
    {
        "id": "stable-large-occupations",
        "category": "Ocupacoes",
        "tags": ["estabilidade", "grandes ocupacoes", "saldo"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _stable_large_occupations,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre grandes ocupacoes estaveis: mais de 50 mil trabalhadores e saldo proximo de zero.

DADOS (use APENAS estes numeros, nao invente dados):
- Ocupacoes estaveis: {n_stable}
- Total de trabalhadores: {total_workers}
- Lista: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 232
    {
        "id": "concentration-index",
        "category": "Mercado",
        "tags": ["concentracao", "desigualdade", "estrutura"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _concentration_index,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a concentracao do mercado de trabalho: quao poucas ocupacoes dominam?

DADOS (use APENAS estes numeros, nao invente dados):
- Top 10 ocupacoes: {pct_top10} da forca de trabalho ({top10_workers} trabalhadores)
- Top 50 ocupacoes: {pct_top50} ({top50_workers})
- Total: {total_workers} em {n_occupations} ocupacoes
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 233
    {
        "id": "micro-occupations",
        "category": "Ocupacoes",
        "tags": ["micro ocupacoes", "nicho", "comparacao"],
        "chart_type": "comparison_pair",
        "analysis_fn": _micro_occupations,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre micro-ocupacoes (1-500 trabalhadores): sao mais ou menos expostas a IA que as grandes?

DADOS (use APENAS estes numeros, nao invente dados):
- Micro-ocupacoes: {n_micro} (exposicao media: {avg_exp_micro})
- Grandes ocupacoes (>=10k): {n_large} (exposicao media: {avg_exp_large})
- Total trabalhadores em micro-ocupacoes: {total_micro_workers}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 234
    {
        "id": "large-occupation-profile",
        "category": "Ocupacoes",
        "tags": ["grandes ocupacoes", "perfil", "economia"],
        "chart_type": "ranking_table",
        "analysis_fn": _large_occupation_profile,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupacoes que definem a economia brasileira: mais de 100 mil trabalhadores cada.

DADOS (use APENAS estes numeros, nao invente dados):
- Ocupacoes com 100k+: {n_large}
- Total de trabalhadores: {total_workers}
- Lista: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 235
    {
        "id": "salary-compression-jobs",
        "category": "Mercado",
        "tags": ["salario", "compressao", "crescimento"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_compression_jobs,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupacoes com pouca margem de crescimento salarial: salario de admissao > 85% do salario medio.

DADOS (use APENAS estes numeros, nao invente dados):
- Ocupacoes com compressao salarial: {n_compressed}
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 236
    {
        "id": "salary-expansion-jobs",
        "category": "Mercado",
        "tags": ["salario", "crescimento", "carreira"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_expansion_jobs,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupacoes com maior crescimento salarial ao longo da carreira: salario medio > 2x o salario de admissao.

DADOS (use APENAS estes numeros, nao invente dados):
- Ocupacoes com expansao salarial: {n_expanded}
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 237
    {
        "id": "masters-doctorate-profile",
        "category": "Educacao",
        "tags": ["mestrado", "doutorado", "pos-graduacao"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _masters_doctorate_profile,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupacoes que exigem mestrado ou doutorado e seu perfil diante da IA.

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Salario medio: {avg_salary}
- Exposicao media: {avg_exposicao}
- Oportunidade media: {avg_oportunidade}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 238
    {
        "id": "medio-completo-risk",
        "category": "Educacao",
        "tags": ["ensino medio", "risco", "vulnerabilidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _medio_completo_risk,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre trabalhadores com ensino medio completo em alto risco de IA. A escolaridade mais comum e a mais vulneravel?

DADOS (use APENAS estes numeros, nao invente dados):
- Total de trabalhadores: {total_workers}
- Numero de ocupacoes: {n_occupations}
- Salario medio: {avg_salary}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 239
    {
        "id": "fundamental-workers",
        "category": "Educacao",
        "tags": ["baixa escolaridade", "fundamental", "analfabeto"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _fundamental_workers,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre trabalhadores de baixa escolaridade (fundamental ou menos) e sua relacao com a IA.

DADOS (use APENAS estes numeros, nao invente dados):
- Total de trabalhadores: {total_workers}
- Numero de ocupacoes: {n_occupations}
- Exposicao media: {avg_exposicao}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 240
    {
        "id": "digital-literacy-demand",
        "category": "Mercado",
        "tags": ["letramento digital", "competencias", "demanda"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _digital_literacy_demand,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a demanda por competencias digitais: quem precisa se adaptar? Trabalhadores com exposicao >= 6.

DADOS (use APENAS estes numeros, nao invente dados):
- Total de trabalhadores: {total_workers}
- Numero de ocupacoes: {n_occupations}
- Por grande grupo: {by_grande_grupo}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 241
    {
        "id": "ai-copilot-potential",
        "category": "Ocupacoes",
        "tags": ["copiloto", "vantagem", "colaboracao"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _ai_copilot_potential,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupacoes onde a IA funciona como copiloto: alta vantagem (>=8) e exposicao moderada (4-7).

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 242
    {
        "id": "full-automation-candidates",
        "category": "Ocupacoes",
        "tags": ["automacao total", "substituicao", "risco extremo"],
        "chart_type": "ranking_table",
        "analysis_fn": _full_automation_candidates,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupacoes mais proximas da automacao total: exposicao >= 9 e baixa vantagem humana (<= 4).

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Total de trabalhadores: {total_workers}
- Lista: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 243
    {
        "id": "human-ai-collaboration",
        "category": "Ocupacoes",
        "tags": ["colaboracao", "sweet spot", "humano-ia"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _human_ai_collaboration,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o sweet spot da colaboracao humano-IA: exposicao 6-8 e vantagem 6-8.

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 244
    {
        "id": "untouched-by-ai",
        "category": "Ocupacoes",
        "tags": ["intocadas", "baixa exposicao", "perfil"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _untouched_by_ai,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupacoes praticamente intocadas pela IA (exposicao <= 1). O que elas tem em comum?

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Total de trabalhadores: {total_workers}
- Salario medio: {avg_salary}
- Setores predominantes: {top_sectors}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 245
    {
        "id": "creative-destruction",
        "category": "Mercado",
        "tags": ["destruicao criativa", "transformacao", "crescimento"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _creative_destruction,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre destruicao criativa: ocupacoes com alta exposicao a IA (>=7) MAS tambem alto crescimento (>=7). Empregos antigos morrem, novos emergem.

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 246
    {
        "id": "structural-unemployment-risk",
        "category": "Mercado",
        "tags": ["desemprego estrutural", "risco", "declinio"],
        "chart_type": "ranking_table",
        "analysis_fn": _structural_unemployment_risk,
        "prompt_template": """Voce e um jornalista de dados escrevendo para uma publicacao como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre candidatos a desemprego estrutural: alta exposicao a IA (>=7), baixo crescimento (<=3) e saldo negativo. A tempestade perfeita.

DADOS (use APENAS estes numeros, nao invente dados):
- Numero de ocupacoes: {n_occupations}
- Total de trabalhadores: {total_workers}
- Lista: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "titulo impactante (max 10 palavras)", "subtitle": "subtitulo explicativo (max 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates_batch_c2():
    """Return the list of batch C2 story templates."""
    return TEMPLATES_BATCH_C2
