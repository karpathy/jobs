"""Insight templates batch B1: cross-regional + advanced demographic."""
import statistics
from insight_templates import _fmt_pct, _fmt_num, _safe_avg


# ═══════════════════════════════════════════════════════════════════════════════
# Region / UF groupings
# ═══════════════════════════════════════════════════════════════════════════════

_COASTAL_UFS = {"Maranhão", "Piauí", "Ceará", "Rio Grande do Norte", "Paraíba",
                "Pernambuco", "Alagoas", "Sergipe", "Bahia", "Pará", "Amapá",
                "Espírito Santo", "Rio de Janeiro", "São Paulo", "Paraná",
                "Santa Catarina", "Rio Grande do Sul"}
_INTERIOR_UFS = {"Amazonas", "Rondônia", "Acre", "Roraima", "Tocantins",
                 "Mato Grosso", "Mato Grosso do Sul", "Goiás", "Minas Gerais",
                 "Distrito Federal"}

_BORDER_CODES = {"43", "42", "41", "50", "51", "11", "12", "13", "14", "15", "16"}

_REGIONS = {
    "Norte": {"11", "12", "13", "14", "15", "16", "17"},
    "Nordeste": {"21", "22", "23", "24", "25", "26", "27", "28", "29"},
    "Sudeste": {"31", "32", "33", "35"},
    "Sul": {"41", "42", "43"},
    "Centro-Oeste": {"50", "51", "52", "53"},
}


def _uf_group_stats(por_uf, codes):
    """Compute weighted avg exposure, avg salary, total workers for a set of UF codes."""
    total_w = 0
    sum_exp_w = 0
    sum_sal_w = 0
    for code, info in por_uf.items():
        if code in codes:
            w = info.get("total_workers", 0)
            total_w += w
            sum_exp_w += info.get("avg_exposicao", 0) * w
            sum_sal_w += info.get("avg_salary", 0) * w
    avg_exp = round(sum_exp_w / total_w, 1) if total_w else 0
    avg_sal = round(sum_sal_w / total_w) if total_w else 0
    return total_w, avg_exp, avg_sal


def _uf_group_stats_by_name(por_uf, names):
    """Like _uf_group_stats but matches on info['nome']."""
    total_w = 0
    sum_exp_w = 0
    sum_sal_w = 0
    for code, info in por_uf.items():
        if info.get("nome") in names:
            w = info.get("total_workers", 0)
            total_w += w
            sum_exp_w += info.get("avg_exposicao", 0) * w
            sum_sal_w += info.get("avg_salary", 0) * w
    avg_exp = round(sum_exp_w / total_w, 1) if total_w else 0
    avg_sal = round(sum_sal_w / total_w) if total_w else 0
    return total_w, avg_exp, avg_sal


def _pct_female(occs):
    """Compute % female across occupations with demographics."""
    total_f = sum(o["demographics"].get("total_feminino", 0) for o in occs if o.get("demographics"))
    total_m = sum(o["demographics"].get("total_masculino", 0) for o in occs if o.get("demographics"))
    total = total_f + total_m
    return round(total_f / total * 100, 1) if total else 0, total_f, total_m


def _keyword_filter(data, keywords):
    """Return occupations whose titulo contains any keyword (case-insensitive)."""
    results = []
    for o in data:
        titulo = o.get("titulo", "").lower()
        if any(kw in titulo for kw in keywords):
            results.append(o)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Template 147: capital-exposure
# ═══════════════════════════════════════════════════════════════════════════════

def _capital_exposure(data, summary):
    por_uf = summary["por_uf"]
    df = por_uf.get("53", {})
    df_exp = df.get("avg_exposicao", 0)
    df_sal = df.get("avg_salary", 0)
    df_workers = df.get("total_workers", 0)
    all_exps = [info["avg_exposicao"] for info in por_uf.values() if "avg_exposicao" in info]
    national_avg = round(_safe_avg(all_exps), 1) if all_exps else 0
    diff = round(df_exp - national_avg, 1)
    return {
        "headline_stat": str(df_exp).replace(".", ","),
        "headline_label": "exposição média no Distrito Federal — capital federal lidera",
        "chart_data": [
            {"label": "Distrito Federal", "value": df_exp, "formatted": str(df_exp).replace(".", ",")},
            {"label": "Média nacional", "value": national_avg, "formatted": str(national_avg).replace(".", ",")},
        ],
        "details": {
            "df_exposicao": str(df_exp).replace(".", ","),
            "df_salary": "R$ " + _fmt_num(round(df_sal)),
            "df_workers": _fmt_num(df_workers),
            "national_avg": str(national_avg).replace(".", ","),
            "diff": str(diff).replace(".", ","),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 148: state-salary-gap
# ═══════════════════════════════════════════════════════════════════════════════

def _state_salary_gap(data, summary):
    por_uf = summary["por_uf"]
    states = [{"uf": info["nome"], "avg_salary": info["avg_salary"], "code": code}
              for code, info in por_uf.items() if info.get("avg_salary")]
    states.sort(key=lambda s: s["avg_salary"], reverse=True)
    top = states[0] if states else {"uf": "N/D", "avg_salary": 0}
    bottom = states[-1] if states else {"uf": "N/D", "avg_salary": 0}
    gap = round(top["avg_salary"] - bottom["avg_salary"])
    ratio = round(top["avg_salary"] / bottom["avg_salary"], 1) if bottom["avg_salary"] else 0
    return {
        "headline_stat": "R$ " + _fmt_num(gap),
        "headline_label": f"diferença salarial entre {top['uf']} e {bottom['uf']}",
        "chart_data": [
            {"label": s["uf"], "value": round(s["avg_salary"]),
             "formatted": "R$ " + _fmt_num(round(s["avg_salary"]))}
            for s in states[:10]
        ],
        "details": {
            "top_state": top["uf"],
            "top_salary": "R$ " + _fmt_num(round(top["avg_salary"])),
            "bottom_state": bottom["uf"],
            "bottom_salary": "R$ " + _fmt_num(round(bottom["avg_salary"])),
            "gap": "R$ " + _fmt_num(gap),
            "ratio": str(ratio).replace(".", ","),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 149: state-most-concentrated
# ═══════════════════════════════════════════════════════════════════════════════

def _state_most_concentrated(data, summary):
    por_uf = summary["por_uf"]
    results = []
    for code, info in por_uf.items():
        total = info.get("total_workers", 0)
        top_occs = info.get("top_occupations", [])
        if total and top_occs:
            top_occ = top_occs[0]
            pct = round(top_occ["workers"] / total * 100, 1)
            results.append({"uf": info["nome"], "top_occ": top_occ["titulo"],
                            "top_workers": top_occ["workers"], "total": total, "pct": pct})
    results.sort(key=lambda r: r["pct"], reverse=True)
    leader = results[0] if results else {"uf": "N/D", "pct": 0, "top_occ": "N/D"}
    return {
        "headline_stat": _fmt_pct(leader["pct"]),
        "headline_label": f"dos trabalhadores de {leader['uf']} em uma única ocupação",
        "chart_data": [
            {"label": r["uf"], "value": r["pct"], "formatted": _fmt_pct(r["pct"]),
             "detail": r["top_occ"]}
            for r in results[:10]
        ],
        "details": {
            "top_state": leader["uf"],
            "top_pct": _fmt_pct(leader["pct"]),
            "top_occupation": leader["top_occ"],
            "ranking": [{"uf": r["uf"], "pct": _fmt_pct(r["pct"]),
                          "occupation": r["top_occ"]} for r in results[:10]],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 150: coastal-vs-interior
# ═══════════════════════════════════════════════════════════════════════════════

def _coastal_vs_interior(data, summary):
    por_uf = summary["por_uf"]
    cw, ce, cs = _uf_group_stats_by_name(por_uf, _COASTAL_UFS)
    iw, ie, is_ = _uf_group_stats_by_name(por_uf, _INTERIOR_UFS)
    return {
        "headline_stat": str(ce).replace(".", ","),
        "headline_label": f"exposição média no litoral vs {str(ie).replace('.', ',')} no interior",
        "chart_data": [
            {"label": "Litoral", "value": ce, "formatted": str(ce).replace(".", ","),
             "detail": _fmt_num(cw) + " trabalhadores"},
            {"label": "Interior", "value": ie, "formatted": str(ie).replace(".", ","),
             "detail": _fmt_num(iw) + " trabalhadores"},
        ],
        "details": {
            "coastal_workers": _fmt_num(cw),
            "coastal_exposure": str(ce).replace(".", ","),
            "coastal_salary": "R$ " + _fmt_num(cs),
            "interior_workers": _fmt_num(iw),
            "interior_exposure": str(ie).replace(".", ","),
            "interior_salary": "R$ " + _fmt_num(is_),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 151: border-states
# ═══════════════════════════════════════════════════════════════════════════════

def _border_states(data, summary):
    por_uf = summary["por_uf"]
    non_border = set(por_uf.keys()) - _BORDER_CODES
    bw, be, bs = _uf_group_stats(por_uf, _BORDER_CODES)
    nw, ne_, ns = _uf_group_stats(por_uf, non_border)
    return {
        "headline_stat": str(be).replace(".", ","),
        "headline_label": f"exposição média nos estados fronteiriços vs {str(ne_).replace('.', ',')} nos demais",
        "chart_data": [
            {"label": "Fronteira", "value": be, "formatted": str(be).replace(".", ","),
             "detail": _fmt_num(bw) + " trabalhadores"},
            {"label": "Demais estados", "value": ne_, "formatted": str(ne_).replace(".", ","),
             "detail": _fmt_num(nw) + " trabalhadores"},
        ],
        "details": {
            "border_workers": _fmt_num(bw),
            "border_exposure": str(be).replace(".", ","),
            "border_salary": "R$ " + _fmt_num(bs),
            "non_border_workers": _fmt_num(nw),
            "non_border_exposure": str(ne_).replace(".", ","),
            "non_border_salary": "R$ " + _fmt_num(ns),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 152: five-regions-comparison
# ═══════════════════════════════════════════════════════════════════════════════

def _five_regions_comparison(data, summary):
    por_uf = summary["por_uf"]
    results = []
    for region, codes in _REGIONS.items():
        w, e, s = _uf_group_stats(por_uf, codes)
        results.append({"region": region, "workers": w, "exposure": e, "salary": s})
    results.sort(key=lambda r: r["exposure"], reverse=True)
    leader = results[0]
    return {
        "headline_stat": str(leader["exposure"]).replace(".", ","),
        "headline_label": f"exposição média — {leader['region']} lidera entre as 5 regiões",
        "chart_data": [
            {"label": r["region"], "value": r["exposure"],
             "formatted": str(r["exposure"]).replace(".", ","),
             "detail": _fmt_num(r["workers"]) + " trabalhadores"}
            for r in results
        ],
        "details": {
            "regions": [
                {"nome": r["region"], "workers": _fmt_num(r["workers"]),
                 "exposure": str(r["exposure"]).replace(".", ","),
                 "salary": "R$ " + _fmt_num(r["salary"])}
                for r in results
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 153: state-exposure-variance
# ═══════════════════════════════════════════════════════════════════════════════

def _state_exposure_variance(data, summary):
    por_uf = summary["por_uf"]
    all_exps = [info["avg_exposicao"] for info in por_uf.values() if "avg_exposicao" in info]
    national_avg = _safe_avg(all_exps)
    deviations = []
    for code, info in por_uf.items():
        exp = info.get("avg_exposicao")
        if exp is not None:
            deviations.append({"uf": info["nome"], "exposure": exp,
                               "diff": round(exp - national_avg, 2)})
    deviations.sort(key=lambda d: d["diff"], reverse=True)
    above = deviations[:5]
    below = deviations[-5:][::-1]
    below.sort(key=lambda d: d["diff"])
    return {
        "headline_stat": str(round(national_avg, 1)).replace(".", ","),
        "headline_label": "exposição média nacional — estados divergem significativamente",
        "chart_data": [
            {"label": d["uf"], "value": d["diff"],
             "formatted": ("+" if d["diff"] >= 0 else "") + str(round(d["diff"], 1)).replace(".", ",")}
            for d in above + below
        ],
        "details": {
            "national_avg": str(round(national_avg, 1)).replace(".", ","),
            "above_avg": [{"uf": d["uf"], "exposure": str(d["exposure"]).replace(".", ","),
                           "diff": "+" + str(round(d["diff"], 1)).replace(".", ",")} for d in above],
            "below_avg": [{"uf": d["uf"], "exposure": str(d["exposure"]).replace(".", ","),
                           "diff": str(round(d["diff"], 1)).replace(".", ",")} for d in below],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 154: state-salary-exposure-correlation
# ═══════════════════════════════════════════════════════════════════════════════

def _state_salary_exposure_correlation(data, summary):
    por_uf = summary["por_uf"]
    states = [{"uf": info["nome"], "salary": info.get("avg_salary", 0),
               "exposure": info.get("avg_exposicao", 0)}
              for info in por_uf.values()]
    states.sort(key=lambda s: s["salary"], reverse=True)
    top5 = states[:5]
    bottom5 = states[-5:]
    avg_exp_top = round(_safe_avg([s["exposure"] for s in top5]), 1)
    avg_exp_bottom = round(_safe_avg([s["exposure"] for s in bottom5]), 1)
    return {
        "headline_stat": str(avg_exp_top).replace(".", ","),
        "headline_label": f"exposição nos estados mais ricos vs {str(avg_exp_bottom).replace('.', ',')} nos mais pobres",
        "chart_data": [
            {"label": "Top 5 salário", "value": avg_exp_top,
             "formatted": str(avg_exp_top).replace(".", ",")},
            {"label": "Bottom 5 salário", "value": avg_exp_bottom,
             "formatted": str(avg_exp_bottom).replace(".", ",")},
        ],
        "details": {
            "avg_exp_top5": str(avg_exp_top).replace(".", ","),
            "avg_exp_bottom5": str(avg_exp_bottom).replace(".", ","),
            "top5": [{"uf": s["uf"], "salary": "R$ " + _fmt_num(round(s["salary"])),
                      "exposure": str(s["exposure"]).replace(".", ",")} for s in top5],
            "bottom5": [{"uf": s["uf"], "salary": "R$ " + _fmt_num(round(s["salary"])),
                         "exposure": str(s["exposure"]).replace(".", ",")} for s in bottom5],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 155: metropolitan-vs-rural-proxy
# ═══════════════════════════════════════════════════════════════════════════════

def _metropolitan_vs_rural_proxy(data, summary):
    por_uf = summary["por_uf"]
    urban_codes = {"35", "33", "53"}
    rural_codes = {"11", "12", "17", "22", "21"}
    uw, ue, us_ = _uf_group_stats(por_uf, urban_codes)
    rw, re_, rs = _uf_group_stats(por_uf, rural_codes)
    return {
        "headline_stat": str(ue).replace(".", ","),
        "headline_label": f"exposição em SP+RJ+DF vs {str(re_).replace('.', ',')} em estados rurais",
        "chart_data": [
            {"label": "SP + RJ + DF", "value": ue,
             "formatted": str(ue).replace(".", ","),
             "detail": _fmt_num(uw) + " trabalhadores"},
            {"label": "RO + AC + TO + PI + MA", "value": re_,
             "formatted": str(re_).replace(".", ","),
             "detail": _fmt_num(rw) + " trabalhadores"},
        ],
        "details": {
            "urban_workers": _fmt_num(uw),
            "urban_exposure": str(ue).replace(".", ","),
            "urban_salary": "R$ " + _fmt_num(us_),
            "rural_workers": _fmt_num(rw),
            "rural_exposure": str(re_).replace(".", ","),
            "rural_salary": "R$ " + _fmt_num(rs),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 156: preta-parda-breakdown
# ═══════════════════════════════════════════════════════════════════════════════

def _preta_parda_breakdown(data, summary):
    total_preta = 0
    total_parda = 0
    total_all = 0
    for o in data:
        dem = o.get("demographics")
        if not dem:
            continue
        preta = dem.get("total_preta", 0)
        parda = dem.get("total_parda", 0)
        fem = dem.get("total_feminino", 0)
        masc = dem.get("total_masculino", 0)
        total_preta += preta
        total_parda += parda
        total_all += fem + masc
    pct_preta = round(total_preta / total_all * 100, 1) if total_all else 0
    pct_parda = round(total_parda / total_all * 100, 1) if total_all else 0
    pct_negra = round((total_preta + total_parda) / total_all * 100, 1) if total_all else 0
    return {
        "headline_stat": _fmt_pct(pct_negra),
        "headline_label": "da força de trabalho é preta ou parda",
        "chart_data": [
            {"label": "Preta", "value": pct_preta, "formatted": _fmt_pct(pct_preta),
             "detail": _fmt_num(total_preta) + " trabalhadores"},
            {"label": "Parda", "value": pct_parda, "formatted": _fmt_pct(pct_parda),
             "detail": _fmt_num(total_parda) + " trabalhadores"},
        ],
        "details": {
            "total_preta": _fmt_num(total_preta),
            "total_parda": _fmt_num(total_parda),
            "total_negra": _fmt_num(total_preta + total_parda),
            "pct_preta": _fmt_pct(pct_preta),
            "pct_parda": _fmt_pct(pct_parda),
            "pct_negra": _fmt_pct(pct_negra),
            "total_workforce": _fmt_num(total_all),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 157: gender-gap-by-salary-band
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_gap_by_salary_band(data, summary):
    bands = {"< R$ 2.000": (0, 2000), "R$ 2.000–4.000": (2000, 4000),
             "R$ 4.000–8.000": (4000, 8000), "R$ 8.000+": (8000, float("inf"))}
    results = []
    for label, (lo, hi) in bands.items():
        total_f = 0
        total_m = 0
        for o in data:
            sal = o.get("salario")
            dem = o.get("demographics")
            if sal is None or dem is None:
                continue
            if lo <= sal < hi:
                total_f += dem.get("total_feminino", 0)
                total_m += dem.get("total_masculino", 0)
        total = total_f + total_m
        pct_f = round(total_f / total * 100, 1) if total else 0
        results.append({"band": label, "pct_female": pct_f, "total_f": total_f, "total": total})
    headline = results[-1] if results else {"band": "N/D", "pct_female": 0}
    return {
        "headline_stat": _fmt_pct(headline["pct_female"]),
        "headline_label": f"de mulheres na faixa {headline['band']}",
        "chart_data": [
            {"label": r["band"], "value": r["pct_female"], "formatted": _fmt_pct(r["pct_female"])}
            for r in results
        ],
        "details": {
            "bands": [{"faixa": r["band"], "pct_feminino": _fmt_pct(r["pct_female"]),
                        "total": _fmt_num(r["total"])} for r in results],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 158: women-high-salary
# ═══════════════════════════════════════════════════════════════════════════════

def _women_high_salary(data, summary):
    high_sal = [o for o in data if o.get("salario") and o["salario"] >= 8000 and o.get("demographics")]
    pct_f, total_f, total_m = _pct_female(high_sal)
    n_occs = len(high_sal)
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres nas ocupações com salário acima de R$ 8.000",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": round(100 - pct_f, 1), "formatted": _fmt_pct(100 - pct_f)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "n_occupations": n_occs,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 159: men-care-economy
# ═══════════════════════════════════════════════════════════════════════════════

def _men_care_economy(data, summary):
    keywords = ["cuidador", "doméstic", "babá", "diarist"]
    matches = _keyword_filter(data, keywords)
    matches_with_dem = [o for o in matches if o.get("demographics")]
    total_m = sum(o["demographics"].get("total_masculino", 0) for o in matches_with_dem)
    total_f = sum(o["demographics"].get("total_feminino", 0) for o in matches_with_dem)
    total = total_m + total_f
    pct_m = round(total_m / total * 100, 1) if total else 0
    return {
        "headline_stat": _fmt_pct(pct_m),
        "headline_label": "de homens na economia do cuidado",
        "chart_data": [
            {"label": "Homens", "value": pct_m, "formatted": _fmt_pct(pct_m)},
            {"label": "Mulheres", "value": round(100 - pct_m, 1), "formatted": _fmt_pct(100 - pct_m)},
        ],
        "details": {
            "pct_masculino": _fmt_pct(pct_m),
            "total_masculino": _fmt_num(total_m),
            "total_feminino": _fmt_num(total_f),
            "total_workers": _fmt_num(total),
            "n_occupations": len(matches_with_dem),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 160: race-opportunity-gap
# ═══════════════════════════════════════════════════════════════════════════════

def _race_opportunity_gap(data, summary):
    high_opp = [o for o in data if o.get("oportunidade") is not None and o["oportunidade"] >= 7 and o.get("demographics")]
    low_opp = [o for o in data if o.get("oportunidade") is not None and o["oportunidade"] <= 3 and o.get("demographics")]
    hi_branca = sum(o["demographics"].get("total_branca", 0) for o in high_opp)
    hi_negra = sum(o["demographics"].get("total_negra", 0) for o in high_opp)
    lo_branca = sum(o["demographics"].get("total_branca", 0) for o in low_opp)
    lo_negra = sum(o["demographics"].get("total_negra", 0) for o in low_opp)
    hi_total = hi_branca + hi_negra
    lo_total = lo_branca + lo_negra
    pct_branca_hi = round(hi_branca / hi_total * 100, 1) if hi_total else 0
    pct_negra_hi = round(hi_negra / hi_total * 100, 1) if hi_total else 0
    pct_branca_lo = round(lo_branca / lo_total * 100, 1) if lo_total else 0
    pct_negra_lo = round(lo_negra / lo_total * 100, 1) if lo_total else 0
    return {
        "headline_stat": _fmt_pct(pct_branca_hi),
        "headline_label": "de brancos em ocupações de alta oportunidade",
        "chart_data": [
            {"label": "Alta oportunidade — Branca", "value": pct_branca_hi,
             "formatted": _fmt_pct(pct_branca_hi)},
            {"label": "Alta oportunidade — Negra", "value": pct_negra_hi,
             "formatted": _fmt_pct(pct_negra_hi)},
            {"label": "Baixa oportunidade — Branca", "value": pct_branca_lo,
             "formatted": _fmt_pct(pct_branca_lo)},
            {"label": "Baixa oportunidade — Negra", "value": pct_negra_lo,
             "formatted": _fmt_pct(pct_negra_lo)},
        ],
        "details": {
            "pct_branca_high_opp": _fmt_pct(pct_branca_hi),
            "pct_negra_high_opp": _fmt_pct(pct_negra_hi),
            "pct_branca_low_opp": _fmt_pct(pct_branca_lo),
            "pct_negra_low_opp": _fmt_pct(pct_negra_lo),
            "n_high_opp": len(high_opp),
            "n_low_opp": len(low_opp),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 161: gender-in-tech
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_in_tech(data, summary):
    keywords = ["programa", "desenvolvedor", "sistemas", "software", "dados", "tecnologia"]
    matches = _keyword_filter(data, keywords)
    matches_dem = [o for o in matches if o.get("demographics")]
    pct_f, total_f, total_m = _pct_female(matches_dem)
    total = total_f + total_m
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres nas ocupações de tecnologia",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": round(100 - pct_f, 1), "formatted": _fmt_pct(100 - pct_f)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_workers": _fmt_num(total),
            "n_occupations": len(matches_dem),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 162: gender-in-health
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_in_health(data, summary):
    keywords = ["enferme", "médic", "saúde", "dentist", "farmac"]
    matches = _keyword_filter(data, keywords)
    matches_dem = [o for o in matches if o.get("demographics")]
    pct_f, total_f, total_m = _pct_female(matches_dem)
    total = total_f + total_m
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres nas ocupações de saúde",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": round(100 - pct_f, 1), "formatted": _fmt_pct(100 - pct_f)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_workers": _fmt_num(total),
            "n_occupations": len(matches_dem),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 163: women-growing-vs-declining
# ═══════════════════════════════════════════════════════════════════════════════

def _women_growing_vs_declining(data, summary):
    growing = [o for o in data if o.get("saldo") and o["saldo"] > 0 and o.get("demographics")]
    declining = [o for o in data if o.get("saldo") and o["saldo"] < 0 and o.get("demographics")]
    pct_f_grow, f_grow, m_grow = _pct_female(growing)
    pct_f_dec, f_dec, m_dec = _pct_female(declining)
    diff = round(pct_f_grow - pct_f_dec, 1)
    return {
        "headline_stat": _fmt_pct(pct_f_grow),
        "headline_label": f"de mulheres em ocupações em crescimento vs {_fmt_pct(pct_f_dec)} em declínio",
        "chart_data": [
            {"label": "Em crescimento", "value": pct_f_grow, "formatted": _fmt_pct(pct_f_grow),
             "detail": f"{len(growing)} ocupações"},
            {"label": "Em declínio", "value": pct_f_dec, "formatted": _fmt_pct(pct_f_dec),
             "detail": f"{len(declining)} ocupações"},
        ],
        "details": {
            "pct_fem_growing": _fmt_pct(pct_f_grow),
            "pct_fem_declining": _fmt_pct(pct_f_dec),
            "diff_pp": _fmt_pct(abs(diff)),
            "n_growing": len(growing),
            "n_declining": len(declining),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 164: race-salary-gap
# ═══════════════════════════════════════════════════════════════════════════════

def _race_salary_gap(data, summary):
    branca_dom = []
    negra_dom = []
    for o in data:
        dem = o.get("demographics")
        sal = o.get("salario")
        if not dem or sal is None:
            continue
        b = dem.get("total_branca", 0)
        n = dem.get("total_negra", 0)
        total = b + n
        if total == 0:
            continue
        pct_b = b / total * 100
        if pct_b > 60:
            branca_dom.append(o)
        elif pct_b < 40:
            negra_dom.append(o)
    avg_sal_b = round(_safe_avg([o["salario"] for o in branca_dom])) if branca_dom else 0
    avg_sal_n = round(_safe_avg([o["salario"] for o in negra_dom])) if negra_dom else 0
    gap = avg_sal_b - avg_sal_n
    ratio = round(avg_sal_b / avg_sal_n, 2) if avg_sal_n else 0
    return {
        "headline_stat": "R$ " + _fmt_num(gap),
        "headline_label": "diferença salarial entre ocupações majoritariamente brancas e negras",
        "chart_data": [
            {"label": "Maioria branca (>60%)", "value": avg_sal_b,
             "formatted": "R$ " + _fmt_num(avg_sal_b),
             "detail": f"{len(branca_dom)} ocupações"},
            {"label": "Maioria negra (>60%)", "value": avg_sal_n,
             "formatted": "R$ " + _fmt_num(avg_sal_n),
             "detail": f"{len(negra_dom)} ocupações"},
        ],
        "details": {
            "avg_salary_branca": "R$ " + _fmt_num(avg_sal_b),
            "avg_salary_negra": "R$ " + _fmt_num(avg_sal_n),
            "gap": "R$ " + _fmt_num(gap),
            "ratio": str(ratio).replace(".", ","),
            "n_branca_dom": len(branca_dom),
            "n_negra_dom": len(negra_dom),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 165: demographic-data-coverage
# ═══════════════════════════════════════════════════════════════════════════════

def _demographic_data_coverage(data, summary):
    total = len(data)
    with_dem = sum(1 for o in data if o.get("demographics"))
    with_uf = sum(1 for o in data if o.get("por_uf"))
    pct_dem = round(with_dem / total * 100, 1) if total else 0
    pct_uf = round(with_uf / total * 100, 1) if total else 0
    return {
        "headline_stat": _fmt_pct(pct_dem),
        "headline_label": "das ocupações possuem dados demográficos",
        "chart_data": [
            {"label": "Com dados demográficos", "value": pct_dem, "formatted": _fmt_pct(pct_dem),
             "detail": f"{with_dem} de {total}"},
            {"label": "Com dados por UF", "value": pct_uf, "formatted": _fmt_pct(pct_uf),
             "detail": f"{with_uf} de {total}"},
        ],
        "details": {
            "total_occupations": total,
            "with_demographics": with_dem,
            "pct_demographics": _fmt_pct(pct_dem),
            "with_por_uf": with_uf,
            "pct_por_uf": _fmt_pct(pct_uf),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 166: gender-in-agriculture
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_in_agriculture(data, summary):
    agro = [o for o in data if o.get("grande_grupo") and "AGROPECUÁRIO" in o["grande_grupo"].upper()
            and o.get("demographics")]
    pct_f, total_f, total_m = _pct_female(agro)
    total = total_f + total_m
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres no setor agropecuário",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": round(100 - pct_f, 1), "formatted": _fmt_pct(100 - pct_f)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_workers": _fmt_num(total),
            "n_occupations": len(agro),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 167: gender-in-manufacturing
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_in_manufacturing(data, summary):
    mfg = [o for o in data if o.get("grande_grupo") and "PRODUÇÃO" in o["grande_grupo"].upper()
           and o.get("demographics")]
    pct_f, total_f, total_m = _pct_female(mfg)
    total = total_f + total_m
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres na produção industrial",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": round(100 - pct_f, 1), "formatted": _fmt_pct(100 - pct_f)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_workers": _fmt_num(total),
            "n_occupations": len(mfg),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 168: gender-diversity-by-grupo
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_diversity_by_grupo(data, summary):
    grupos = {}
    for o in data:
        gg = o.get("grande_grupo")
        dem = o.get("demographics")
        if not gg or not dem:
            continue
        if gg not in grupos:
            grupos[gg] = {"f": 0, "m": 0}
        grupos[gg]["f"] += dem.get("total_feminino", 0)
        grupos[gg]["m"] += dem.get("total_masculino", 0)
    results = []
    for gg, vals in grupos.items():
        total = vals["f"] + vals["m"]
        if total == 0:
            continue
        pct_f = round(vals["f"] / total * 100, 1)
        balance = round(50 - abs(50 - pct_f), 1)
        results.append({"grupo": gg, "pct_female": pct_f, "balance": balance, "total": total})
    results.sort(key=lambda r: r["balance"], reverse=True)
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
    leader = results[0] if results else {"grupo": "N/D", "pct_female": 0}
    return {
        "headline_stat": _fmt_pct(leader["pct_female"]),
        "headline_label": f"de mulheres em {short_names.get(leader['grupo'], leader['grupo'])} — mais equilibrado",
        "chart_data": [
            {"label": short_names.get(r["grupo"], r["grupo"]),
             "value": r["pct_female"], "formatted": _fmt_pct(r["pct_female"])}
            for r in results
        ],
        "details": {
            "ranking": [
                {"grupo": short_names.get(r["grupo"], r["grupo"]),
                 "pct_feminino": _fmt_pct(r["pct_female"]),
                 "total": _fmt_num(r["total"])}
                for r in results
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 169: gender-in-finance
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_in_finance(data, summary):
    keywords = ["contab", "financ", "banc", "audit"]
    matches = _keyword_filter(data, keywords)
    matches_dem = [o for o in matches if o.get("demographics")]
    pct_f, total_f, total_m = _pct_female(matches_dem)
    total = total_f + total_m
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres nas ocupações financeiras",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": round(100 - pct_f, 1), "formatted": _fmt_pct(100 - pct_f)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_workers": _fmt_num(total),
            "n_occupations": len(matches_dem),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 170: gender-in-legal
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_in_legal(data, summary):
    keywords = ["advogad", "jurídic"]
    matches = _keyword_filter(data, keywords)
    matches_dem = [o for o in matches if o.get("demographics")]
    pct_f, total_f, total_m = _pct_female(matches_dem)
    total = total_f + total_m
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres nas ocupações jurídicas",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": round(100 - pct_f, 1), "formatted": _fmt_pct(100 - pct_f)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_workers": _fmt_num(total),
            "n_occupations": len(matches_dem),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 171: gender-in-education-teaching
# ═══════════════════════════════════════════════════════════════════════════════

def _gender_in_education_teaching(data, summary):
    keywords = ["professor"]
    matches = _keyword_filter(data, keywords)
    matches_dem = [o for o in matches if o.get("demographics")]
    pct_f, total_f, total_m = _pct_female(matches_dem)
    total = total_f + total_m
    total_workers = sum(o.get("empregados", 0) or 0 for o in matches)
    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "de mulheres entre professores",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": round(100 - pct_f, 1), "formatted": _fmt_pct(100 - pct_f)},
        ],
        "details": {
            "pct_feminino": _fmt_pct(pct_f),
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "total_dem_workers": _fmt_num(total),
            "total_workers": _fmt_num(total_workers),
            "n_occupations": len(matches),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template list
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES_BATCH_B1 = [
    # 147
    {
        "id": "capital-exposure",
        "category": "Regional",
        "tags": ["Distrito Federal", "DF", "capital", "exposição"],
        "chart_type": "comparison_pair",
        "analysis_fn": _capital_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a exposição do Distrito Federal à IA — o estado mais "white collar" do Brasil.

DADOS (use APENAS estes números, não invente dados):
- Exposição média DF: {df_exposicao}
- Salário médio DF: {df_salary}
- Trabalhadores DF: {df_workers}
- Média nacional: {national_avg}
- Diferença: {diff} pontos

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 148
    {
        "id": "state-salary-gap",
        "category": "Regional",
        "tags": ["salário", "desigualdade", "estados"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_salary_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença salarial entre o estado mais rico e o mais pobre do Brasil.

DADOS (use APENAS estes números, não invente dados):
- Estado com maior salário: {top_state} — {top_salary}
- Estado com menor salário: {bottom_state} — {bottom_salary}
- Diferença: {gap}
- Razão: {ratio}x

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 149
    {
        "id": "state-most-concentrated",
        "category": "Regional",
        "tags": ["concentração", "ocupações", "estados"],
        "chart_type": "ranking_table",
        "analysis_fn": _state_most_concentrated,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre qual estado tem o mercado de trabalho mais concentrado em uma única ocupação.

DADOS (use APENAS estes números, não invente dados):
- Estado mais concentrado: {top_state} — {top_pct} em {top_occupation}
- Ranking: {ranking}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 150
    {
        "id": "coastal-vs-interior",
        "category": "Regional",
        "tags": ["litoral", "interior", "comparação"],
        "chart_type": "comparison_pair",
        "analysis_fn": _coastal_vs_interior,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando o impacto da IA entre estados litorâneos e do interior do Brasil.

DADOS (use APENAS estes números, não invente dados):
- Litoral: {coastal_workers} trabalhadores, exposição {coastal_exposure}, salário {coastal_salary}
- Interior: {interior_workers} trabalhadores, exposição {interior_exposure}, salário {interior_salary}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 151
    {
        "id": "border-states",
        "category": "Regional",
        "tags": ["fronteira", "estados", "comparação"],
        "chart_type": "comparison_pair",
        "analysis_fn": _border_states,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando estados fronteiriços com os demais em relação ao impacto da IA.

DADOS (use APENAS estes números, não invente dados):
- Fronteiriços: {border_workers} trabalhadores, exposição {border_exposure}, salário {border_salary}
- Demais: {non_border_workers} trabalhadores, exposição {non_border_exposure}, salário {non_border_salary}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 152
    {
        "id": "five-regions-comparison",
        "category": "Regional",
        "tags": ["regiões", "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _five_regions_comparison,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando as 5 regiões do Brasil em relação à exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Regiões: {regions}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 153
    {
        "id": "state-exposure-variance",
        "category": "Regional",
        "tags": ["variância", "exposição", "estados", "desvio"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_exposure_variance,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre quais estados mais se desviam da média nacional de exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Média nacional: {national_avg}
- Acima da média: {above_avg}
- Abaixo da média: {below_avg}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 154
    {
        "id": "state-salary-exposure-correlation",
        "category": "Regional",
        "tags": ["correlação", "salário", "exposição", "estados"],
        "chart_type": "comparison_pair",
        "analysis_fn": _state_salary_exposure_correlation,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a relação entre riqueza e exposição à IA nos estados brasileiros.

DADOS (use APENAS estes números, não invente dados):
- Top 5 salário — exposição média: {avg_exp_top5}
- Bottom 5 salário — exposição média: {avg_exp_bottom5}
- Top 5: {top5}
- Bottom 5: {bottom5}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 155
    {
        "id": "metropolitan-vs-rural-proxy",
        "category": "Regional",
        "tags": ["metrópole", "rural", "SP", "RJ", "DF"],
        "chart_type": "comparison_pair",
        "analysis_fn": _metropolitan_vs_rural_proxy,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando estados metropolitanos (SP+RJ+DF) com estados rurais (RO+AC+TO+PI+MA).

DADOS (use APENAS estes números, não invente dados):
- Metropolitanos: {urban_workers} trabalhadores, exposição {urban_exposure}, salário {urban_salary}
- Rurais: {rural_workers} trabalhadores, exposição {rural_exposure}, salário {rural_salary}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 156
    {
        "id": "preta-parda-breakdown",
        "category": "Demografia",
        "tags": ["raça", "preta", "parda", "negra"],
        "chart_type": "comparison_pair",
        "analysis_fn": _preta_parda_breakdown,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a composição racial preta vs parda no mercado de trabalho formal brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Total preta: {total_preta} ({pct_preta})
- Total parda: {total_parda} ({pct_parda})
- Total negra (preta+parda): {total_negra} ({pct_negra})
- Total da força de trabalho analisada: {total_workforce}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 157
    {
        "id": "gender-gap-by-salary-band",
        "category": "Demografia",
        "tags": ["gênero", "salário", "faixa salarial"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _gender_gap_by_salary_band,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a presença feminina varia por faixa salarial no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Faixas salariais: {bands}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 158
    {
        "id": "women-high-salary",
        "category": "Demografia",
        "tags": ["gênero", "alto salário", "mulheres"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_high_salary,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina em ocupações com salário acima de R$ 8.000.

DADOS (use APENAS estes números, não invente dados):
- Mulheres: {pct_feminino} ({total_feminino})
- Homens: {total_masculino}
- Ocupações analisadas: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 159
    {
        "id": "men-care-economy",
        "category": "Demografia",
        "tags": ["gênero", "cuidado", "doméstico", "homens"],
        "chart_type": "comparison_pair",
        "analysis_fn": _men_care_economy,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença masculina na economia do cuidado (cuidadores, domésticos, babás, diaristas).

DADOS (use APENAS estes números, não invente dados):
- Homens: {pct_masculino} ({total_masculino})
- Mulheres: {total_feminino}
- Total: {total_workers}
- Ocupações: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 160
    {
        "id": "race-opportunity-gap",
        "category": "Demografia",
        "tags": ["raça", "oportunidade", "desigualdade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _race_opportunity_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença racial entre ocupações de alta e baixa oportunidade frente à IA.

DADOS (use APENAS estes números, não invente dados):
- Alta oportunidade (≥7): {pct_branca_high_opp} brancos, {pct_negra_high_opp} negros ({n_high_opp} ocupações)
- Baixa oportunidade (≤3): {pct_branca_low_opp} brancos, {pct_negra_low_opp} negros ({n_low_opp} ocupações)

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 161
    {
        "id": "gender-in-tech",
        "category": "Demografia",
        "tags": ["gênero", "tecnologia", "mulheres", "TI"],
        "chart_type": "comparison_pair",
        "analysis_fn": _gender_in_tech,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina nas ocupações de tecnologia no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Mulheres: {pct_feminino} ({total_feminino})
- Homens: {total_masculino}
- Total: {total_workers}
- Ocupações: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 162
    {
        "id": "gender-in-health",
        "category": "Demografia",
        "tags": ["gênero", "saúde", "mulheres"],
        "chart_type": "comparison_pair",
        "analysis_fn": _gender_in_health,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina nas ocupações de saúde no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Mulheres: {pct_feminino} ({total_feminino})
- Homens: {total_masculino}
- Total: {total_workers}
- Ocupações: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 163
    {
        "id": "women-growing-vs-declining",
        "category": "Demografia",
        "tags": ["gênero", "crescimento", "declínio", "saldo"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_growing_vs_declining,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando a presença feminina em ocupações em crescimento vs em declínio.

DADOS (use APENAS estes números, não invente dados):
- Em crescimento: {pct_fem_growing} de mulheres ({n_growing} ocupações)
- Em declínio: {pct_fem_declining} de mulheres ({n_declining} ocupações)
- Diferença: {diff_pp} pontos percentuais

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 164
    {
        "id": "race-salary-gap",
        "category": "Demografia",
        "tags": ["raça", "salário", "desigualdade"],
        "chart_type": "comparison_pair",
        "analysis_fn": _race_salary_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença salarial entre ocupações majoritariamente brancas e negras.

DADOS (use APENAS estes números, não invente dados):
- Ocupações maioria branca (>60%): {avg_salary_branca} ({n_branca_dom} ocupações)
- Ocupações maioria negra (>60%): {avg_salary_negra} ({n_negra_dom} ocupações)
- Diferença: {gap}
- Razão: {ratio}x

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 165
    {
        "id": "demographic-data-coverage",
        "category": "Mercado",
        "tags": ["cobertura", "dados", "qualidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _demographic_data_coverage,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a cobertura dos dados demográficos e regionais das ocupações brasileiras.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {total_occupations}
- Com dados demográficos: {with_demographics} ({pct_demographics})
- Com dados por UF: {with_por_uf} ({pct_por_uf})

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 166
    {
        "id": "gender-in-agriculture",
        "category": "Demografia",
        "tags": ["gênero", "agropecuário", "rural"],
        "chart_type": "comparison_pair",
        "analysis_fn": _gender_in_agriculture,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina no setor agropecuário brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Mulheres: {pct_feminino} ({total_feminino})
- Homens: {total_masculino}
- Total: {total_workers}
- Ocupações: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 167
    {
        "id": "gender-in-manufacturing",
        "category": "Demografia",
        "tags": ["gênero", "produção", "indústria"],
        "chart_type": "comparison_pair",
        "analysis_fn": _gender_in_manufacturing,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina na produção industrial brasileira.

DADOS (use APENAS estes números, não invente dados):
- Mulheres: {pct_feminino} ({total_feminino})
- Homens: {total_masculino}
- Total: {total_workers}
- Ocupações: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 168
    {
        "id": "gender-diversity-by-grupo",
        "category": "Demografia",
        "tags": ["gênero", "grande grupo", "diversidade", "equilíbrio"],
        "chart_type": "ranking_table",
        "analysis_fn": _gender_diversity_by_grupo,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o equilíbrio de gênero nos grandes grupos ocupacionais brasileiros.

DADOS (use APENAS estes números, não invente dados):
- Ranking do mais ao menos equilibrado: {ranking}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 169
    {
        "id": "gender-in-finance",
        "category": "Demografia",
        "tags": ["gênero", "finanças", "contabilidade", "banco"],
        "chart_type": "comparison_pair",
        "analysis_fn": _gender_in_finance,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina nas ocupações financeiras no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Mulheres: {pct_feminino} ({total_feminino})
- Homens: {total_masculino}
- Total: {total_workers}
- Ocupações: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 170
    {
        "id": "gender-in-legal",
        "category": "Demografia",
        "tags": ["gênero", "jurídico", "advocacia"],
        "chart_type": "comparison_pair",
        "analysis_fn": _gender_in_legal,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina nas ocupações jurídicas no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Mulheres: {pct_feminino} ({total_feminino})
- Homens: {total_masculino}
- Total: {total_workers}
- Ocupações: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 171
    {
        "id": "gender-in-education-teaching",
        "category": "Demografia",
        "tags": ["gênero", "educação", "professor", "ensino"],
        "chart_type": "comparison_pair",
        "analysis_fn": _gender_in_education_teaching,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a presença feminina entre professores no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Mulheres: {pct_feminino} ({total_feminino})
- Homens: {total_masculino}
- Total demográfico: {total_dem_workers}
- Total de trabalhadores: {total_workers}
- Ocupações: {n_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates_batch_b1():
    return TEMPLATES_BATCH_B1
