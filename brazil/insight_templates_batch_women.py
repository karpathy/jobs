"""Insight templates: impact of AI on women in the Brazilian workforce."""
import statistics
from insight_templates import _fmt_pct, _fmt_num, _safe_avg


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _keyword_filter(data, keywords):
    """Return occupations whose titulo contains any keyword (case-insensitive)."""
    matches = []
    for o in data:
        titulo = o.get("titulo", "").lower()
        if any(kw in titulo for kw in keywords):
            matches.append(o)
    return matches


def _with_demographics(data):
    """Return occupations that have non-None demographics with gender data."""
    return [o for o in data if o.get("demographics") and
            o["demographics"].get("total_feminino") is not None and
            o["demographics"].get("total_masculino") is not None]


def _pct_female(o):
    """Return % female for an occupation, or None."""
    d = o.get("demographics")
    if not d:
        return None
    f = d.get("total_feminino") or 0
    m = d.get("total_masculino") or 0
    total = f + m
    if total == 0:
        return None
    return f / total * 100


def _gg_filter(data, gg_fragment):
    """Return occupations matching grande_grupo fragment (case-insensitive)."""
    fragment = gg_fragment.upper()
    return [o for o in data if fragment in (o.get("grande_grupo") or "").upper()]


# ─── 297: women-total-workforce ──────────────────────────────────────────────

def _women_total_workforce(data, summary):
    dem = summary["demographics"]
    total_f = dem["total_feminino"]
    total_m = dem["total_masculino"]
    total = total_f + total_m
    pct_f = (total_f / total * 100) if total else 0
    pct_m = (total_m / total * 100) if total else 0
    return {
        "headline_stat": _fmt_num(total_f),
        "headline_label": "mulheres na força de trabalho formal analisada",
        "chart_data": [
            {"label": "Mulheres", "value": total_f, "formatted": _fmt_num(total_f)},
            {"label": "Homens", "value": total_m, "formatted": _fmt_num(total_m)},
        ],
        "details": {
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_geral": _fmt_num(total),
            "pct_feminino": _fmt_pct(pct_f),
            "pct_masculino": _fmt_pct(pct_m),
        },
    }


# ─── 298: women-high-risk-total ──────────────────────────────────────────────

def _women_high_risk_total(data, summary):
    dem = summary["demographics"]
    hr_f = dem["high_risk_feminino"]
    total_f = dem["total_feminino"]
    pct = (hr_f / total_f * 100) if total_f else 0
    hr_m = dem["high_risk_masculino"]
    total_m = dem["total_masculino"]
    pct_m = (hr_m / total_m * 100) if total_m else 0
    return {
        "headline_stat": _fmt_num(hr_f),
        "headline_label": "mulheres em ocupações de alto risco de IA",
        "chart_data": [
            {"label": "Mulheres em alto risco", "value": hr_f, "formatted": _fmt_num(hr_f)},
            {"label": "Mulheres fora de risco", "value": total_f - hr_f, "formatted": _fmt_num(total_f - hr_f)},
        ],
        "details": {
            "high_risk_feminino": _fmt_num(hr_f),
            "total_feminino": _fmt_num(total_f),
            "pct_high_risk_feminino": _fmt_pct(pct),
            "high_risk_masculino": _fmt_num(hr_m),
            "pct_high_risk_masculino": _fmt_pct(pct_m),
        },
    }


# ─── 299: women-vs-men-high-risk-ratio ───────────────────────────────────────

def _women_vs_men_high_risk_ratio(data, summary):
    dem = summary["demographics"]
    hr_f = dem["high_risk_feminino"]
    hr_m = dem["high_risk_masculino"]
    ratio = round(hr_f / hr_m * 100) if hr_m else 0
    pct_f = dem["pct_high_risk_feminino"]
    pct_m = dem["pct_high_risk_masculino"]
    return {
        "headline_stat": str(ratio),
        "headline_label": "mulheres em alto risco para cada 100 homens",
        "chart_data": [
            {"label": "Mulheres em alto risco", "value": hr_f, "formatted": _fmt_num(hr_f)},
            {"label": "Homens em alto risco", "value": hr_m, "formatted": _fmt_num(hr_m)},
        ],
        "details": {
            "ratio_per_100": str(ratio),
            "high_risk_feminino": _fmt_num(hr_f),
            "high_risk_masculino": _fmt_num(hr_m),
            "pct_high_risk_feminino": _fmt_pct(pct_f),
            "pct_high_risk_masculino": _fmt_pct(pct_m),
        },
    }


# ─── 300: women-top10-exposed-occupations ────────────────────────────────────

def _women_top10_exposed_occupations(data, summary):
    candidates = _with_demographics(data)
    candidates = [o for o in candidates if (o.get("exposicao") or 0) >= 8]
    for o in candidates:
        o["_total_f"] = o["demographics"].get("total_feminino") or 0
    candidates.sort(key=lambda o: o["_total_f"], reverse=True)
    top10 = candidates[:10]
    total_w = sum(o["_total_f"] for o in top10)
    rows = []
    for o in top10:
        pf = _pct_female(o)
        rows.append({
            "titulo": o.get("titulo", ""),
            "total_feminino": _fmt_num(o["_total_f"]),
            "pct_feminino": _fmt_pct(pf) if pf is not None else "N/D",
            "exposicao": str(o.get("exposicao", 0)).replace(".", ","),
        })
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "mulheres nas 10 ocupações mais expostas à IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["_total_f"], "formatted": _fmt_num(o["_total_f"])}
            for o in top10
        ],
        "details": {
            "total_women_top10": _fmt_num(total_w),
            "num_occupations_high_exposure": str(len(candidates)),
            "top_occupations": rows,
        },
    }


# ─── 301: women-safest-occupations ───────────────────────────────────────────

def _women_safest_occupations(data, summary):
    candidates = _with_demographics(data)
    candidates = [o for o in candidates if o.get("exposicao") is not None and o["exposicao"] <= 3]
    for o in candidates:
        o["_total_f"] = o["demographics"].get("total_feminino") or 0
    candidates.sort(key=lambda o: o["_total_f"], reverse=True)
    top10 = candidates[:10]
    total_w = sum(o["_total_f"] for o in top10)
    rows = []
    for o in top10:
        pf = _pct_female(o)
        rows.append({
            "titulo": o.get("titulo", ""),
            "total_feminino": _fmt_num(o["_total_f"]),
            "pct_feminino": _fmt_pct(pf) if pf is not None else "N/D",
            "exposicao": str(o.get("exposicao", 0)).replace(".", ","),
        })
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": "mulheres nas 10 ocupações mais seguras da IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["_total_f"], "formatted": _fmt_num(o["_total_f"])}
            for o in top10
        ],
        "details": {
            "total_women_top10": _fmt_num(total_w),
            "num_safe_occupations": str(len(candidates)),
            "top_occupations": rows,
        },
    }


# ─── 302: women-salary-gap-high-risk ─────────────────────────────────────────

def _women_salary_gap_high_risk(data, summary):
    candidates = _with_demographics(data)
    candidates = [o for o in candidates if (o.get("exposicao") or 0) >= 7 and o.get("salario")]
    fem_dom = [o for o in candidates if (_pct_female(o) or 0) > 60]
    mal_dom = [o for o in candidates if (_pct_female(o) or 100) < 40]
    avg_sal_f = round(_safe_avg([o["salario"] for o in fem_dom])) if fem_dom else 0
    avg_sal_m = round(_safe_avg([o["salario"] for o in mal_dom])) if mal_dom else 0
    gap = avg_sal_m - avg_sal_f
    gap_pct = (gap / avg_sal_m * 100) if avg_sal_m else 0
    return {
        "headline_stat": "R$ " + _fmt_num(abs(gap)),
        "headline_label": "diferença salarial em ocupações de alto risco por gênero",
        "chart_data": [
            {"label": "Ocupações feminizadas (>60% mulheres)", "value": avg_sal_f, "formatted": "R$ " + _fmt_num(avg_sal_f)},
            {"label": "Ocupações masculinizadas (>60% homens)", "value": avg_sal_m, "formatted": "R$ " + _fmt_num(avg_sal_m)},
        ],
        "details": {
            "avg_salary_fem_dominated": "R$ " + _fmt_num(avg_sal_f),
            "avg_salary_mal_dominated": "R$ " + _fmt_num(avg_sal_m),
            "gap_reais": "R$ " + _fmt_num(abs(gap)),
            "gap_pct": _fmt_pct(abs(gap_pct)),
            "num_fem_dominated": str(len(fem_dom)),
            "num_mal_dominated": str(len(mal_dom)),
        },
    }


# ─── 303: women-opportunity-gap ──────────────────────────────────────────────

def _women_opportunity_gap(data, summary):
    candidates = _with_demographics(data)
    candidates = [o for o in candidates if o.get("oportunidade") is not None]
    fem_dom = [o for o in candidates if (_pct_female(o) or 0) > 55]
    mal_dom = [o for o in candidates if (_pct_female(o) or 100) < 45]
    avg_op_f = round(_safe_avg([o["oportunidade"] for o in fem_dom]), 1) if fem_dom else 0
    avg_op_m = round(_safe_avg([o["oportunidade"] for o in mal_dom]), 1) if mal_dom else 0
    diff = round(avg_op_f - avg_op_m, 1)
    return {
        "headline_stat": str(avg_op_f).replace(".", ","),
        "headline_label": "oportunidade média em ocupações feminizadas vs " + str(avg_op_m).replace(".", ",") + " nas masculinizadas",
        "chart_data": [
            {"label": "Ocupações feminizadas (>55% mulheres)", "value": avg_op_f, "formatted": str(avg_op_f).replace(".", ",")},
            {"label": "Ocupações masculinizadas (>55% homens)", "value": avg_op_m, "formatted": str(avg_op_m).replace(".", ",")},
        ],
        "details": {
            "avg_oportunidade_fem": str(avg_op_f).replace(".", ","),
            "avg_oportunidade_mal": str(avg_op_m).replace(".", ","),
            "diff": str(diff).replace(".", ","),
            "num_fem_dominated": str(len(fem_dom)),
            "num_mal_dominated": str(len(mal_dom)),
        },
    }


# ─── 304: women-secretarias-risk ─────────────────────────────────────────────

def _women_secretarias_risk(data, summary):
    matches = _keyword_filter(data, ["secretári"])
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top5 = matches[:5]
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres entre secretári@s — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top5
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top5
            ],
        },
    }


# ─── 305: women-telemarketing-gender ─────────────────────────────────────────

def _women_telemarketing_gender(data, summary):
    matches = _keyword_filter(data, ["telemarketing"])
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres no telemarketing — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": "Mulheres", "value": total_f, "formatted": _fmt_num(total_f)},
            {"label": "Homens", "value": total_m, "formatted": _fmt_num(total_m)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
        },
    }


# ─── 306: women-professoras-profile ──────────────────────────────────────────

def _women_professoras_profile(data, summary):
    matches = _keyword_filter(data, ["professor"])
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_num(total_f),
        "headline_label": "professoras no ensino formal — " + _fmt_pct(pct_f) + " mulheres",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top8
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 307: women-enfermeiras-profile ──────────────────────────────────────────

def _women_enfermeiras_profile(data, summary):
    matches = _keyword_filter(data, ["enferme"])
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres na enfermagem — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": "Mulheres", "value": total_f, "formatted": _fmt_num(total_f)},
            {"label": "Homens", "value": total_m, "formatted": _fmt_num(total_m)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "num_occupations": str(len(matches)),
        },
    }


# ─── 308: women-caixas-profile ───────────────────────────────────────────────

def _women_caixas_profile(data, summary):
    matches = _keyword_filter(data, ["caixa"])
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    return {
        "headline_stat": _fmt_num(total_f),
        "headline_label": "mulheres operadoras de caixa — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": "Mulheres", "value": total_f, "formatted": _fmt_num(total_f)},
            {"label": "Homens", "value": total_m, "formatted": _fmt_num(total_m)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
        },
    }


# ─── 309: women-admin-crisis ─────────────────────────────────────────────────

def _women_admin_crisis(data, summary):
    matches = _gg_filter(data, "SERVIÇOS ADMINISTRATIVOS")
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres nos serviços administrativos — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 310: women-services-commerce ────────────────────────────────────────────

def _women_services_commerce(data, summary):
    matches = _gg_filter(data, "VENDEDORES DO COMÉRCIO")
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_num(total_f),
        "headline_label": "mulheres em serviços e comércio — " + _fmt_pct(pct_f) + " do total",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top8
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 311: women-production-underrepresented ──────────────────────────────────

def _women_production_underrepresented(data, summary):
    matches = _gg_filter(data, "PRODUÇÃO")
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres na produção industrial — exposição média " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": "Mulheres", "value": total_f, "formatted": _fmt_num(total_f)},
            {"label": "Homens", "value": total_m, "formatted": _fmt_num(total_m)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
        },
    }


# ─── 312: women-leadership-exposure ──────────────────────────────────────────

def _women_leadership_exposure(data, summary):
    matches = _gg_filter(data, "MEMBROS SUPERIORES")
    if not matches:
        matches = _gg_filter(data, "DIRIGENTES")
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres em cargos de liderança — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 313: women-tech-representation ──────────────────────────────────────────

def _women_tech_representation(data, summary):
    keywords = ["programa", "desenvolvedor", "sistemas", "software", "dados", "tecnologia"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_oport = round(_safe_avg([o.get("oportunidade") for o in matches if o.get("oportunidade") is not None]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres em tecnologia — oportunidade média " + str(avg_oport).replace(".", ","),
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("oportunidade") or 0, "formatted": str(o.get("oportunidade", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_oportunidade": str(avg_oport).replace(".", ","),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "oportunidade": str(o.get("oportunidade", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 314: women-high-salary-access ───────────────────────────────────────────

def _women_high_salary_access(data, summary):
    candidates = _with_demographics(data)
    high_sal = [o for o in candidates if (o.get("salario") or 0) >= 8000]
    low_sal = [o for o in candidates if o.get("salario") and o["salario"] < 2000]
    pcts_high = [_pct_female(o) for o in high_sal if _pct_female(o) is not None]
    pcts_low = [_pct_female(o) for o in low_sal if _pct_female(o) is not None]
    avg_pct_high = round(_safe_avg(pcts_high), 1) if pcts_high else 0
    avg_pct_low = round(_safe_avg(pcts_low), 1) if pcts_low else 0
    return {
        "headline_stat": _fmt_pct(avg_pct_high),
        "headline_label": "de mulheres em ocupações com salário acima de R$ 8.000",
        "chart_data": [
            {"label": "Salário >= R$ 8.000", "value": avg_pct_high, "formatted": _fmt_pct(avg_pct_high)},
            {"label": "Salário < R$ 2.000", "value": avg_pct_low, "formatted": _fmt_pct(avg_pct_low)},
        ],
        "details": {
            "avg_pct_fem_high_salary": _fmt_pct(avg_pct_high),
            "avg_pct_fem_low_salary": _fmt_pct(avg_pct_low),
            "num_high_salary_occs": str(len(high_sal)),
            "num_low_salary_occs": str(len(low_sal)),
            "diff_pp": _fmt_pct(abs(avg_pct_high - avg_pct_low)),
        },
    }


# ─── 315: women-entry-salary-penalty ─────────────────────────────────────────

def _women_entry_salary_penalty(data, summary):
    candidates = _with_demographics(data)
    candidates = [o for o in candidates if o.get("salario_admissao")]
    fem_dom = [o for o in candidates if (_pct_female(o) or 0) > 60]
    mal_dom = [o for o in candidates if (_pct_female(o) or 100) < 40]
    avg_adm_f = round(_safe_avg([o["salario_admissao"] for o in fem_dom])) if fem_dom else 0
    avg_adm_m = round(_safe_avg([o["salario_admissao"] for o in mal_dom])) if mal_dom else 0
    gap = avg_adm_m - avg_adm_f
    gap_pct = (gap / avg_adm_m * 100) if avg_adm_m else 0
    return {
        "headline_stat": "R$ " + _fmt_num(abs(gap)),
        "headline_label": "diferença no salário de admissão entre ocupações feminizadas e masculinizadas",
        "chart_data": [
            {"label": "Ocupações feminizadas (>60% mulheres)", "value": avg_adm_f, "formatted": "R$ " + _fmt_num(avg_adm_f)},
            {"label": "Ocupações masculinizadas (>60% homens)", "value": avg_adm_m, "formatted": "R$ " + _fmt_num(avg_adm_m)},
        ],
        "details": {
            "avg_admissao_fem": "R$ " + _fmt_num(avg_adm_f),
            "avg_admissao_mal": "R$ " + _fmt_num(avg_adm_m),
            "gap_reais": "R$ " + _fmt_num(abs(gap)),
            "gap_pct": _fmt_pct(abs(gap_pct)),
            "num_fem_dominated": str(len(fem_dom)),
            "num_mal_dominated": str(len(mal_dom)),
        },
    }


# ─── 316: women-growing-declining-jobs ───────────────────────────────────────

def _women_growing_declining_jobs(data, summary):
    candidates = _with_demographics(data)
    candidates = [o for o in candidates if o.get("saldo") is not None]
    growing = [o for o in candidates if o["saldo"] > 0]
    declining = [o for o in candidates if o["saldo"] < 0]
    pcts_grow = [_pct_female(o) for o in growing if _pct_female(o) is not None]
    pcts_decl = [_pct_female(o) for o in declining if _pct_female(o) is not None]
    avg_grow = round(_safe_avg(pcts_grow), 1) if pcts_grow else 0
    avg_decl = round(_safe_avg(pcts_decl), 1) if pcts_decl else 0
    total_f_grow = sum(o["demographics"].get("total_feminino") or 0 for o in growing)
    total_f_decl = sum(o["demographics"].get("total_feminino") or 0 for o in declining)
    return {
        "headline_stat": _fmt_pct(avg_grow),
        "headline_label": "de mulheres em ocupações em crescimento vs " + _fmt_pct(avg_decl) + " nas em declínio",
        "chart_data": [
            {"label": "Ocupações em crescimento (saldo > 0)", "value": avg_grow, "formatted": _fmt_pct(avg_grow)},
            {"label": "Ocupações em declínio (saldo < 0)", "value": avg_decl, "formatted": _fmt_pct(avg_decl)},
        ],
        "details": {
            "avg_pct_fem_growing": _fmt_pct(avg_grow),
            "avg_pct_fem_declining": _fmt_pct(avg_decl),
            "total_fem_growing": _fmt_num(total_f_grow),
            "total_fem_declining": _fmt_num(total_f_decl),
            "num_growing": str(len(growing)),
            "num_declining": str(len(declining)),
        },
    }


# ─── 317: women-education-paradox ────────────────────────────────────────────

def _women_education_paradox(data, summary):
    candidates = _with_demographics(data)
    superior = [o for o in candidates if o.get("escolaridade") and "superior completo" in o["escolaridade"].lower()]
    pcts = [_pct_female(o) for o in superior if _pct_female(o) is not None]
    avg_pct_f = round(_safe_avg(pcts), 1) if pcts else 0
    exps = [o["exposicao"] for o in superior if o.get("exposicao") is not None]
    avg_exp = round(_safe_avg(exps), 1) if exps else 0
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in superior)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in superior)
    return {
        "headline_stat": _fmt_pct(avg_pct_f),
        "headline_label": "de mulheres em ocupações de nível superior — exposição média " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": "Mulheres (superior completo)", "value": total_f, "formatted": _fmt_num(total_f)},
            {"label": "Homens (superior completo)", "value": total_m, "formatted": _fmt_num(total_m)},
        ],
        "details": {
            "avg_pct_feminino": _fmt_pct(avg_pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(superior)),
        },
    }


# ─── 318: women-automation-vulnerability ─────────────────────────────────────

def _women_automation_vulnerability(data, summary):
    candidates = _with_demographics(data)
    vuln = [o for o in candidates if (o.get("exposicao") or 0) >= 8 and (o.get("vantagem") or 10) <= 4]
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in vuln)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in vuln)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    vuln.sort(key=lambda o: (o["demographics"].get("total_feminino") or 0), reverse=True)
    top8 = vuln[:8]
    rows = []
    for o in top8:
        rows.append({
            "titulo": o.get("titulo", ""),
            "total_feminino": _fmt_num(o["demographics"].get("total_feminino") or 0),
            "exposicao": str(o.get("exposicao", 0)).replace(".", ","),
            "vantagem": str(o.get("vantagem", 0)).replace(".", ","),
        })
    return {
        "headline_stat": _fmt_num(total_f),
        "headline_label": "mulheres em ocupações altamente automatizáveis",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["demographics"].get("total_feminino") or 0,
             "formatted": _fmt_num(o["demographics"].get("total_feminino") or 0)}
            for o in top8
        ],
        "details": {
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "pct_feminino": _fmt_pct(pct_f),
            "num_occupations": str(len(vuln)),
            "top_occupations": rows,
        },
    }


# ─── 319: women-ai-augmentation ──────────────────────────────────────────────

def _women_ai_augmentation(data, summary):
    candidates = _with_demographics(data)
    aug = [o for o in candidates if (o.get("vantagem") or 0) >= 7 and (o.get("exposicao") or 0) >= 6]
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in aug)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in aug)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    aug.sort(key=lambda o: (o["demographics"].get("total_feminino") or 0), reverse=True)
    top8 = aug[:8]
    return {
        "headline_stat": _fmt_num(total_f),
        "headline_label": "mulheres em ocupações com alto potencial de aumentação por IA",
        "chart_data": [
            {"label": "Mulheres", "value": total_f, "formatted": _fmt_num(total_f)},
            {"label": "Homens", "value": total_m, "formatted": _fmt_num(total_m)},
        ],
        "details": {
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "pct_feminino": _fmt_pct(pct_f),
            "num_occupations": str(len(aug)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "total_feminino": _fmt_num(o["demographics"].get("total_feminino") or 0),
                 "vantagem": str(o.get("vantagem", 0)).replace(".", ","), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 320: women-by-exposure-tier ─────────────────────────────────────────────

def _women_by_exposure_tier(data, summary):
    candidates = _with_demographics(data)
    candidates = [o for o in candidates if o.get("exposicao") is not None]
    tiers = {"Baixa (0-3)": [], "Média (4-6)": [], "Alta (7-10)": []}
    for o in candidates:
        exp = o["exposicao"]
        if exp <= 3:
            tiers["Baixa (0-3)"].append(o)
        elif exp <= 6:
            tiers["Média (4-6)"].append(o)
        else:
            tiers["Alta (7-10)"].append(o)
    chart = []
    details_tiers = []
    for tier_name in ["Baixa (0-3)", "Média (4-6)", "Alta (7-10)"]:
        occs = tiers[tier_name]
        tf = sum(o["demographics"].get("total_feminino") or 0 for o in occs)
        tm = sum(o["demographics"].get("total_masculino") or 0 for o in occs)
        pct = (tf / (tf + tm) * 100) if (tf + tm) else 0
        chart.append({"label": tier_name, "value": round(pct, 1), "formatted": _fmt_pct(pct)})
        details_tiers.append({
            "tier": tier_name, "total_feminino": _fmt_num(tf),
            "total_masculino": _fmt_num(tm), "pct_feminino": _fmt_pct(pct),
            "num_occupations": str(len(occs)),
        })
    return {
        "headline_stat": chart[2]["formatted"] if len(chart) > 2 else "0%",
        "headline_label": "de mulheres na faixa de alta exposição à IA",
        "chart_data": chart,
        "details": {
            "tiers": details_tiers,
        },
    }


# ─── 321: women-care-economy-safety ──────────────────────────────────────────

def _women_care_economy_safety(data, summary):
    keywords = ["cuidador", "doméstic", "babá", "enferme", "assistência social"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres na economia do cuidado — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 322: women-creative-sector ──────────────────────────────────────────────

def _women_creative_sector(data, summary):
    keywords = ["design", "jornalist", "publicit", "fotógraf"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres no setor criativo — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 323: women-financial-sector ─────────────────────────────────────────────

def _women_financial_sector(data, summary):
    keywords = ["contab", "financ", "banc", "audit"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres no setor financeiro — exposição " + str(avg_exp).replace(".", ","),
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "num_occupations": str(len(matches)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 324: women-health-sector-gender ─────────────────────────────────────────

def _women_health_sector_gender(data, summary):
    keywords = ["médic", "enferme", "farmac", "fisioterapeut", "nutricion", "dentist", "saúde", "hospitalar"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    dem_matches = _with_demographics(matches)
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in dem_matches)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in dem_matches)
    pct_f = (total_f / (total_f + total_m) * 100) if (total_f + total_m) else 0
    top10 = matches[:10]
    rows = []
    for o in top10:
        pf = _pct_female(o)
        rows.append({
            "titulo": o.get("titulo", ""),
            "workers": _fmt_num(o.get("empregados") or 0),
            "pct_feminino": _fmt_pct(pf) if pf is not None else "N/D",
            "exposicao": str(o.get("exposicao", 0)).replace(".", ","),
        })
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres no setor de saúde — " + _fmt_num(total_f) + " trabalhadoras",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "num_occupations": str(len(matches)),
            "top_occupations": rows,
        },
    }


# ─── 325: women-double-burden ────────────────────────────────────────────────

def _women_double_burden(data, summary):
    candidates = _with_demographics(data)
    triple = [o for o in candidates
              if (_pct_female(o) or 0) > 70
              and (o.get("exposicao") or 0) >= 7
              and o.get("salario") is not None and o["salario"] < 2500]
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in triple)
    total_m = sum(o["demographics"].get("total_masculino") or 0 for o in triple)
    triple.sort(key=lambda o: (o["demographics"].get("total_feminino") or 0), reverse=True)
    top8 = triple[:8]
    rows = []
    for o in top8:
        rows.append({
            "titulo": o.get("titulo", ""),
            "total_feminino": _fmt_num(o["demographics"].get("total_feminino") or 0),
            "pct_feminino": _fmt_pct(_pct_female(o) or 0),
            "exposicao": str(o.get("exposicao", 0)).replace(".", ","),
            "salario": "R$ " + _fmt_num(round(o.get("salario") or 0)),
        })
    return {
        "headline_stat": str(len(triple)),
        "headline_label": "ocupações com tripla vulnerabilidade: feminizadas, expostas e mal pagas",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["demographics"].get("total_feminino") or 0,
             "formatted": _fmt_num(o["demographics"].get("total_feminino") or 0)}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(triple)),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "top_occupations": rows,
        },
    }


# ─── 326: women-bright-spots ─────────────────────────────────────────────────

def _women_bright_spots(data, summary):
    candidates = _with_demographics(data)
    bright = [o for o in candidates
              if (_pct_female(o) or 0) > 55
              and (o.get("oportunidade") or 0) >= 7]
    total_f = sum(o["demographics"].get("total_feminino") or 0 for o in bright)
    bright.sort(key=lambda o: (o.get("oportunidade") or 0), reverse=True)
    top10 = bright[:10]
    rows = []
    for o in top10:
        rows.append({
            "titulo": o.get("titulo", ""),
            "total_feminino": _fmt_num(o["demographics"].get("total_feminino") or 0),
            "pct_feminino": _fmt_pct(_pct_female(o) or 0),
            "oportunidade": str(o.get("oportunidade", 0)).replace(".", ","),
        })
    return {
        "headline_stat": str(len(bright)),
        "headline_label": "ocupações feminizadas com alta oportunidade de IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("oportunidade") or 0,
             "formatted": str(o.get("oportunidade", 0)).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "num_occupations": str(len(bright)),
            "total_feminino": _fmt_num(total_f),
            "top_occupations": rows,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template list
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES_BATCH_WOMEN = [
    # 297
    {
        "id": "women-total-workforce",
        "category": "Demografia",
        "tags": ["mulheres", "gênero", "força de trabalho"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_total_workforce,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a participação das mulheres na força de trabalho formal brasileira e o que isso significa diante da revolução da IA.

DADOS (use APENAS estes números, não invente dados):
- Total de mulheres: {total_feminino}
- Total de homens: {total_masculino}
- Total geral: {total_geral}
- Percentual feminino: {pct_feminino}
- Percentual masculino: {pct_masculino}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 298
    {
        "id": "women-high-risk-total",
        "category": "Demografia",
        "tags": ["mulheres", "alto risco", "exposição"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_high_risk_total,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre quantas mulheres estão em ocupações de alto risco de disrupção pela IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Mulheres em alto risco: {high_risk_feminino}
- Total de mulheres: {total_feminino}
- Percentual de mulheres em alto risco: {pct_high_risk_feminino}
- Homens em alto risco: {high_risk_masculino}
- Percentual de homens em alto risco: {pct_high_risk_masculino}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 299
    {
        "id": "women-vs-men-high-risk-ratio",
        "category": "Demografia",
        "tags": ["mulheres", "homens", "razão", "alto risco"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_vs_men_high_risk_ratio,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a proporção de mulheres vs homens em ocupações de alto risco de IA. Para cada 100 homens em risco, quantas mulheres estão na mesma situação?

DADOS (use APENAS estes números, não invente dados):
- Para cada 100 homens em alto risco, há {ratio_per_100} mulheres
- Mulheres em alto risco: {high_risk_feminino}
- Homens em alto risco: {high_risk_masculino}
- Pct mulheres em alto risco: {pct_high_risk_feminino}
- Pct homens em alto risco: {pct_high_risk_masculino}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 300
    {
        "id": "women-top10-exposed-occupations",
        "category": "Ocupações",
        "tags": ["mulheres", "exposição alta", "ranking"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_top10_exposed_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações de alta exposição à IA (>=8) onde mais mulheres trabalham. Quais são e o que isso revela?

DADOS (use APENAS estes números, não invente dados):
- Total de mulheres nas 10 ocupações mais expostas: {total_women_top10}
- Número de ocupações com exposição >= 8: {num_occupations_high_exposure}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 301
    {
        "id": "women-safest-occupations",
        "category": "Ocupações",
        "tags": ["mulheres", "baixa exposição", "segurança"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_safest_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações mais seguras da IA (exposição <=3) onde mais mulheres trabalham. Onde as mulheres estão protegidas?

DADOS (use APENAS estes números, não invente dados):
- Total de mulheres nas 10 ocupações mais seguras: {total_women_top10}
- Número de ocupações com baixa exposição: {num_safe_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 302
    {
        "id": "women-salary-gap-high-risk",
        "category": "Mercado",
        "tags": ["mulheres", "salário", "gap", "alto risco"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_salary_gap_high_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença salarial entre ocupações feminizadas e masculinizadas em alto risco de IA. As mulheres ganham menos mesmo quando enfrentam o mesmo risco?

DADOS (use APENAS estes números, não invente dados):
- Salário médio em ocupações feminizadas (>60%% mulheres): {avg_salary_fem_dominated}
- Salário médio em ocupações masculinizadas (>60%% homens): {avg_salary_mal_dominated}
- Diferença salarial: {gap_reais} ({gap_pct})
- Número de ocupações feminizadas em alto risco: {num_fem_dominated}
- Número de ocupações masculinizadas em alto risco: {num_mal_dominated}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 303
    {
        "id": "women-opportunity-gap",
        "category": "Mercado",
        "tags": ["mulheres", "oportunidade", "gap"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_opportunity_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença de oportunidade de IA entre ocupações feminizadas e masculinizadas. As mulheres têm oportunidade igual de se beneficiar da IA?

DADOS (use APENAS estes números, não invente dados):
- Oportunidade média em ocupações feminizadas (>55%% mulheres): {avg_oportunidade_fem}
- Oportunidade média em ocupações masculinizadas (>55%% homens): {avg_oportunidade_mal}
- Diferença: {diff}
- Número de ocupações feminizadas: {num_fem_dominated}
- Número de ocupações masculinizadas: {num_mal_dominated}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 304
    {
        "id": "women-secretarias-risk",
        "category": "Ocupações",
        "tags": ["mulheres", "secretárias", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_secretarias_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as secretárias no Brasil — uma profissão clássica feminina em alto risco de automação pela IA.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 305
    {
        "id": "women-telemarketing-gender",
        "category": "Ocupações",
        "tags": ["mulheres", "telemarketing", "exposição"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_telemarketing_gender,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o telemarketing — uma das profissões mais expostas à IA e altamente feminizada no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 306
    {
        "id": "women-professoras-profile",
        "category": "Ocupações",
        "tags": ["mulheres", "professoras", "educação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_professoras_profile,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as professoras no Brasil — o ensino é majoritariamente feminino. Qual o impacto da IA nessas profissionais?

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres professoras: {total_feminino}
- Total de trabalhadores no ensino: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 307
    {
        "id": "women-enfermeiras-profile",
        "category": "Ocupações",
        "tags": ["mulheres", "enfermagem", "saúde"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_enfermeiras_profile,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a enfermagem no Brasil — profissão feminizada. Qual a exposição à IA e o salário dessas trabalhadoras?

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Número de ocupações: {num_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 308
    {
        "id": "women-caixas-profile",
        "category": "Ocupações",
        "tags": ["mulheres", "caixas", "varejo"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_caixas_profile,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as operadoras de caixa no Brasil — mulheres na linha de frente do varejo e da automação.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 309
    {
        "id": "women-admin-crisis",
        "category": "Setores",
        "tags": ["mulheres", "administrativo", "automação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_admin_crisis,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as mulheres nos serviços administrativos — o grande grupo com maior exposição à IA. As mulheres carregam o peso da automação administrativa.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 310
    {
        "id": "women-services-commerce",
        "category": "Setores",
        "tags": ["mulheres", "serviços", "comércio"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_services_commerce,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as mulheres em serviços e comércio — um dos maiores empregadores femininos no Brasil. Qual o impacto da IA?

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 311
    {
        "id": "women-production-underrepresented",
        "category": "Setores",
        "tags": ["mulheres", "produção", "industrial"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_production_underrepresented,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a sub-representação das mulheres na produção industrial — empregos que tendem a ter baixa exposição à IA. A segregação ocupacional protege os homens?

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres na produção: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de homens: {total_masculino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 312
    {
        "id": "women-leadership-exposure",
        "category": "Ocupações",
        "tags": ["mulheres", "liderança", "teto de vidro"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_leadership_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as mulheres em cargos de liderança e alta gestão — o teto de vidro encontra a inteligência artificial.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres em liderança: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 313
    {
        "id": "women-tech-representation",
        "category": "Setores",
        "tags": ["mulheres", "tecnologia", "oportunidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_tech_representation,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a representação feminina em ocupações de tecnologia — as profissões de alta oportunidade com IA são dominadas por homens.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres em tech: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Oportunidade média: {avg_oportunidade} (escala 0-10)
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 314
    {
        "id": "women-high-salary-access",
        "category": "Mercado",
        "tags": ["mulheres", "salário alto", "acesso"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_high_salary_access,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o acesso das mulheres a ocupações de alto salário vs baixo salário. A desigualdade de gênero se aprofunda no topo?

DADOS (use APENAS estes números, não invente dados):
- Média de %% feminino em ocupações com salário >= R$ 8.000: {avg_pct_fem_high_salary}
- Média de %% feminino em ocupações com salário < R$ 2.000: {avg_pct_fem_low_salary}
- Número de ocupações com salário alto: {num_high_salary_occs}
- Número de ocupações com salário baixo: {num_low_salary_occs}
- Diferença em pontos percentuais: {diff_pp}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 315
    {
        "id": "women-entry-salary-penalty",
        "category": "Mercado",
        "tags": ["mulheres", "salário admissão", "penalidade"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_entry_salary_penalty,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença no salário de admissão entre ocupações feminizadas e masculinizadas. As mulheres já começam ganhando menos.

DADOS (use APENAS estes números, não invente dados):
- Salário de admissão médio em ocupações feminizadas (>60%% mulheres): {avg_admissao_fem}
- Salário de admissão médio em ocupações masculinizadas (>60%% homens): {avg_admissao_mal}
- Diferença: {gap_reais} ({gap_pct})
- Número de ocupações feminizadas: {num_fem_dominated}
- Número de ocupações masculinizadas: {num_mal_dominated}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 316
    {
        "id": "women-growing-declining-jobs",
        "category": "Mercado",
        "tags": ["mulheres", "crescimento", "declínio"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_growing_declining_jobs,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre se os empregos das mulheres estão crescendo ou encolhendo. Compare a presença feminina em ocupações com saldo positivo vs negativo.

DADOS (use APENAS estes números, não invente dados):
- Média de %% feminino em ocupações em crescimento: {avg_pct_fem_growing}
- Média de %% feminino em ocupações em declínio: {avg_pct_fem_declining}
- Total de mulheres em ocupações crescentes: {total_fem_growing}
- Total de mulheres em ocupações em declínio: {total_fem_declining}
- Número de ocupações crescentes: {num_growing}
- Número de ocupações em declínio: {num_declining}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 317
    {
        "id": "women-education-paradox",
        "category": "Educação",
        "tags": ["mulheres", "educação", "superior", "paradoxo"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_education_paradox,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o paradoxo educacional: mulheres com ensino superior enfrentam maior exposição à IA. Mais educação = mais risco?

DADOS (use APENAS estes números, não invente dados):
- Média de %% feminino em ocupações de nível superior: {avg_pct_feminino}
- Total de mulheres (superior completo): {total_feminino}
- Total de homens (superior completo): {total_masculino}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 318
    {
        "id": "women-automation-vulnerability",
        "category": "Mercado",
        "tags": ["mulheres", "automação", "vulnerabilidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_automation_vulnerability,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as mulheres mais vulneráveis à automação — ocupações com alta exposição (>=8) e baixa vantagem (<=4). Empregos com maior probabilidade de desaparecer.

DADOS (use APENAS estes números, não invente dados):
- Total de mulheres em ocupações automatizáveis: {total_feminino}
- Total de homens: {total_masculino}
- Percentual feminino: {pct_feminino}
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 319
    {
        "id": "women-ai-augmentation",
        "category": "Mercado",
        "tags": ["mulheres", "aumentação", "vantagem"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_ai_augmentation,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a capacidade das mulheres de usar a IA como ferramenta de aumentação — ocupações com alta vantagem (>=7) e exposição (>=6). As mulheres conseguem aproveitar a IA igualmente?

DADOS (use APENAS estes números, não invente dados):
- Total de mulheres em ocupações de aumentação: {total_feminino}
- Total de homens: {total_masculino}
- Percentual feminino: {pct_feminino}
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 320
    {
        "id": "women-by-exposure-tier",
        "category": "Demografia",
        "tags": ["mulheres", "faixas de exposição", "distribuição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_by_exposure_tier,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a composição de gênero muda conforme o nível de exposição à IA. As mulheres estão mais concentradas nas faixas de risco?

DADOS (use APENAS estes números, não invente dados):
- Distribuição por faixa de exposição: {tiers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 321
    {
        "id": "women-care-economy-safety",
        "category": "Setores",
        "tags": ["mulheres", "economia do cuidado", "proteção"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_care_economy_safety,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a economia do cuidado como refúgio feminino da IA — cuidadoras, domésticas, enfermeiras, assistentes sociais.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 322
    {
        "id": "women-creative-sector",
        "category": "Setores",
        "tags": ["mulheres", "setor criativo", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_creative_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as mulheres no setor criativo — design, jornalismo, publicidade, fotografia — e a disrupção da IA generativa.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 323
    {
        "id": "women-financial-sector",
        "category": "Setores",
        "tags": ["mulheres", "financeiro", "contabilidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_financial_sector,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as mulheres no setor financeiro — contabilidade, bancos, auditoria — e a exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Número de ocupações: {num_occupations}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 324
    {
        "id": "women-health-sector-gender",
        "category": "Setores",
        "tags": ["mulheres", "saúde", "gênero"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _women_health_sector_gender,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as mulheres no setor de saúde — maioria na enfermagem, minoria na medicina. Como a IA impacta cada segmento?

DADOS (use APENAS estes números, não invente dados):
- Percentual de mulheres no setor: {pct_feminino}
- Total de mulheres: {total_feminino}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Número de ocupações: {num_occupations}
- Top ocupações com %% feminino: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 325
    {
        "id": "women-double-burden",
        "category": "Demografia",
        "tags": ["mulheres", "tripla vulnerabilidade", "desigualdade"],
        "chart_type": "ranking_table",
        "analysis_fn": _women_double_burden,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a tripla vulnerabilidade: ocupações que são simultaneamente feminizadas (>70%% mulheres), altamente expostas à IA (>=7) e mal pagas (<R$ 2.500). A tempestade perfeita para as trabalhadoras brasileiras.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações com tripla vulnerabilidade: {num_occupations}
- Total de mulheres afetadas: {total_feminino}
- Total de homens: {total_masculino}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 326
    {
        "id": "women-bright-spots",
        "category": "Ocupações",
        "tags": ["mulheres", "oportunidade", "pontos positivos"],
        "chart_type": "ranking_table",
        "analysis_fn": _women_bright_spots,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os pontos positivos: ocupações feminizadas (>55%% mulheres) com alta oportunidade de IA (>=7). Onde a IA pode beneficiar as mulheres?

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações com alta oportunidade feminina: {num_occupations}
- Total de mulheres nessas ocupações: {total_feminino}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates_batch_women():
    return TEMPLATES_BATCH_WOMEN
