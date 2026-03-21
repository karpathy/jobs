"""Insight templates batch C1: score analyses + thematic stories."""
import statistics
from insight_templates import _fmt_pct, _fmt_num, _safe_avg


# ─── Grande grupo short-name mapping ─────────────────────────────────────────

_GG_SHORT = {
    "MEMBROS SUPERIORES DO PODER PÚBLICO, DIRIGENTES DE ORGANIZAÇÕES DE INTERESSE PÚBLICO E DE EMPRESAS E GERENTES": "Dirigentes",
    "PROFISSIONAIS DAS CIÊNCIAS E DAS ARTES": "Ciências/Artes",
    "TÉCNICOS DE NIVEL MÉDIO": "Técnicos",
    "TRABALHADORES DE SERVIÇOS ADMINISTRATIVOS": "Administrativos",
    "TRABALHADORES DOS SERVIÇOS, VENDEDORES DO COMÉRCIO EM LOJAS E MERCADOS": "Serviços/Comércio",
    "TRABALHADORES AGROPECUÁRIOS, FLORESTAIS, DA CAÇA E DA PESCA": "Agropecuária",
    "TRABALHADORES DA PRODUÇÃO DE BENS E SERVIÇOS INDUSTRIAIS": "Produção Industrial",
    "TRABALHADORES EM SERVIÇOS DE REPARAÇÃO E MANUTENÇÃO": "Reparação",
    "MEMBROS DAS FORÇAS ARMADAS, POLICIAIS E BOMBEIROS MILITARES": "Forças Armadas",
}


def _gg_short(name):
    """Return short name for a grande_grupo, trying substring match."""
    if not name:
        return "Outros"
    upper = name.upper()
    for key, short in _GG_SHORT.items():
        if key in upper or upper in key:
            return short
    # partial match
    for key, short in _GG_SHORT.items():
        if key[:20] in upper or upper[:20] in key:
            return short
    return name[:25]


# ═══════════════════════════════════════════════════════════════════════════════
# Template 197: exposure-equals-vantagem
# ═══════════════════════════════════════════════════════════════════════════════

def _exposure_equals_vantagem(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None
        and abs(o["exposicao"] - o["vantagem"]) <= 1
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações com exposição ≈ vantagem IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "top_occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0),
                 "exposicao": str(o["exposicao"]), "vantagem": str(o["vantagem"])}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 198: exposure-exceeds-vantagem
# ═══════════════════════════════════════════════════════════════════════════════

def _exposure_exceeds_vantagem(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None
        and (o["exposicao"] - o["vantagem"]) >= 3
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações onde a IA ameaça mais do que ajuda",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "top_occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0),
                 "exposicao": str(o["exposicao"]), "vantagem": str(o["vantagem"])}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 199: vantagem-exceeds-exposure
# ═══════════════════════════════════════════════════════════════════════════════

def _vantagem_exceeds_exposure(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None
        and (o["vantagem"] - o["exposicao"]) >= 3
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações onde a IA ajuda mais do que ameaça",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "top_occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0),
                 "exposicao": str(o["exposicao"]), "vantagem": str(o["vantagem"])}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 200: high-crescimento-low-exposure
# ═══════════════════════════════════════════════════════════════════════════════

def _high_crescimento_low_exposure(data, summary):
    matches = [
        o for o in data
        if o.get("crescimento") is not None and o.get("exposicao") is not None
        and o["crescimento"] >= 7 and o["exposicao"] <= 3
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações com alta demanda e baixa disrupção por IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0),
                 "crescimento": str(o["crescimento"]), "exposicao": str(o["exposicao"])}
                for o in matches[:15]
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 201: low-crescimento-high-exposure
# ═══════════════════════════════════════════════════════════════════════════════

def _low_crescimento_high_exposure(data, summary):
    matches = [
        o for o in data
        if o.get("crescimento") is not None and o.get("exposicao") is not None
        and o["crescimento"] <= 3 and o["exposicao"] >= 7
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações em declínio E altamente expostas à IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0),
                 "crescimento": str(o["crescimento"]), "exposicao": str(o["exposicao"])}
                for o in matches[:15]
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 202: oportunidade-above-8
# ═══════════════════════════════════════════════════════════════════════════════

def _oportunidade_above_8(data, summary):
    matches = [o for o in data if o.get("oportunidade") is not None and o["oportunidade"] >= 8]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações com oportunidade IA ≥ 8",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0),
                 "oportunidade": str(o["oportunidade"]).replace(".", ",")}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 203: oportunidade-below-3
# ═══════════════════════════════════════════════════════════════════════════════

def _oportunidade_below_3(data, summary):
    matches = [o for o in data if o.get("oportunidade") is not None and o["oportunidade"] <= 3]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações com oportunidade IA ≤ 3",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 204: exposure-median-analysis
# ═══════════════════════════════════════════════════════════════════════════════

def _exposure_median_analysis(data, summary):
    valid = [o for o in data if o.get("exposicao") is not None]
    if not valid:
        return {"headline_stat": "0", "headline_label": "dados insuficientes", "chart_data": [], "details": {}}
    exp_vals = [o["exposicao"] for o in valid]
    median = statistics.median(exp_vals)
    above = [o for o in valid if o["exposicao"] > median]
    below = [o for o in valid if o["exposicao"] <= median]
    w_above = sum(o.get("empregados") or 0 for o in above)
    w_below = sum(o.get("empregados") or 0 for o in below)
    return {
        "headline_stat": str(median).replace(".", ","),
        "headline_label": "mediana de exposição à IA (escala 0-10)",
        "chart_data": [
            {"label": "Acima da mediana", "value": w_above, "formatted": _fmt_num(w_above)},
            {"label": "Abaixo da mediana", "value": w_below, "formatted": _fmt_num(w_below)},
        ],
        "details": {
            "median": str(median).replace(".", ","),
            "count_above": str(len(above)),
            "count_below": str(len(below)),
            "workers_above": _fmt_num(w_above),
            "workers_below": _fmt_num(w_below),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 205: scores-by-grande-grupo
# ═══════════════════════════════════════════════════════════════════════════════

def _scores_by_grande_grupo(data, summary):
    groups = {}
    for o in data:
        gg = o.get("grande_grupo") or "Outros"
        if gg not in groups:
            groups[gg] = []
        groups[gg].append(o)
    rows = []
    for gg, occs in sorted(groups.items()):
        short = _gg_short(gg)
        rows.append({
            "label": short,
            "avg_exposicao": round(_safe_avg([o.get("exposicao") for o in occs if o.get("exposicao") is not None]), 1),
            "avg_vantagem": round(_safe_avg([o.get("vantagem") for o in occs if o.get("vantagem") is not None]), 1),
            "avg_crescimento": round(_safe_avg([o.get("crescimento") for o in occs if o.get("crescimento") is not None]), 1),
            "avg_oportunidade": round(_safe_avg([o.get("oportunidade") for o in occs if o.get("oportunidade") is not None]), 1),
        })
    return {
        "headline_stat": str(len(rows)),
        "headline_label": "grandes grupos ocupacionais analisados",
        "chart_data": [
            {"label": r["label"], "value": r["avg_exposicao"], "formatted": str(r["avg_exposicao"]).replace(".", ",")}
            for r in rows
        ],
        "details": {
            "groups": [
                {"grupo": r["label"],
                 "avg_exposicao": str(r["avg_exposicao"]).replace(".", ","),
                 "avg_vantagem": str(r["avg_vantagem"]).replace(".", ","),
                 "avg_crescimento": str(r["avg_crescimento"]).replace(".", ","),
                 "avg_oportunidade": str(r["avg_oportunidade"]).replace(".", ",")}
                for r in rows
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 206: scores-by-education
# ═══════════════════════════════════════════════════════════════════════════════

_EDU_ORDER = [
    "Analfabeto", "Até 5ª Incompleto", "5ª Completo Fundamental",
    "6ª a 9ª Fundamental", "Fundamental Completo", "Médio Incompleto",
    "Médio Completo", "Superior Incompleto", "Superior Completo",
    "Mestrado", "Doutorado",
]


def _edu_sort_key(name):
    upper = (name or "").strip()
    for i, e in enumerate(_EDU_ORDER):
        if e.lower() in upper.lower() or upper.lower() in e.lower():
            return i
    return 99


def _scores_by_education(data, summary):
    groups = {}
    for o in data:
        esc = o.get("escolaridade") or "Não informado"
        if esc not in groups:
            groups[esc] = []
        groups[esc].append(o)
    rows = []
    for esc, occs in sorted(groups.items(), key=lambda x: _edu_sort_key(x[0])):
        rows.append({
            "label": esc,
            "avg_exposicao": round(_safe_avg([o.get("exposicao") for o in occs if o.get("exposicao") is not None]), 1),
            "avg_vantagem": round(_safe_avg([o.get("vantagem") for o in occs if o.get("vantagem") is not None]), 1),
            "avg_crescimento": round(_safe_avg([o.get("crescimento") for o in occs if o.get("crescimento") is not None]), 1),
            "avg_oportunidade": round(_safe_avg([o.get("oportunidade") for o in occs if o.get("oportunidade") is not None]), 1),
        })
    return {
        "headline_stat": str(len(rows)),
        "headline_label": "níveis de escolaridade analisados",
        "chart_data": [
            {"label": r["label"], "value": r["avg_exposicao"], "formatted": str(r["avg_exposicao"]).replace(".", ",")}
            for r in rows
        ],
        "details": {
            "education_levels": [
                {"escolaridade": r["label"],
                 "avg_exposicao": str(r["avg_exposicao"]).replace(".", ","),
                 "avg_vantagem": str(r["avg_vantagem"]).replace(".", ","),
                 "avg_crescimento": str(r["avg_crescimento"]).replace(".", ","),
                 "avg_oportunidade": str(r["avg_oportunidade"]).replace(".", ",")}
                for r in rows
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 207: perfect-storm-occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _perfect_storm_occupations(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None and o.get("crescimento") is not None
        and o["exposicao"] >= 7 and o["vantagem"] <= 3 and o["crescimento"] <= 3
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações na \"tempestade perfeita\" da IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0),
                 "exposicao": str(o["exposicao"]), "vantagem": str(o["vantagem"]),
                 "crescimento": str(o["crescimento"])}
                for o in matches[:15]
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 208: golden-occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _golden_occupations(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None
        and o.get("crescimento") is not None and o.get("oportunidade") is not None
        and o["exposicao"] >= 7 and o["vantagem"] >= 7
        and o["crescimento"] >= 7 and o["oportunidade"] >= 7
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações \"de ouro\" — todos os scores ≥ 7",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0)}
                for o in matches[:15]
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 209: digital-vs-physical
# ═══════════════════════════════════════════════════════════════════════════════

_DIGITAL_KW = ["ADMINISTRATIVOS", "CIÊNCIAS", "TÉCNICOS"]
_PHYSICAL_KW = ["AGROPECUÁRIOS", "PRODUÇÃO", "REPARAÇÃO"]


def _digital_vs_physical(data, summary):
    digital = [o for o in data if o.get("grande_grupo") and any(kw in o["grande_grupo"].upper() for kw in _DIGITAL_KW)]
    physical = [o for o in data if o.get("grande_grupo") and any(kw in o["grande_grupo"].upper() for kw in _PHYSICAL_KW)]
    d_w = sum(o.get("empregados") or 0 for o in digital)
    p_w = sum(o.get("empregados") or 0 for o in physical)
    d_exp = round(_safe_avg([o.get("exposicao") for o in digital if o.get("exposicao") is not None]), 1)
    p_exp = round(_safe_avg([o.get("exposicao") for o in physical if o.get("exposicao") is not None]), 1)
    d_sal = round(_safe_avg([o["salario"] for o in digital if o.get("salario")])) if any(o.get("salario") for o in digital) else 0
    p_sal = round(_safe_avg([o["salario"] for o in physical if o.get("salario")])) if any(o.get("salario") for o in physical) else 0
    return {
        "headline_stat": str(d_exp).replace(".", ",") + " vs " + str(p_exp).replace(".", ","),
        "headline_label": "exposição média: digital vs físico",
        "chart_data": [
            {"label": "Digital — exposição", "value": d_exp, "formatted": str(d_exp).replace(".", ",")},
            {"label": "Físico — exposição", "value": p_exp, "formatted": str(p_exp).replace(".", ",")},
        ],
        "details": {
            "digital_workers": _fmt_num(d_w),
            "physical_workers": _fmt_num(p_w),
            "digital_avg_exposure": str(d_exp).replace(".", ","),
            "physical_avg_exposure": str(p_exp).replace(".", ","),
            "digital_avg_salary": "R$ " + _fmt_num(d_sal),
            "physical_avg_salary": "R$ " + _fmt_num(p_sal),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 210: ai-displacement-estimate
# ═══════════════════════════════════════════════════════════════════════════════

def _ai_displacement_estimate(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None
        and o["exposicao"] >= 8 and o["vantagem"] <= 4
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    top10 = matches[:10]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores com maior risco de deslocamento por IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "top_occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 211: ai-creation-estimate
# ═══════════════════════════════════════════════════════════════════════════════

def _ai_creation_estimate(data, summary):
    matches = [o for o in data if o.get("crescimento") is not None and o["crescimento"] >= 8]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    top10 = matches[:10]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores em ocupações que a IA expande",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 212: net-ai-effect
# ═══════════════════════════════════════════════════════════════════════════════

def _net_ai_effect(data, summary):
    displaced = [
        o for o in data
        if o.get("exposicao") is not None and o.get("vantagem") is not None
        and o["exposicao"] >= 8 and o["vantagem"] <= 4
    ]
    created = [o for o in data if o.get("crescimento") is not None and o["crescimento"] >= 8]
    w_disp = sum(o.get("empregados") or 0 for o in displaced)
    w_crea = sum(o.get("empregados") or 0 for o in created)
    net = w_crea - w_disp
    sign = "+" if net >= 0 else ""
    return {
        "headline_stat": sign + _fmt_num(net),
        "headline_label": "efeito líquido estimado da IA em empregos",
        "chart_data": [
            {"label": "Deslocamento", "value": w_disp, "formatted": _fmt_num(w_disp)},
            {"label": "Criação/Expansão", "value": w_crea, "formatted": _fmt_num(w_crea)},
        ],
        "details": {
            "displacement_count": str(len(displaced)),
            "displacement_workers": _fmt_num(w_disp),
            "creation_count": str(len(created)),
            "creation_workers": _fmt_num(w_crea),
            "net_effect": sign + _fmt_num(net),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 213: retraining-scale
# ═══════════════════════════════════════════════════════════════════════════════

def _retraining_scale(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o.get("salario") is not None
        and o["exposicao"] >= 7 and o["salario"] < 3000
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores expostos à IA com salário < R$ 3.000",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 214: ai-salary-premium
# ═══════════════════════════════════════════════════════════════════════════════

def _ai_salary_premium(data, summary):
    high_opp = [o for o in data if o.get("oportunidade") is not None and o.get("salario") is not None and o["oportunidade"] >= 7]
    low_opp = [o for o in data if o.get("oportunidade") is not None and o.get("salario") is not None and o["oportunidade"] <= 3]
    avg_high = round(_safe_avg([o["salario"] for o in high_opp])) if high_opp else 0
    avg_low = round(_safe_avg([o["salario"] for o in low_opp])) if low_opp else 0
    diff = avg_high - avg_low
    pct_diff = round(diff / avg_low * 100, 1) if avg_low else 0
    return {
        "headline_stat": _fmt_pct(pct_diff) if avg_low else "N/D",
        "headline_label": "prêmio salarial da oportunidade IA",
        "chart_data": [
            {"label": "Oportunidade ≥ 7", "value": avg_high, "formatted": "R$ " + _fmt_num(avg_high)},
            {"label": "Oportunidade ≤ 3", "value": avg_low, "formatted": "R$ " + _fmt_num(avg_low)},
        ],
        "details": {
            "avg_salary_high_opp": "R$ " + _fmt_num(avg_high),
            "avg_salary_low_opp": "R$ " + _fmt_num(avg_low),
            "count_high": str(len(high_opp)),
            "count_low": str(len(low_opp)),
            "salary_diff": "R$ " + _fmt_num(diff),
            "pct_diff": _fmt_pct(pct_diff),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 215: white-collar-blue-collar
# ═══════════════════════════════════════════════════════════════════════════════

_WHITE_COLLAR_KW = ["SUPERIORES", "CIÊNCIAS", "TÉCNICOS", "ADMINISTRATIVOS"]


def _white_collar_blue_collar(data, summary):
    white = [o for o in data if o.get("grande_grupo") and any(kw in o["grande_grupo"].upper() for kw in _WHITE_COLLAR_KW)]
    blue = [o for o in data if o.get("grande_grupo") and not any(kw in o["grande_grupo"].upper() for kw in _WHITE_COLLAR_KW)]
    ww = sum(o.get("empregados") or 0 for o in white)
    bw = sum(o.get("empregados") or 0 for o in blue)
    w_exp = round(_safe_avg([o.get("exposicao") for o in white if o.get("exposicao") is not None]), 1)
    b_exp = round(_safe_avg([o.get("exposicao") for o in blue if o.get("exposicao") is not None]), 1)
    w_sal = round(_safe_avg([o["salario"] for o in white if o.get("salario")])) if any(o.get("salario") for o in white) else 0
    b_sal = round(_safe_avg([o["salario"] for o in blue if o.get("salario")])) if any(o.get("salario") for o in blue) else 0
    return {
        "headline_stat": str(w_exp).replace(".", ",") + " vs " + str(b_exp).replace(".", ","),
        "headline_label": "exposição: colarinho branco vs azul",
        "chart_data": [
            {"label": "Colarinho branco", "value": w_exp, "formatted": str(w_exp).replace(".", ",")},
            {"label": "Colarinho azul", "value": b_exp, "formatted": str(b_exp).replace(".", ",")},
        ],
        "details": {
            "white_collar_workers": _fmt_num(ww),
            "blue_collar_workers": _fmt_num(bw),
            "white_collar_avg_exposure": str(w_exp).replace(".", ","),
            "blue_collar_avg_exposure": str(b_exp).replace(".", ","),
            "white_collar_avg_salary": "R$ " + _fmt_num(w_sal),
            "blue_collar_avg_salary": "R$ " + _fmt_num(b_sal),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 216: routine-cognitive-jobs
# ═══════════════════════════════════════════════════════════════════════════════

def _routine_cognitive_jobs(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None and o.get("salario") is not None
        and o["exposicao"] >= 7 and 2000 <= o["salario"] <= 5000
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    top10 = matches[:10]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores em empregos cognitivos rotineiros em risco",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "top_occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0),
                 "salario": "R$ " + _fmt_num(round(o["salario"]))}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 217: knowledge-economy-size
# ═══════════════════════════════════════════════════════════════════════════════

def _knowledge_economy_size(data, summary):
    all_w = sum(o.get("empregados") or 0 for o in data)
    matches = [o for o in data if o.get("exposicao") is not None and o["exposicao"] >= 6]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    pct = round(total_w / all_w * 100, 1) if all_w else 0
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    return {
        "headline_stat": _fmt_pct(pct),
        "headline_label": "da força de trabalho na economia do conhecimento",
        "chart_data": [
            {"label": "Economia do conhecimento (exp≥6)", "value": total_w, "formatted": _fmt_num(total_w)},
            {"label": "Demais", "value": all_w - total_w, "formatted": _fmt_num(all_w - total_w)},
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "pct_total": _fmt_pct(pct),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 218: service-economy-size
# ═══════════════════════════════════════════════════════════════════════════════

def _service_economy_size(data, summary):
    all_w = sum(o.get("empregados") or 0 for o in data)
    matches = [o for o in data if o.get("grande_grupo") and "SERVIÇOS" in o["grande_grupo"].upper() and "VENDEDOR" in o["grande_grupo"].upper()]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    pct = round(total_w / all_w * 100, 1) if all_w else 0
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    return {
        "headline_stat": _fmt_pct(pct),
        "headline_label": "da força de trabalho em serviços e comércio",
        "chart_data": [
            {"label": "Serviços/Comércio", "value": total_w, "formatted": _fmt_num(total_w)},
            {"label": "Demais", "value": all_w - total_w, "formatted": _fmt_num(all_w - total_w)},
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "pct_total": _fmt_pct(pct),
            "avg_exposicao": str(avg_exp).replace(".", ","),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 219: industrial-workforce-profile
# ═══════════════════════════════════════════════════════════════════════════════

def _industrial_workforce_profile(data, summary):
    matches = [o for o in data if o.get("grande_grupo") and "PRODUÇÃO" in o["grande_grupo"].upper()]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores na produção industrial",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "num_occupations": str(len(matches)),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 220: gig-vulnerability-proxy
# ═══════════════════════════════════════════════════════════════════════════════

def _gig_vulnerability_proxy(data, summary):
    matches = [
        o for o in data
        if o.get("salario") is not None and o.get("admissoes") is not None and o.get("empregados") is not None
        and o["salario"] < 2000 and o["empregados"] > 0 and (o["admissoes"] / o["empregados"]) > 0.5
    ]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "trabalhadores em ocupações de alta rotatividade e baixo salário",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 221: early-automation-wave
# ═══════════════════════════════════════════════════════════════════════════════

def _early_automation_wave(data, summary):
    matches = [o for o in data if o.get("exposicao") is not None and o["exposicao"] >= 9]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações na primeira onda de automação por IA",
        "chart_data": [
            {"label": o["titulo"], "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "occupations": [
                {"titulo": o["titulo"], "workers": _fmt_num(o.get("empregados") or 0)}
                for o in matches[:15]
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template list
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES_BATCH_C1 = [
    # 197
    {
        "id": "exposure-equals-vantagem",
        "category": "Ocupações",
        "tags": ["exposição", "vantagem", "equilíbrio"],
        "chart_type": "ranking_table",
        "analysis_fn": _exposure_equals_vantagem,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações onde exposição e vantagem da IA são praticamente iguais — nem ameaça nem benefício claro.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 198
    {
        "id": "exposure-exceeds-vantagem",
        "category": "Ocupações",
        "tags": ["exposição", "vantagem", "ameaça"],
        "chart_type": "ranking_table",
        "analysis_fn": _exposure_exceeds_vantagem,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações onde a IA ameaça muito mais do que ajuda — exposição supera vantagem em 3+ pontos.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 199
    {
        "id": "vantagem-exceeds-exposure",
        "category": "Ocupações",
        "tags": ["exposição", "vantagem", "benefício"],
        "chart_type": "ranking_table",
        "analysis_fn": _vantagem_exceeds_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações onde a IA ajuda muito mais do que ameaça — vantagem supera exposição em 3+ pontos.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 200
    {
        "id": "high-crescimento-low-exposure",
        "category": "Ocupações",
        "tags": ["crescimento", "exposição", "oportunidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _high_crescimento_low_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações em alta demanda e baixa disrupção por IA — as carreiras mais seguras e promissoras.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Ocupações: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 201
    {
        "id": "low-crescimento-high-exposure",
        "category": "Ocupações",
        "tags": ["crescimento", "exposição", "risco"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _low_crescimento_high_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações em declínio E altamente expostas à IA — a pior combinação possível para trabalhadores.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Ocupações: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 202
    {
        "id": "oportunidade-above-8",
        "category": "Ocupações",
        "tags": ["oportunidade", "alta"],
        "chart_type": "ranking_table",
        "analysis_fn": _oportunidade_above_8,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações com altíssima oportunidade de IA (score ≥ 8). Que carreiras mais se beneficiam?

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 203
    {
        "id": "oportunidade-below-3",
        "category": "Ocupações",
        "tags": ["oportunidade", "baixa"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _oportunidade_below_3,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações com baixíssima oportunidade de IA (score ≤ 3). A IA não ajuda nem ameaça — por quê?

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 204
    {
        "id": "exposure-median-analysis",
        "category": "Mercado",
        "tags": ["exposição", "mediana", "distribuição"],
        "chart_type": "comparison_pair",
        "analysis_fn": _exposure_median_analysis,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a mediana de exposição à IA e como o mercado se divide.

DADOS (use APENAS estes números, não invente dados):
- Mediana de exposição: {median} (escala 0-10)
- Ocupações acima da mediana: {count_above}
- Ocupações abaixo da mediana: {count_below}
- Trabalhadores acima: {workers_above}
- Trabalhadores abaixo: {workers_below}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 205
    {
        "id": "scores-by-grande-grupo",
        "category": "Setores",
        "tags": ["grande grupo", "scores", "comparação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _scores_by_grande_grupo,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando os scores médios de IA por grande grupo ocupacional.

DADOS (use APENAS estes números, não invente dados):
- Grupos analisados: {groups}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 206
    {
        "id": "scores-by-education",
        "category": "Educação",
        "tags": ["escolaridade", "scores", "comparação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _scores_by_education,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como os scores de IA variam por nível de escolaridade. Mais educação = mais exposto?

DADOS (use APENAS estes números, não invente dados):
- Níveis de escolaridade: {education_levels}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 207
    {
        "id": "perfect-storm-occupations",
        "category": "Ocupações",
        "tags": ["risco", "tempestade perfeita"],
        "chart_type": "ranking_table",
        "analysis_fn": _perfect_storm_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações na "tempestade perfeita": alta exposição à IA, baixa vantagem, baixo crescimento.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Ocupações: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 208
    {
        "id": "golden-occupations",
        "category": "Ocupações",
        "tags": ["oportunidade", "ouro", "destaque"],
        "chart_type": "ranking_table",
        "analysis_fn": _golden_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações "de ouro" onde todos os 4 scores de IA são ≥ 7 — alta exposição, alta vantagem, alto crescimento, alta oportunidade.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {count}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Ocupações: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 209
    {
        "id": "digital-vs-physical",
        "category": "Setores",
        "tags": ["digital", "físico", "comparação"],
        "chart_type": "comparison_pair",
        "analysis_fn": _digital_vs_physical,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando o impacto da IA em setores digitais vs físicos. Quem sofre mais?

DADOS (use APENAS estes números, não invente dados):
- Trabalhadores digitais: {digital_workers}
- Trabalhadores físicos: {physical_workers}
- Exposição média digital: {digital_avg_exposure}
- Exposição média física: {physical_avg_exposure}
- Salário médio digital: {digital_avg_salary}
- Salário médio físico: {physical_avg_salary}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 210
    {
        "id": "ai-displacement-estimate",
        "category": "Mercado",
        "tags": ["deslocamento", "risco", "estimativa"],
        "chart_type": "ranking_table",
        "analysis_fn": _ai_displacement_estimate,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre trabalhadores com maior risco de deslocamento por IA — alta exposição e baixa vantagem.

DADOS (use APENAS estes números, não invente dados):
- Ocupações em risco: {count}
- Total de trabalhadores: {total_workers}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 211
    {
        "id": "ai-creation-estimate",
        "category": "Mercado",
        "tags": ["criação", "crescimento", "estimativa"],
        "chart_type": "ranking_table",
        "analysis_fn": _ai_creation_estimate,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre empregos que a IA está criando ou expandindo — ocupações com crescimento ≥ 8.

DADOS (use APENAS estes números, não invente dados):
- Ocupações em expansão: {count}
- Total de trabalhadores: {total_workers}
- Ocupações: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 212
    {
        "id": "net-ai-effect",
        "category": "Mercado",
        "tags": ["efeito líquido", "deslocamento", "criação"],
        "chart_type": "comparison_pair",
        "analysis_fn": _net_ai_effect,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o efeito líquido da IA no emprego: quantos empregos são deslocados vs criados/expandidos?

DADOS (use APENAS estes números, não invente dados):
- Ocupações em risco de deslocamento: {displacement_count}
- Trabalhadores em risco: {displacement_workers}
- Ocupações em expansão: {creation_count}
- Trabalhadores em expansão: {creation_workers}
- Efeito líquido: {net_effect}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 213
    {
        "id": "retraining-scale",
        "category": "Mercado",
        "tags": ["requalificação", "salário", "vulnerabilidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _retraining_scale,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre trabalhadores que precisam de requalificação mas não têm recursos — alta exposição e salário abaixo de R$ 3.000.

DADOS (use APENAS estes números, não invente dados):
- Ocupações afetadas: {count}
- Total de trabalhadores: {total_workers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 214
    {
        "id": "ai-salary-premium",
        "category": "Mercado",
        "tags": ["salário", "oportunidade", "prêmio"],
        "chart_type": "comparison_pair",
        "analysis_fn": _ai_salary_premium,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o prêmio salarial da oportunidade IA: quem tem alta oportunidade ganha mais?

DADOS (use APENAS estes números, não invente dados):
- Salário médio alta oportunidade (≥7): {avg_salary_high_opp}
- Salário médio baixa oportunidade (≤3): {avg_salary_low_opp}
- Ocupações alta oportunidade: {count_high}
- Ocupações baixa oportunidade: {count_low}
- Diferença salarial: {salary_diff}
- Diferença percentual: {pct_diff}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 215
    {
        "id": "white-collar-blue-collar",
        "category": "Setores",
        "tags": ["colarinho branco", "colarinho azul", "comparação"],
        "chart_type": "comparison_pair",
        "analysis_fn": _white_collar_blue_collar,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando o impacto da IA em trabalhadores de colarinho branco vs azul.

DADOS (use APENAS estes números, não invente dados):
- Trabalhadores colarinho branco: {white_collar_workers}
- Trabalhadores colarinho azul: {blue_collar_workers}
- Exposição média branco: {white_collar_avg_exposure}
- Exposição média azul: {blue_collar_avg_exposure}
- Salário médio branco: {white_collar_avg_salary}
- Salário médio azul: {blue_collar_avg_salary}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 216
    {
        "id": "routine-cognitive-jobs",
        "category": "Mercado",
        "tags": ["cognitivo", "rotineiro", "risco"],
        "chart_type": "ranking_table",
        "analysis_fn": _routine_cognitive_jobs,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre trabalho cognitivo rotineiro em risco — alta exposição à IA com salários entre R$ 2.000 e R$ 5.000.

DADOS (use APENAS estes números, não invente dados):
- Ocupações afetadas: {count}
- Total de trabalhadores: {total_workers}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 217
    {
        "id": "knowledge-economy-size",
        "category": "Mercado",
        "tags": ["economia do conhecimento", "perfil"],
        "chart_type": "comparison_pair",
        "analysis_fn": _knowledge_economy_size,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o tamanho da economia do conhecimento no Brasil — trabalhadores com exposição IA ≥ 6.

DADOS (use APENAS estes números, não invente dados):
- Ocupações: {count}
- Total de trabalhadores: {total_workers}
- Percentual do total: {pct_total}
- Salário médio: {avg_salary}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 218
    {
        "id": "service-economy-size",
        "category": "Setores",
        "tags": ["serviços", "comércio", "perfil"],
        "chart_type": "comparison_pair",
        "analysis_fn": _service_economy_size,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o setor de serviços e comércio — o maior empregador do Brasil. Como a IA o afeta?

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores: {total_workers}
- Percentual do total: {pct_total}
- Exposição média: {avg_exposicao}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 219
    {
        "id": "industrial-workforce-profile",
        "category": "Setores",
        "tags": ["indústria", "produção", "perfil"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _industrial_workforce_profile,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o perfil da força de trabalho industrial brasileira diante da IA.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores: {total_workers}
- Número de ocupações: {num_occupations}
- Exposição média: {avg_exposicao}
- Salário médio: {avg_salary}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 220
    {
        "id": "gig-vulnerability-proxy",
        "category": "Mercado",
        "tags": ["rotatividade", "precarização", "vulnerabilidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _gig_vulnerability_proxy,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações com alta rotatividade e baixo salário — proxy para trabalho precarizado vulnerável à IA.

DADOS (use APENAS estes números, não invente dados):
- Ocupações afetadas: {count}
- Total de trabalhadores: {total_workers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 221
    {
        "id": "early-automation-wave",
        "category": "Mercado",
        "tags": ["automação", "primeira onda", "exposição extrema"],
        "chart_type": "ranking_table",
        "analysis_fn": _early_automation_wave,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a primeira onda de automação por IA — ocupações com exposição ≥ 9.

DADOS (use APENAS estes números, não invente dados):
- Ocupações afetadas: {count}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Ocupações: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates_batch_c1():
    return TEMPLATES_BATCH_C1
