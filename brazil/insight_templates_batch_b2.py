"""Insight templates batch B2: market deep cuts."""
import statistics
from insight_templates import _fmt_pct, _fmt_num, _safe_avg


# ═══════════════════════════════════════════════════════════════════════════════
# Template 172: Gender in Creative Occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_in_creative(data, summary):
    keywords = ["artist", "design", "músic", "fotógraf", "publicit"]
    matches = [
        o for o in data
        if any(kw in o.get("titulo", "").lower() for kw in keywords)
        and o.get("demographics")
    ]
    total_fem = sum(o["demographics"].get("total_feminino", 0) for o in matches)
    total_masc = sum(o["demographics"].get("total_masculino", 0) for o in matches)
    total = total_fem + total_masc
    pct_fem = round(total_fem / total * 100, 1) if total else 0
    pct_masc = round(total_masc / total * 100, 1) if total else 0
    total_workers = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    return {
        "headline_stat": _fmt_pct(pct_fem),
        "headline_label": "de mulheres nas ocupações criativas",
        "chart_data": [
            {"label": "Mulheres", "value": pct_fem, "formatted": _fmt_pct(pct_fem)},
            {"label": "Homens", "value": pct_masc, "formatted": _fmt_pct(pct_masc)},
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_workers),
            "total_feminino": _fmt_num(total_fem),
            "total_masculino": _fmt_num(total_masc),
            "pct_feminino": _fmt_pct(pct_fem),
            "pct_masculino": _fmt_pct(pct_masc),
            "avg_exposicao": str(avg_exp).replace(".", ","),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Templates 173-177: Salary Bands
# ═══════════════════════════════════════════════════════════════════════════════

def _salary_band(data, summary, lo, hi, band_label):
    if hi is None:
        matches = [o for o in data if o.get("salario") is not None and o["salario"] >= lo]
    else:
        matches = [o for o in data if o.get("salario") is not None and lo <= o["salario"] < hi]
    count = len(matches)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top5 = matches[:5]
    return {
        "headline_stat": str(count),
        "headline_label": f"ocupações na faixa {band_label}",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top5
        ],
        "details": {
            "count": str(count),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "band_label": band_label,
            "top5": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "salario": _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in top5
            ],
        },
    }


def _salary_band_under_1500(data, summary):
    return _salary_band(data, summary, 0, 1500, "até R$ 1.500")


def _salary_band_1500_2500(data, summary):
    return _salary_band(data, summary, 1500, 2500, "R$ 1.500–2.500")


def _salary_band_2500_5000(data, summary):
    return _salary_band(data, summary, 2500, 5000, "R$ 2.500–5.000")


def _salary_band_5000_10000(data, summary):
    return _salary_band(data, summary, 5000, 10000, "R$ 5.000–10.000")


def _salary_band_above_10000(data, summary):
    return _salary_band(data, summary, 10000, None, "acima de R$ 10.000")


# ═══════════════════════════════════════════════════════════════════════════════
# Template 178: Growing + Safe Occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _growing_safe_occupations(data, summary):
    matches = [
        o for o in data
        if o.get("saldo") is not None and o["saldo"] > 0
        and o.get("exposicao") is not None and o["exposicao"] <= 3
    ]
    count = len(matches)
    total_saldo = sum(o["saldo"] for o in matches)
    matches.sort(key=lambda o: o["saldo"], reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(count),
        "headline_label": "ocupações crescendo com baixo risco de IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["saldo"], "formatted": _fmt_num(o["saldo"])}
            for o in top10
        ],
        "details": {
            "count": str(count),
            "total_saldo": _fmt_num(total_saldo),
            "top10": [
                {"titulo": o.get("titulo", ""), "saldo": _fmt_num(o["saldo"]), "exposicao": str(o["exposicao"]).replace(".", ",")}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 179: Declining + Safe Occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _declining_safe_occupations(data, summary):
    matches = [
        o for o in data
        if o.get("saldo") is not None and o["saldo"] < 0
        and o.get("exposicao") is not None and o["exposicao"] <= 3
    ]
    count = len(matches)
    total_saldo = sum(o["saldo"] for o in matches)
    matches.sort(key=lambda o: o["saldo"])
    top10 = matches[:10]
    return {
        "headline_stat": str(count),
        "headline_label": "ocupações em declínio apesar do baixo risco de IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": abs(o["saldo"]), "formatted": _fmt_num(o["saldo"])}
            for o in top10
        ],
        "details": {
            "count": str(count),
            "total_saldo": _fmt_num(total_saldo),
            "top10": [
                {"titulo": o.get("titulo", ""), "saldo": _fmt_num(o["saldo"]), "exposicao": str(o["exposicao"]).replace(".", ",")}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 180: Stagnant Occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _stagnant_occupations(data, summary):
    matches = [
        o for o in data
        if o.get("saldo") is not None and abs(o["saldo"]) <= 100
        and o.get("empregados") is not None and o["empregados"] >= 1000
    ]
    count = len(matches)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(count),
        "headline_label": "ocupações com mercado estagnado",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(count),
            "total_workers": _fmt_num(total_w),
            "top10": [
                {"titulo": o.get("titulo", ""), "empregados": _fmt_num(o.get("empregados") or 0), "saldo": _fmt_num(o.get("saldo", 0))}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 181: Admissões Leaders
# ═══════════════════════════════════════════════════════════════════════════════

def _admissoes_leaders(data, summary):
    valid = [o for o in data if o.get("admissoes") is not None and o["admissoes"] > 0]
    valid.sort(key=lambda o: o["admissoes"], reverse=True)
    top10 = valid[:10]
    return {
        "headline_stat": _fmt_num(top10[0]["admissoes"]) if top10 else "0",
        "headline_label": f"admissões — {top10[0].get('titulo', '')}" if top10 else "admissões",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["admissoes"], "formatted": _fmt_num(o["admissoes"])}
            for o in top10
        ],
        "details": {
            "top10": [
                {
                    "titulo": o.get("titulo", ""),
                    "admissoes": _fmt_num(o["admissoes"]),
                    "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D",
                    "exposicao": str(o.get("exposicao", "N/D")).replace(".", ","),
                }
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 182: Admissões per Worker (Turnover proxy)
# ═══════════════════════════════════════════════════════════════════════════════

def _admissoes_per_worker_ratio(data, summary):
    valid = [
        o for o in data
        if o.get("admissoes") is not None and o.get("empregados") is not None
        and o["empregados"] >= 1000
    ]
    for o in valid:
        o["_ratio"] = round(o["admissoes"] / o["empregados"], 2) if o["empregados"] else 0
    valid.sort(key=lambda o: o["_ratio"], reverse=True)
    top10 = valid[:10]
    top_ratio = top10[0]["_ratio"] if top10 else 0
    return {
        "headline_stat": str(top_ratio).replace(".", ","),
        "headline_label": f"admissões por trabalhador — {top10[0].get('titulo', '')}" if top10 else "admissões por trabalhador",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["_ratio"], "formatted": str(o["_ratio"]).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "top10": [
                {
                    "titulo": o.get("titulo", ""),
                    "ratio": str(o["_ratio"]).replace(".", ","),
                    "admissoes": _fmt_num(o["admissoes"]),
                    "empregados": _fmt_num(o["empregados"]),
                }
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 183: Salary vs Admission Salary Gap
# ═══════════════════════════════════════════════════════════════════════════════

def _salary_admissao_gap_largest(data, summary):
    valid = [
        o for o in data
        if o.get("salario") is not None and o.get("salario_admissao") is not None
    ]
    for o in valid:
        o["_gap"] = round(o["salario"] - o["salario_admissao"], 2)
    valid.sort(key=lambda o: o["_gap"], reverse=True)
    top10 = valid[:10]
    return {
        "headline_stat": "R$ " + _fmt_num(round(top10[0]["_gap"])) if top10 else "R$ 0",
        "headline_label": f"maior diferença salarial — {top10[0].get('titulo', '')}" if top10 else "maior diferença salarial",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["_gap"], "formatted": "R$ " + _fmt_num(round(o["_gap"]))}
            for o in top10
        ],
        "details": {
            "top10": [
                {
                    "titulo": o.get("titulo", ""),
                    "gap": "R$ " + _fmt_num(round(o["_gap"])),
                    "salario": "R$ " + _fmt_num(round(o["salario"])),
                    "salario_admissao": "R$ " + _fmt_num(round(o["salario_admissao"])),
                }
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 184: High Opportunity, Low Salary
# ═══════════════════════════════════════════════════════════════════════════════

def _high_opportunity_low_salary(data, summary):
    matches = [
        o for o in data
        if o.get("oportunidade") is not None and o["oportunidade"] >= 7
        and o.get("salario") is not None and o["salario"] < 2000
    ]
    count = len(matches)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(count),
        "headline_label": "ocupações com alta oportunidade e baixo salário",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(count),
            "total_workers": _fmt_num(total_w),
            "list": [
                {
                    "titulo": o.get("titulo", ""),
                    "oportunidade": str(o["oportunidade"]).replace(".", ","),
                    "salario": "R$ " + _fmt_num(round(o["salario"])),
                    "empregados": _fmt_num(o.get("empregados") or 0),
                }
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 185: Triple High
# ═══════════════════════════════════════════════════════════════════════════════

def _triple_high(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o["exposicao"] >= 7
        and o.get("vantagem") is not None and o["vantagem"] >= 7
        and o.get("crescimento") is not None and o["crescimento"] >= 7
    ]
    count = len(matches)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if matches else 0
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(count),
        "headline_label": "ocupações com triplo alto (exposição, vantagem e crescimento ≥7)",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(count),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top10": [
                {
                    "titulo": o.get("titulo", ""),
                    "empregados": _fmt_num(o.get("empregados") or 0),
                    "exposicao": str(o["exposicao"]).replace(".", ","),
                    "vantagem": str(o["vantagem"]).replace(".", ","),
                    "crescimento": str(o["crescimento"]).replace(".", ","),
                }
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 186: Triple Low
# ═══════════════════════════════════════════════════════════════════════════════

def _triple_low(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o["exposicao"] <= 3
        and o.get("vantagem") is not None and o["vantagem"] <= 3
        and o.get("crescimento") is not None and o["crescimento"] <= 3
    ]
    count = len(matches)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(count),
        "headline_label": "ocupações irrelevantes para IA (triplo baixo ≤3)",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(count),
            "total_workers": _fmt_num(total_w),
            "top10": [
                {"titulo": o.get("titulo", ""), "empregados": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 187: Crescimento vs Saldo
# ═══════════════════════════════════════════════════════════════════════════════

def _crescimento_vs_saldo(data, summary):
    high_cresc = [o for o in data if o.get("crescimento") is not None and o["crescimento"] >= 7 and o.get("saldo") is not None]
    low_cresc = [o for o in data if o.get("crescimento") is not None and o["crescimento"] <= 3 and o.get("saldo") is not None]
    avg_saldo_high = round(_safe_avg([o["saldo"] for o in high_cresc])) if high_cresc else 0
    avg_saldo_low = round(_safe_avg([o["saldo"] for o in low_cresc])) if low_cresc else 0
    return {
        "headline_stat": _fmt_num(avg_saldo_high),
        "headline_label": "saldo médio em ocupações com crescimento alto (≥7)",
        "chart_data": [
            {"label": "Crescimento alto (≥7)", "value": avg_saldo_high, "formatted": _fmt_num(avg_saldo_high)},
            {"label": "Crescimento baixo (≤3)", "value": avg_saldo_low, "formatted": _fmt_num(avg_saldo_low)},
        ],
        "details": {
            "count_high": str(len(high_cresc)),
            "count_low": str(len(low_cresc)),
            "avg_saldo_high": _fmt_num(avg_saldo_high),
            "avg_saldo_low": _fmt_num(avg_saldo_low),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 188: Vantagem vs Salary Correlation
# ═══════════════════════════════════════════════════════════════════════════════

def _vantagem_vs_salary_correlation(data, summary):
    high_van = [o for o in data if o.get("vantagem") is not None and o["vantagem"] >= 7 and o.get("salario") is not None]
    low_van = [o for o in data if o.get("vantagem") is not None and o["vantagem"] <= 3 and o.get("salario") is not None]
    avg_sal_high = round(_safe_avg([o["salario"] for o in high_van])) if high_van else 0
    avg_sal_low = round(_safe_avg([o["salario"] for o in low_van])) if low_van else 0
    return {
        "headline_stat": "R$ " + _fmt_num(avg_sal_high),
        "headline_label": "salário médio em ocupações com alta vantagem (≥7)",
        "chart_data": [
            {"label": "Vantagem alta (≥7)", "value": avg_sal_high, "formatted": "R$ " + _fmt_num(avg_sal_high)},
            {"label": "Vantagem baixa (≤3)", "value": avg_sal_low, "formatted": "R$ " + _fmt_num(avg_sal_low)},
        ],
        "details": {
            "count_high": str(len(high_van)),
            "count_low": str(len(low_van)),
            "avg_salary_high": "R$ " + _fmt_num(avg_sal_high),
            "avg_salary_low": "R$ " + _fmt_num(avg_sal_low),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 189: Opportunity by Education
# ═══════════════════════════════════════════════════════════════════════════════

def _opportunity_by_education(data, summary):
    edu_groups = {}
    for o in data:
        esc = o.get("escolaridade")
        if not esc or o.get("oportunidade") is None:
            continue
        edu_groups.setdefault(esc, []).append(o["oportunidade"])
    results = []
    for esc, vals in edu_groups.items():
        avg_op = round(_safe_avg(vals), 1)
        results.append({"escolaridade": esc, "avg_oportunidade": avg_op, "count": len(vals)})
    results.sort(key=lambda r: r["avg_oportunidade"], reverse=True)
    return {
        "headline_stat": str(results[0]["avg_oportunidade"]).replace(".", ",") if results else "0",
        "headline_label": f"oportunidade média — {results[0]['escolaridade']}" if results else "oportunidade média",
        "chart_data": [
            {"label": r["escolaridade"], "value": r["avg_oportunidade"], "formatted": str(r["avg_oportunidade"]).replace(".", ",")}
            for r in results
        ],
        "details": {
            "by_education": [
                {"escolaridade": r["escolaridade"], "avg_oportunidade": str(r["avg_oportunidade"]).replace(".", ","), "count": str(r["count"])}
                for r in results
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Templates 190-192: Score Histograms
# ═══════════════════════════════════════════════════════════════════════════════

def _score_histogram(data, summary, field, field_label):
    buckets = {i: 0 for i in range(11)}
    for o in data:
        val = o.get(field)
        if val is not None and 0 <= val <= 10:
            buckets[int(val)] += 1
    total = sum(buckets.values())
    peak_score = max(buckets, key=buckets.get) if total else 0
    peak_count = buckets[peak_score]
    return {
        "headline_stat": str(peak_score),
        "headline_label": f"score mais frequente de {field_label} ({_fmt_num(peak_count)} ocupações)",
        "chart_data": [
            {"label": f"Score {i}", "value": buckets[i], "formatted": str(buckets[i])}
            for i in range(11)
        ],
        "details": {
            "histogram": [
                {"score": str(i), "count": str(buckets[i])}
                for i in range(11)
            ],
            "total": str(total),
            "peak_score": str(peak_score),
            "peak_count": str(peak_count),
        },
    }


def _exposure_histogram(data, summary):
    return _score_histogram(data, summary, "exposicao", "exposição")


def _vantagem_histogram(data, summary):
    return _score_histogram(data, summary, "vantagem", "vantagem")


def _crescimento_histogram(data, summary):
    return _score_histogram(data, summary, "crescimento", "crescimento")


# ═══════════════════════════════════════════════════════════════════════════════
# Template 193: Oportunidade Ranges
# ═══════════════════════════════════════════════════════════════════════════════

def _oportunidade_ranges(data, summary):
    ranges = [
        ("0–2", 0, 2),
        ("2–4", 2, 4),
        ("4–6", 4, 6),
        ("6–8", 6, 8),
        ("8–10", 8, 10),
    ]
    buckets = []
    for label, lo, hi in ranges:
        if hi == 10:
            count = len([o for o in data if o.get("oportunidade") is not None and lo <= o["oportunidade"] <= hi])
        else:
            count = len([o for o in data if o.get("oportunidade") is not None and lo <= o["oportunidade"] < hi])
        buckets.append({"label": label, "count": count})
    total = sum(b["count"] for b in buckets)
    peak = max(buckets, key=lambda b: b["count"]) if total else buckets[0]
    return {
        "headline_stat": peak["label"],
        "headline_label": f"faixa de oportunidade mais comum ({_fmt_num(peak['count'])} ocupações)",
        "chart_data": [
            {"label": b["label"], "value": b["count"], "formatted": str(b["count"])}
            for b in buckets
        ],
        "details": {
            "ranges": [
                {"range": b["label"], "count": str(b["count"])}
                for b in buckets
            ],
            "total": str(total),
            "peak_range": peak["label"],
            "peak_count": str(peak["count"]),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 194: Score Averages Overview
# ═══════════════════════════════════════════════════════════════════════════════

def _score_averages_overview(data, summary):
    avg_exp = round(_safe_avg([o["exposicao"] for o in data if o.get("exposicao") is not None]), 1)
    avg_van = round(_safe_avg([o["vantagem"] for o in data if o.get("vantagem") is not None]), 1)
    avg_cre = round(_safe_avg([o["crescimento"] for o in data if o.get("crescimento") is not None]), 1)
    avg_opo = round(_safe_avg([o["oportunidade"] for o in data if o.get("oportunidade") is not None]), 1)
    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": "exposição média nacional à IA",
        "chart_data": [
            {"label": "Exposição", "value": avg_exp, "formatted": str(avg_exp).replace(".", ",")},
            {"label": "Vantagem", "value": avg_van, "formatted": str(avg_van).replace(".", ",")},
            {"label": "Crescimento", "value": avg_cre, "formatted": str(avg_cre).replace(".", ",")},
            {"label": "Oportunidade", "value": avg_opo, "formatted": str(avg_opo).replace(".", ",")},
        ],
        "details": {
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_vantagem": str(avg_van).replace(".", ","),
            "avg_crescimento": str(avg_cre).replace(".", ","),
            "avg_oportunidade": str(avg_opo).replace(".", ","),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 195: Highest Composite Score
# ═══════════════════════════════════════════════════════════════════════════════

def _highest_composite_score(data, summary):
    valid = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None
        and o.get("crescimento") is not None and o.get("oportunidade") is not None
    ]
    for o in valid:
        o["_composite"] = round(o["exposicao"] + o["vantagem"] + o["crescimento"] + o["oportunidade"], 1)
    valid.sort(key=lambda o: o["_composite"], reverse=True)
    top10 = valid[:10]
    return {
        "headline_stat": str(top10[0]["_composite"]).replace(".", ",") if top10 else "0",
        "headline_label": f"score composto máximo — {top10[0].get('titulo', '')}" if top10 else "score composto máximo",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["_composite"], "formatted": str(o["_composite"]).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "top10": [
                {
                    "titulo": o.get("titulo", ""),
                    "composite": str(o["_composite"]).replace(".", ","),
                    "exposicao": str(o["exposicao"]).replace(".", ","),
                    "vantagem": str(o["vantagem"]).replace(".", ","),
                    "crescimento": str(o["crescimento"]).replace(".", ","),
                    "oportunidade": str(o["oportunidade"]).replace(".", ","),
                }
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 196: Lowest Composite Score
# ═══════════════════════════════════════════════════════════════════════════════

def _lowest_composite_score(data, summary):
    valid = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None
        and o.get("crescimento") is not None and o.get("oportunidade") is not None
    ]
    for o in valid:
        o["_composite"] = round(o["exposicao"] + o["vantagem"] + o["crescimento"] + o["oportunidade"], 1)
    valid.sort(key=lambda o: o["_composite"])
    bottom10 = valid[:10]
    return {
        "headline_stat": str(bottom10[0]["_composite"]).replace(".", ",") if bottom10 else "0",
        "headline_label": f"score composto mínimo — {bottom10[0].get('titulo', '')}" if bottom10 else "score composto mínimo",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["_composite"], "formatted": str(o["_composite"]).replace(".", ",")}
            for o in bottom10
        ],
        "details": {
            "bottom10": [
                {
                    "titulo": o.get("titulo", ""),
                    "composite": str(o["_composite"]).replace(".", ","),
                    "exposicao": str(o["exposicao"]).replace(".", ","),
                    "vantagem": str(o["vantagem"]).replace(".", ","),
                    "crescimento": str(o["crescimento"]).replace(".", ","),
                    "oportunidade": str(o["oportunidade"]).replace(".", ","),
                }
                for o in bottom10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Prompt templates
# ═══════════════════════════════════════════════════════════════════════════════

_PROMPT_GENDER_CREATIVE = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a representatividade feminina nas ocupações criativas do Brasil e como a IA as impacta.

DADOS (use APENAS estes números, não invente dados):
- Ocupações criativas encontradas: {num_occupations}
- Total de trabalhadores: {total_workers}
- Total feminino: {total_feminino}
- Total masculino: {total_masculino}
- Percentual feminino: {pct_feminino}
- Percentual masculino: {pct_masculino}
- Exposição média à IA: {avg_exposicao} (escala 0-10)

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_SALARY_BAND = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações na faixa salarial {band_label} e sua exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Ocupações na faixa: {count}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Top 5 ocupações por empregados: {top5}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_GROWING_SAFE = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações que crescem e têm baixo risco de IA — o melhor dos dois mundos.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com saldo positivo e exposição ≤3: {count}
- Saldo total: {total_saldo}
- Top 10 por saldo: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_DECLINING_SAFE = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações em declínio apesar do baixo risco de IA — causas além da automação.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com saldo negativo e exposição ≤3: {count}
- Saldo total: {total_saldo}
- Top 10 mais afetadas: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_STAGNANT = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações com mercado estagnado — sem crescimento nem declínio expressivo.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com |saldo| ≤100 e ≥1000 empregados: {count}
- Total de trabalhadores: {total_workers}
- Top 10 por empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_ADMISSOES_LEADERS = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações que mais contratam no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por admissões: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_ADMISSOES_RATIO = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre rotatividade no mercado de trabalho — ocupações com maior taxa de admissões por trabalhador.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por taxa admissões/empregados (mín. 1.000 empregados): {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_SALARY_GAP = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença entre salário médio e salário de admissão — onde novos contratados ganham muito menos.

DADOS (use APENAS estes números, não invente dados):
- Top 10 maiores gaps (salário - salário admissão): {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_HIGH_OPP_LOW_SAL = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações com alta oportunidade de IA mas baixo salário — oportunidade sem recompensa.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com oportunidade ≥7 e salário <R$2.000: {count}
- Total de trabalhadores: {total_workers}
- Lista: {list}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_TRIPLE_HIGH = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações com triplo alto — exposição, vantagem e crescimento todos ≥7. Profissões na linha de frente da transformação por IA.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com triplo alto: {count}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Top 10 por empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_TRIPLE_LOW = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações com triplo baixo — exposição, vantagem e crescimento todos ≤3. Profissões irrelevantes para a IA.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com triplo baixo: {count}
- Total de trabalhadores: {total_workers}
- Top 10 por empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_CRESCIMENTO_SALDO = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) analisando se a previsão de crescimento por IA se confirma nas contratações reais.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com crescimento alto (≥7): {count_high}
  - Saldo médio: {avg_saldo_high}
- Ocupações com crescimento baixo (≤3): {count_low}
  - Saldo médio: {avg_saldo_low}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_VANTAGEM_SALARY = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a correlação entre vantagem com IA e salário.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com vantagem alta (≥7): {count_high}
  - Salário médio: {avg_salary_high}
- Ocupações com vantagem baixa (≤3): {count_low}
  - Salário médio: {avg_salary_low}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_OPP_EDUCATION = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre qual nível de escolaridade tem mais oportunidade com IA.

DADOS (use APENAS estes números, não invente dados):
- Oportunidade média por escolaridade: {by_education}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_EXPOSURE_HIST = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a distribuição dos scores de exposição à IA nas ocupações brasileiras.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações com dados: {total}
- Score mais frequente: {peak_score} ({peak_count} ocupações)
- Distribuição completa: {histogram}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_VANTAGEM_HIST = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a distribuição dos scores de vantagem com IA nas ocupações brasileiras.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações com dados: {total}
- Score mais frequente: {peak_score} ({peak_count} ocupações)
- Distribuição completa: {histogram}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_CRESCIMENTO_HIST = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a distribuição dos scores de crescimento nas ocupações brasileiras.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações com dados: {total}
- Score mais frequente: {peak_score} ({peak_count} ocupações)
- Distribuição completa: {histogram}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_OPP_RANGES = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como se distribui a oportunidade com IA entre as ocupações brasileiras.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações com dados: {total}
- Faixa mais comum: {peak_range} ({peak_count} ocupações)
- Distribuição por faixa: {ranges}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_SCORE_AVERAGES = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) com um panorama geral dos indicadores de IA no mercado de trabalho brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Exposição média nacional: {avg_exposicao} (escala 0-10)
- Vantagem média nacional: {avg_vantagem} (escala 0-10)
- Crescimento médio nacional: {avg_crescimento} (escala 0-10)
- Oportunidade média nacional: {avg_oportunidade} (escala 0-10)

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_HIGHEST_COMPOSITE = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com maior score composto (exposição + vantagem + crescimento + oportunidade).

DADOS (use APENAS estes números, não invente dados):
- Top 10 por score composto: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""

_PROMPT_LOWEST_COMPOSITE = """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com menor score composto — as menos tocadas pela IA em todas as dimensões.

DADOS (use APENAS estes números, não invente dados):
- Bottom 10 por score composto: {bottom10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}"""


# ═══════════════════════════════════════════════════════════════════════════════
# Template list
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES_BATCH_B2 = [
    {
        "id": "gender-in-creative",
        "category": "Demografia",
        "tags": ["gênero", "criativo", "demografia"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _gender_in_creative,
        "prompt_template": _PROMPT_GENDER_CREATIVE,
    },
    {
        "id": "salary-band-under-1500",
        "category": "Mercado",
        "tags": ["salário", "faixa salarial", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_band_under_1500,
        "prompt_template": _PROMPT_SALARY_BAND,
    },
    {
        "id": "salary-band-1500-2500",
        "category": "Mercado",
        "tags": ["salário", "faixa salarial", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_band_1500_2500,
        "prompt_template": _PROMPT_SALARY_BAND,
    },
    {
        "id": "salary-band-2500-5000",
        "category": "Mercado",
        "tags": ["salário", "faixa salarial", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_band_2500_5000,
        "prompt_template": _PROMPT_SALARY_BAND,
    },
    {
        "id": "salary-band-5000-10000",
        "category": "Mercado",
        "tags": ["salário", "faixa salarial", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_band_5000_10000,
        "prompt_template": _PROMPT_SALARY_BAND,
    },
    {
        "id": "salary-band-above-10000",
        "category": "Mercado",
        "tags": ["salário", "faixa salarial", "alto salário", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_band_above_10000,
        "prompt_template": _PROMPT_SALARY_BAND,
    },
    {
        "id": "growing-safe-occupations",
        "category": "Mercado",
        "tags": ["crescimento", "baixo risco", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _growing_safe_occupations,
        "prompt_template": _PROMPT_GROWING_SAFE,
    },
    {
        "id": "declining-safe-occupations",
        "category": "Mercado",
        "tags": ["declínio", "baixo risco", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _declining_safe_occupations,
        "prompt_template": _PROMPT_DECLINING_SAFE,
    },
    {
        "id": "stagnant-occupations",
        "category": "Mercado",
        "tags": ["estagnação", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _stagnant_occupations,
        "prompt_template": _PROMPT_STAGNANT,
    },
    {
        "id": "admissoes-leaders",
        "category": "Mercado",
        "tags": ["admissões", "contratação", "mercado"],
        "chart_type": "ranking_table",
        "analysis_fn": _admissoes_leaders,
        "prompt_template": _PROMPT_ADMISSOES_LEADERS,
    },
    {
        "id": "admissoes-per-worker-ratio",
        "category": "Mercado",
        "tags": ["admissões", "rotatividade", "mercado"],
        "chart_type": "ranking_table",
        "analysis_fn": _admissoes_per_worker_ratio,
        "prompt_template": _PROMPT_ADMISSOES_RATIO,
    },
    {
        "id": "salary-admissao-gap-largest",
        "category": "Mercado",
        "tags": ["salário", "admissão", "gap", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_admissao_gap_largest,
        "prompt_template": _PROMPT_SALARY_GAP,
    },
    {
        "id": "high-opportunity-low-salary",
        "category": "Mercado",
        "tags": ["oportunidade", "salário", "mercado"],
        "chart_type": "ranking_table",
        "analysis_fn": _high_opportunity_low_salary,
        "prompt_template": _PROMPT_HIGH_OPP_LOW_SAL,
    },
    {
        "id": "triple-high",
        "category": "Mercado",
        "tags": ["exposição", "vantagem", "crescimento", "mercado"],
        "chart_type": "ranking_table",
        "analysis_fn": _triple_high,
        "prompt_template": _PROMPT_TRIPLE_HIGH,
    },
    {
        "id": "triple-low",
        "category": "Mercado",
        "tags": ["exposição", "vantagem", "crescimento", "mercado"],
        "chart_type": "ranking_table",
        "analysis_fn": _triple_low,
        "prompt_template": _PROMPT_TRIPLE_LOW,
    },
    {
        "id": "crescimento-vs-saldo",
        "category": "Mercado",
        "tags": ["crescimento", "saldo", "mercado"],
        "chart_type": "comparison_pair",
        "analysis_fn": _crescimento_vs_saldo,
        "prompt_template": _PROMPT_CRESCIMENTO_SALDO,
    },
    {
        "id": "vantagem-vs-salary-correlation",
        "category": "Mercado",
        "tags": ["vantagem", "salário", "correlação", "mercado"],
        "chart_type": "comparison_pair",
        "analysis_fn": _vantagem_vs_salary_correlation,
        "prompt_template": _PROMPT_VANTAGEM_SALARY,
    },
    {
        "id": "opportunity-by-education",
        "category": "Educação",
        "tags": ["oportunidade", "escolaridade", "educação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _opportunity_by_education,
        "prompt_template": _PROMPT_OPP_EDUCATION,
    },
    {
        "id": "exposure-histogram",
        "category": "Mercado",
        "tags": ["exposição", "distribuição", "histograma"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _exposure_histogram,
        "prompt_template": _PROMPT_EXPOSURE_HIST,
    },
    {
        "id": "vantagem-histogram",
        "category": "Mercado",
        "tags": ["vantagem", "distribuição", "histograma"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _vantagem_histogram,
        "prompt_template": _PROMPT_VANTAGEM_HIST,
    },
    {
        "id": "crescimento-histogram",
        "category": "Mercado",
        "tags": ["crescimento", "distribuição", "histograma"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _crescimento_histogram,
        "prompt_template": _PROMPT_CRESCIMENTO_HIST,
    },
    {
        "id": "oportunidade-ranges",
        "category": "Mercado",
        "tags": ["oportunidade", "distribuição", "faixas"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _oportunidade_ranges,
        "prompt_template": _PROMPT_OPP_RANGES,
    },
    {
        "id": "score-averages-overview",
        "category": "Mercado",
        "tags": ["panorama", "médias", "mercado"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _score_averages_overview,
        "prompt_template": _PROMPT_SCORE_AVERAGES,
    },
    {
        "id": "highest-composite-score",
        "category": "Ocupações",
        "tags": ["composto", "ranking", "ocupações"],
        "chart_type": "ranking_table",
        "analysis_fn": _highest_composite_score,
        "prompt_template": _PROMPT_HIGHEST_COMPOSITE,
    },
    {
        "id": "lowest-composite-score",
        "category": "Ocupações",
        "tags": ["composto", "ranking", "ocupações"],
        "chart_type": "ranking_table",
        "analysis_fn": _lowest_composite_score,
        "prompt_template": _PROMPT_LOWEST_COMPOSITE,
    },
]


def get_templates_batch_b2():
    return TEMPLATES_BATCH_B2
