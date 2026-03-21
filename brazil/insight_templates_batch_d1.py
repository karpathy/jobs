"""Insight templates batch D1: comparative + sector deep dives."""
import statistics
from insight_templates import _fmt_pct, _fmt_num, _safe_avg


# ═══════════════════════════════════════════════════════════════════════════════
# Region mapping used by templates 258 & 259
# ═══════════════════════════════════════════════════════════════════════════════

_REGIONS = {
    "Norte": ["11", "12", "13", "14", "15", "16", "17"],
    "Nordeste": ["21", "22", "23", "24", "25", "26", "27", "28", "29"],
    "Sudeste": ["31", "32", "33", "35"],
    "Sul": ["41", "42", "43"],
    "Centro-Oeste": ["50", "51", "52", "53"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Template 247: salary-exposure-quartiles
# ═══════════════════════════════════════════════════════════════════════════════

def _salary_exposure_quartiles(data, summary):
    valid = [o for o in data if o.get("salario") is not None and o.get("exposicao") is not None]
    valid.sort(key=lambda o: o["salario"])
    n = len(valid)
    if n == 0:
        return {"headline_stat": "0", "headline_label": "ocupações com salário", "chart_data": [], "details": {}}
    q_size = n // 4
    quartiles = []
    for i in range(4):
        start = i * q_size
        end = (i + 1) * q_size if i < 3 else n
        chunk = valid[start:end]
        sals = [o["salario"] for o in chunk]
        exps = [o["exposicao"] for o in chunk]
        workers = sum(o.get("empregados") or 0 for o in chunk)
        quartiles.append({
            "label": f"Q{i+1}: R$ {_fmt_num(round(min(sals)))}–{_fmt_num(round(max(sals)))}",
            "sal_min": round(min(sals)),
            "sal_max": round(max(sals)),
            "avg_exposure": round(_safe_avg(exps), 1),
            "count": len(chunk),
            "total_workers": workers,
        })
    return {
        "headline_stat": str(quartiles[3]["avg_exposure"]).replace(".", ","),
        "headline_label": "exposição média no quartil salarial mais alto",
        "chart_data": [
            {"label": q["label"], "value": q["avg_exposure"],
             "formatted": str(q["avg_exposure"]).replace(".", ",")}
            for q in quartiles
        ],
        "details": {
            "quartiles": [
                {"faixa": q["label"], "avg_exposure": str(q["avg_exposure"]).replace(".", ","),
                 "count": str(q["count"]), "total_workers": _fmt_num(q["total_workers"])}
                for q in quartiles
            ],
            "total_occupations": str(n),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 248: salary-vantagem-quartiles
# ═══════════════════════════════════════════════════════════════════════════════

def _salary_vantagem_quartiles(data, summary):
    valid = [o for o in data if o.get("salario") is not None and o.get("vantagem") is not None]
    valid.sort(key=lambda o: o["salario"])
    n = len(valid)
    if n == 0:
        return {"headline_stat": "0", "headline_label": "ocupações com dados", "chart_data": [], "details": {}}
    q_size = n // 4
    quartiles = []
    for i in range(4):
        start = i * q_size
        end = (i + 1) * q_size if i < 3 else n
        chunk = valid[start:end]
        sals = [o["salario"] for o in chunk]
        vants = [o["vantagem"] for o in chunk]
        workers = sum(o.get("empregados") or 0 for o in chunk)
        quartiles.append({
            "label": f"Q{i+1}: R$ {_fmt_num(round(min(sals)))}–{_fmt_num(round(max(sals)))}",
            "avg_vantagem": round(_safe_avg(vants), 1),
            "count": len(chunk),
            "total_workers": workers,
        })
    return {
        "headline_stat": str(quartiles[3]["avg_vantagem"]).replace(".", ","),
        "headline_label": "vantagem média no quartil salarial mais alto",
        "chart_data": [
            {"label": q["label"], "value": q["avg_vantagem"],
             "formatted": str(q["avg_vantagem"]).replace(".", ",")}
            for q in quartiles
        ],
        "details": {
            "quartiles": [
                {"faixa": q["label"], "avg_vantagem": str(q["avg_vantagem"]).replace(".", ","),
                 "count": str(q["count"]), "total_workers": _fmt_num(q["total_workers"])}
                for q in quartiles
            ],
            "total_occupations": str(n),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 249: regional-salary-inequality
# ═══════════════════════════════════════════════════════════════════════════════

def _regional_salary_inequality(data, summary):
    por_uf = summary.get("por_uf", {})
    states = [{"uf": info["nome"], "avg_salary": info.get("avg_salary", 0)}
              for info in por_uf.values() if info.get("avg_salary")]
    states.sort(key=lambda s: s["avg_salary"], reverse=True)
    if len(states) < 2:
        return {"headline_stat": "N/D", "headline_label": "dados insuficientes", "chart_data": [], "details": {}}
    ratio = round(states[0]["avg_salary"] / states[-1]["avg_salary"], 1) if states[-1]["avg_salary"] else 0
    top5 = states[:5]
    bottom5 = states[-5:]
    return {
        "headline_stat": str(ratio).replace(".", ",") + "x",
        "headline_label": "razão entre maior e menor salário médio estadual",
        "chart_data": [
            {"label": s["uf"], "value": s["avg_salary"],
             "formatted": "R$ " + _fmt_num(round(s["avg_salary"]))}
            for s in top5 + bottom5
        ],
        "details": {
            "ratio": str(ratio).replace(".", ","),
            "top5": [{"uf": s["uf"], "avg_salary": "R$ " + _fmt_num(round(s["avg_salary"]))} for s in top5],
            "bottom5": [{"uf": s["uf"], "avg_salary": "R$ " + _fmt_num(round(s["avg_salary"]))} for s in bottom5],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 250: regional-exposure-spread
# ═══════════════════════════════════════════════════════════════════════════════

def _regional_exposure_spread(data, summary):
    por_uf = summary.get("por_uf", {})
    states = [{"uf": info["nome"], "avg_exposicao": info.get("avg_exposicao", 0)}
              for info in por_uf.values() if info.get("avg_exposicao") is not None]
    states.sort(key=lambda s: s["avg_exposicao"], reverse=True)
    if not states:
        return {"headline_stat": "N/D", "headline_label": "dados insuficientes", "chart_data": [], "details": {}}
    spread = round(states[0]["avg_exposicao"] - states[-1]["avg_exposicao"], 1)
    return {
        "headline_stat": str(spread).replace(".", ","),
        "headline_label": "pontos de diferença entre estados extremos",
        "chart_data": [
            {"label": s["uf"], "value": s["avg_exposicao"],
             "formatted": str(s["avg_exposicao"]).replace(".", ",")}
            for s in states
        ],
        "details": {
            "spread": str(spread).replace(".", ","),
            "top_state": states[0]["uf"],
            "top_score": str(states[0]["avg_exposicao"]).replace(".", ","),
            "bottom_state": states[-1]["uf"],
            "bottom_score": str(states[-1]["avg_exposicao"]).replace(".", ","),
            "all_states": [
                {"uf": s["uf"], "score": str(s["avg_exposicao"]).replace(".", ",")}
                for s in states
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 251: top-50-employers-profile
# ═══════════════════════════════════════════════════════════════════════════════

def _top_50_employers_profile(data, summary):
    with_emp = [o for o in data if o.get("empregados") and o["empregados"] > 0]
    with_emp.sort(key=lambda o: o["empregados"], reverse=True)
    top50 = with_emp[:50]
    total_national = sum(o.get("empregados") or 0 for o in data)
    total_top50 = sum(o["empregados"] for o in top50)
    pct = round(total_top50 / total_national * 100, 1) if total_national else 0
    avg_exp = round(_safe_avg([o.get("exposicao") for o in top50 if o.get("exposicao") is not None]), 1)
    sal_vals = [o["salario"] for o in top50 if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    return {
        "headline_stat": _fmt_pct(pct),
        "headline_label": "da força de trabalho nas 50 maiores ocupações",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["empregados"],
             "formatted": _fmt_num(o["empregados"])}
            for o in top50[:10]
        ],
        "details": {
            "total_top50": _fmt_num(total_top50),
            "total_national": _fmt_num(total_national),
            "pct_workforce": _fmt_pct(pct),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top10": [
                {"titulo": o.get("titulo", ""), "empregados": _fmt_num(o["empregados"])}
                for o in top50[:10]
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 252: smallest-occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _smallest_occupations(data, summary):
    with_emp = [o for o in data if o.get("empregados") and o["empregados"] > 0]
    with_emp.sort(key=lambda o: o["empregados"])
    bottom20 = with_emp[:20]
    avg_exp = round(_safe_avg([o.get("exposicao") for o in bottom20 if o.get("exposicao") is not None]), 1)
    sal_vals = [o["salario"] for o in bottom20 if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    return {
        "headline_stat": str(len(bottom20)),
        "headline_label": "menores ocupações por número de empregados",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["empregados"],
             "formatted": _fmt_num(o["empregados"])}
            for o in bottom20
        ],
        "details": {
            "occupations": [
                {"titulo": o.get("titulo", ""), "empregados": _fmt_num(o["empregados"]),
                 "exposicao": str(o.get("exposicao", "N/D")).replace(".", ","),
                 "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in bottom20
            ],
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal) if avg_sal else "N/D",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 253: saldo-per-thousand
# ═══════════════════════════════════════════════════════════════════════════════

def _saldo_per_thousand(data, summary):
    valid = [o for o in data if o.get("saldo") is not None and o.get("empregados") and o["empregados"] >= 1000]
    for o in valid:
        o["_spt"] = o["saldo"] / o["empregados"] * 1000
    valid.sort(key=lambda o: o["_spt"], reverse=True)
    top10 = valid[:10]
    return {
        "headline_stat": str(round(top10[0]["_spt"], 1)).replace(".", ",") if top10 else "N/D",
        "headline_label": "saldo por mil empregados (líder)",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": round(o["_spt"], 1),
             "formatted": str(round(o["_spt"], 1)).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o.get("titulo", ""), "saldo_per_mil": str(round(o["_spt"], 1)).replace(".", ","),
                 "saldo": _fmt_num(o["saldo"]), "empregados": _fmt_num(o["empregados"])}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 254: hiring-efficiency
# ═══════════════════════════════════════════════════════════════════════════════

def _hiring_efficiency(data, summary):
    valid = [o for o in data
             if o.get("admissoes") and o["admissoes"] >= 500
             and o.get("saldo") is not None and o["saldo"] > 0]
    for o in valid:
        o["_eff"] = round(o["saldo"] / o["admissoes"] * 100, 1)
    valid.sort(key=lambda o: o["_eff"], reverse=True)
    top10 = valid[:10]
    return {
        "headline_stat": _fmt_pct(top10[0]["_eff"]) if top10 else "N/D",
        "headline_label": "das admissões resultam em saldo líquido (líder)",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["_eff"],
             "formatted": _fmt_pct(o["_eff"])}
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o.get("titulo", ""), "efficiency": _fmt_pct(o["_eff"]),
                 "admissoes": _fmt_num(o["admissoes"]), "saldo": _fmt_num(o["saldo"])}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 255: occupations-missing-salary
# ═══════════════════════════════════════════════════════════════════════════════

def _occupations_missing_salary(data, summary):
    no_sal = [o for o in data if o.get("salario") is None]
    no_emp = [o for o in data if not o.get("empregados")]
    both_missing = [o for o in data if o.get("salario") is None and not o.get("empregados")]
    return {
        "headline_stat": str(len(no_sal)),
        "headline_label": "ocupações sem dados de salário",
        "chart_data": [
            {"label": "Sem salário", "value": len(no_sal), "formatted": str(len(no_sal))},
            {"label": "Sem empregados", "value": len(no_emp), "formatted": str(len(no_emp))},
            {"label": "Sem ambos", "value": len(both_missing), "formatted": str(len(both_missing))},
        ],
        "details": {
            "no_salary": str(len(no_sal)),
            "no_empregados": str(len(no_emp)),
            "both_missing": str(len(both_missing)),
            "total": str(len(data)),
            "pct_no_salary": _fmt_pct(round(len(no_sal) / len(data) * 100, 1)) if data else "0%",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 256: data-completeness
# ═══════════════════════════════════════════════════════════════════════════════

def _data_completeness(data, summary):
    fields = ["empregados", "salario", "saldo", "admissoes", "salario_admissao"]
    counts = {i: 0 for i in range(6)}  # 0..5 fields present
    for o in data:
        present = sum(1 for f in fields if o.get(f) is not None)
        counts[present] += 1
    total = len(data) or 1
    return {
        "headline_stat": _fmt_pct(round(counts[5] / total * 100, 1)),
        "headline_label": "das ocupações com todos os 5 campos preenchidos",
        "chart_data": [
            {"label": f"{i} campos", "value": counts[i],
             "formatted": str(counts[i])}
            for i in range(5, -1, -1)
        ],
        "details": {
            "breakdown": [
                {"fields_present": str(i), "count": str(counts[i]),
                 "pct": _fmt_pct(round(counts[i] / total * 100, 1))}
                for i in range(5, -1, -1)
            ],
            "total": str(len(data)),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 257: most-common-subgrupo
# ═══════════════════════════════════════════════════════════════════════════════

def _most_common_subgrupo(data, summary):
    counts = {}
    for o in data:
        sub = o.get("subgrupo_principal")
        if sub:
            counts[sub] = counts.get(sub, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top10 = ranked[:10]
    return {
        "headline_stat": str(top10[0][1]) if top10 else "0",
        "headline_label": f"ocupações em \"{top10[0][0]}\"" if top10 else "subgrupo líder",
        "chart_data": [
            {"label": name, "value": cnt, "formatted": str(cnt)}
            for name, cnt in top10
        ],
        "details": {
            "top10": [
                {"subgrupo": name, "count": str(cnt)}
                for name, cnt in top10
            ],
            "total_subgrupos": str(len(counts)),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 258: salary-by-5-regions
# ═══════════════════════════════════════════════════════════════════════════════

def _salary_by_5_regions(data, summary):
    por_uf = summary.get("por_uf", {})
    results = []
    for region, codes in _REGIONS.items():
        total_w = 0
        weighted_sal = 0
        for code in codes:
            info = por_uf.get(code, {})
            w = info.get("total_workers", 0)
            s = info.get("avg_salary", 0)
            if w and s:
                weighted_sal += s * w
                total_w += w
        avg_sal = round(weighted_sal / total_w) if total_w else 0
        results.append({"region": region, "avg_salary": avg_sal, "total_workers": total_w})
    results.sort(key=lambda r: r["avg_salary"], reverse=True)
    return {
        "headline_stat": "R$ " + _fmt_num(results[0]["avg_salary"]) if results else "N/D",
        "headline_label": f"salário médio ponderado — {results[0]['region']}" if results else "",
        "chart_data": [
            {"label": r["region"], "value": r["avg_salary"],
             "formatted": "R$ " + _fmt_num(r["avg_salary"])}
            for r in results
        ],
        "details": {
            "regions": [
                {"region": r["region"], "avg_salary": "R$ " + _fmt_num(r["avg_salary"]),
                 "total_workers": _fmt_num(r["total_workers"])}
                for r in results
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 259: exposure-by-5-regions
# ═══════════════════════════════════════════════════════════════════════════════

def _exposure_by_5_regions(data, summary):
    por_uf = summary.get("por_uf", {})
    results = []
    for region, codes in _REGIONS.items():
        total_w = 0
        weighted_exp = 0
        for code in codes:
            info = por_uf.get(code, {})
            w = info.get("total_workers", 0)
            e = info.get("avg_exposicao", 0)
            if w and e:
                weighted_exp += e * w
                total_w += w
        avg_exp = round(weighted_exp / total_w, 1) if total_w else 0
        results.append({"region": region, "avg_exposicao": avg_exp, "total_workers": total_w})
    results.sort(key=lambda r: r["avg_exposicao"], reverse=True)
    return {
        "headline_stat": str(results[0]["avg_exposicao"]).replace(".", ",") if results else "N/D",
        "headline_label": f"exposição média ponderada — {results[0]['region']}" if results else "",
        "chart_data": [
            {"label": r["region"], "value": r["avg_exposicao"],
             "formatted": str(r["avg_exposicao"]).replace(".", ",")}
            for r in results
        ],
        "details": {
            "regions": [
                {"region": r["region"], "avg_exposicao": str(r["avg_exposicao"]).replace(".", ","),
                 "total_workers": _fmt_num(r["total_workers"])}
                for r in results
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 260: women-salary-structure
# ═══════════════════════════════════════════════════════════════════════════════

def _women_salary_structure(data, summary):
    fem_occs = []
    masc_occs = []
    for o in data:
        dem = o.get("demographics") or {}
        f = dem.get("total_feminino", 0)
        m = dem.get("total_masculino", 0)
        total = f + m
        if not total or o.get("salario") is None:
            continue
        if f / total > 0.6:
            fem_occs.append(o)
        elif m / total > 0.6:
            masc_occs.append(o)
    avg_sal_f = round(_safe_avg([o["salario"] for o in fem_occs])) if fem_occs else 0
    avg_sal_m = round(_safe_avg([o["salario"] for o in masc_occs])) if masc_occs else 0
    gap_pct = round((avg_sal_m - avg_sal_f) / avg_sal_m * 100, 1) if avg_sal_m else 0
    return {
        "headline_stat": _fmt_pct(abs(gap_pct)),
        "headline_label": "diferença salarial entre ocupações femininas e masculinas",
        "chart_data": [
            {"label": "Ocupações >60% femininas", "value": avg_sal_f,
             "formatted": "R$ " + _fmt_num(avg_sal_f)},
            {"label": "Ocupações >60% masculinas", "value": avg_sal_m,
             "formatted": "R$ " + _fmt_num(avg_sal_m)},
        ],
        "details": {
            "avg_salary_fem": "R$ " + _fmt_num(avg_sal_f),
            "avg_salary_masc": "R$ " + _fmt_num(avg_sal_m),
            "gap_pct": _fmt_pct(abs(gap_pct)),
            "count_fem": str(len(fem_occs)),
            "count_masc": str(len(masc_occs)),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 261: race-occupational-profile
# ═══════════════════════════════════════════════════════════════════════════════

def _race_occupational_profile(data, summary):
    branca_occs = []
    negra_occs = []
    for o in data:
        dem = o.get("demographics") or {}
        b = dem.get("total_branca", 0)
        n = dem.get("total_negra", 0)
        total = b + n
        if not total:
            continue
        if b / total > 0.6:
            branca_occs.append(o)
        elif n / total > 0.6:
            negra_occs.append(o)
    avg_sal_b = round(_safe_avg([o["salario"] for o in branca_occs if o.get("salario")])) if branca_occs else 0
    avg_sal_n = round(_safe_avg([o["salario"] for o in negra_occs if o.get("salario")])) if negra_occs else 0
    avg_exp_b = round(_safe_avg([o["exposicao"] for o in branca_occs if o.get("exposicao") is not None]), 1)
    avg_exp_n = round(_safe_avg([o["exposicao"] for o in negra_occs if o.get("exposicao") is not None]), 1)
    return {
        "headline_stat": "R$ " + _fmt_num(avg_sal_b) + " vs R$ " + _fmt_num(avg_sal_n),
        "headline_label": "salário médio: ocupações >60% branca vs >60% negra",
        "chart_data": [
            {"label": ">60% branca — salário", "value": avg_sal_b,
             "formatted": "R$ " + _fmt_num(avg_sal_b)},
            {"label": ">60% negra — salário", "value": avg_sal_n,
             "formatted": "R$ " + _fmt_num(avg_sal_n)},
        ],
        "details": {
            "avg_salary_branca": "R$ " + _fmt_num(avg_sal_b),
            "avg_salary_negra": "R$ " + _fmt_num(avg_sal_n),
            "avg_exposicao_branca": str(avg_exp_b).replace(".", ","),
            "avg_exposicao_negra": str(avg_exp_n).replace(".", ","),
            "count_branca": str(len(branca_occs)),
            "count_negra": str(len(negra_occs)),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 262: technology-adoption-ready
# ═══════════════════════════════════════════════════════════════════════════════

def _technology_adoption_ready(data, summary):
    matches = [o for o in data
               if o.get("vantagem") is not None and o["vantagem"] >= 7
               and o.get("exposicao") is not None and 4 <= o["exposicao"] <= 6]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    return {
        "headline_stat": str(len(matches)),
        "headline_label": "ocupações prontas para adoção de IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0,
             "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in matches[:10]
        ],
        "details": {
            "count": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "empregados": _fmt_num(o.get("empregados") or 0),
                 "vantagem": str(o.get("vantagem", "")).replace(".", ","),
                 "exposicao": str(o.get("exposicao", "")).replace(".", ",")}
                for o in matches[:10]
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 263: most-volatile-occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _most_volatile_occupations(data, summary):
    valid = [o for o in data
             if o.get("saldo") is not None and o.get("empregados") and o["empregados"] >= 1000]
    for o in valid:
        o["_vol"] = abs(o["saldo"]) / o["empregados"]
    valid.sort(key=lambda o: o["_vol"], reverse=True)
    top10 = valid[:10]
    return {
        "headline_stat": str(round(top10[0]["_vol"] * 100, 1)).replace(".", ",") + "%" if top10 else "N/D",
        "headline_label": "volatilidade máxima (|saldo|/empregados)",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": round(o["_vol"] * 100, 1),
             "formatted": str(round(o["_vol"] * 100, 1)).replace(".", ",") + "%"}
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o.get("titulo", ""),
                 "volatilidade": str(round(o["_vol"] * 100, 1)).replace(".", ",") + "%",
                 "saldo": _fmt_num(o["saldo"]), "empregados": _fmt_num(o["empregados"])}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 264: most-stable-occupations
# ═══════════════════════════════════════════════════════════════════════════════

def _most_stable_occupations(data, summary):
    valid = [o for o in data
             if o.get("saldo") is not None and o.get("empregados") and o["empregados"] >= 5000]
    for o in valid:
        o["_stab"] = abs(o["saldo"]) / o["empregados"]
    valid.sort(key=lambda o: o["_stab"])
    top10 = valid[:10]
    return {
        "headline_stat": str(round(top10[0]["_stab"] * 100, 2)).replace(".", ",") + "%" if top10 else "N/D",
        "headline_label": "menor volatilidade (|saldo|/empregados)",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": round(o["_stab"] * 100, 2),
             "formatted": str(round(o["_stab"] * 100, 2)).replace(".", ",") + "%"}
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o.get("titulo", ""),
                 "volatilidade": str(round(o["_stab"] * 100, 2)).replace(".", ",") + "%",
                 "saldo": _fmt_num(o["saldo"]), "empregados": _fmt_num(o["empregados"])}
                for o in top10
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 265: education-premium-analysis
# ═══════════════════════════════════════════════════════════════════════════════

def _education_premium_analysis(data, summary):
    by_edu = {}
    for o in data:
        esc = o.get("escolaridade")
        if not esc or o.get("salario") is None:
            continue
        by_edu.setdefault(esc, []).append(o["salario"])
    results = [{"escolaridade": k, "avg_salary": round(_safe_avg(v)), "count": len(v)}
               for k, v in by_edu.items()]
    results.sort(key=lambda r: r["avg_salary"], reverse=True)
    return {
        "headline_stat": "R$ " + _fmt_num(results[0]["avg_salary"]) if results else "N/D",
        "headline_label": f"salário médio — {results[0]['escolaridade']}" if results else "",
        "chart_data": [
            {"label": r["escolaridade"], "value": r["avg_salary"],
             "formatted": "R$ " + _fmt_num(r["avg_salary"])}
            for r in results
        ],
        "details": {
            "levels": [
                {"escolaridade": r["escolaridade"], "avg_salary": "R$ " + _fmt_num(r["avg_salary"]),
                 "count": str(r["count"])}
                for r in results
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 266: exposure-by-escolaridade-cross
# ═══════════════════════════════════════════════════════════════════════════════

def _exposure_by_escolaridade_cross(data, summary):
    tiers = {"baixa (0-3)": (0, 3), "média (4-6)": (4, 6), "alta (7-10)": (7, 10)}
    cross = {}
    for o in data:
        esc = o.get("escolaridade")
        exp = o.get("exposicao")
        if not esc or exp is None:
            continue
        for tier_name, (lo, hi) in tiers.items():
            if lo <= exp <= hi:
                key = f"{esc} × {tier_name}"
                cross[key] = cross.get(key, 0) + 1
                break
    # Build structured output by education level
    edu_levels = {}
    for o in data:
        esc = o.get("escolaridade")
        if esc:
            edu_levels[esc] = True
    rows = []
    for esc in sorted(edu_levels.keys()):
        row = {"escolaridade": esc}
        for tier_name in tiers:
            key = f"{esc} × {tier_name}"
            row[tier_name] = cross.get(key, 0)
        rows.append(row)
    total = sum(cross.values()) or 1
    return {
        "headline_stat": str(len(cross)),
        "headline_label": "combinações educação × exposição encontradas",
        "chart_data": [
            {"label": k, "value": v, "formatted": str(v)}
            for k, v in sorted(cross.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
        "details": {
            "cross_table": [
                {"escolaridade": r["escolaridade"],
                 "baixa": str(r.get("baixa (0-3)", 0)),
                 "media": str(r.get("média (4-6)", 0)),
                 "alta": str(r.get("alta (7-10)", 0))}
                for r in rows
            ],
            "total_occupations": str(total),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 267: health-ai-opportunity-focus
# ═══════════════════════════════════════════════════════════════════════════════

def _health_ai_opportunity_focus(data, summary):
    health_kw = ["médic", "saúde", "enfermeir", "fisioterapeut", "nutricion",
                 "farmac", "dentist", "odont", "hospitalar", "clínic"]
    matches = [o for o in data
               if any(kw in o.get("titulo", "").lower() for kw in health_kw)
               and o.get("oportunidade") is not None]
    matches.sort(key=lambda o: o["oportunidade"], reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(round(top10[0]["oportunidade"], 1)).replace(".", ",") if top10 else "N/D",
        "headline_label": "oportunidade máxima em saúde",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["oportunidade"],
             "formatted": str(round(o["oportunidade"], 1)).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o.get("titulo", ""),
                 "oportunidade": str(round(o["oportunidade"], 1)).replace(".", ","),
                 "exposicao": str(o.get("exposicao", "N/D")).replace(".", ","),
                 "empregados": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
            "total_health": str(len(matches)),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 268: education-ai-transformation
# ═══════════════════════════════════════════════════════════════════════════════

def _education_ai_transformation(data, summary):
    matches = [o for o in data
               if "professor" in o.get("titulo", "").lower()
               and o.get("oportunidade") is not None]
    matches.sort(key=lambda o: o["oportunidade"], reverse=True)
    avg_opp = round(_safe_avg([o["oportunidade"] for o in matches]), 1)
    top10 = matches[:10]
    return {
        "headline_stat": str(avg_opp).replace(".", ","),
        "headline_label": "oportunidade média para professores com IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["oportunidade"],
             "formatted": str(round(o["oportunidade"], 1)).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o.get("titulo", ""),
                 "oportunidade": str(round(o["oportunidade"], 1)).replace(".", ","),
                 "exposicao": str(o.get("exposicao", "N/D")).replace(".", ","),
                 "empregados": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
            "total_professors": str(len(matches)),
            "avg_oportunidade": str(avg_opp).replace(".", ","),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 269: legal-ai-disruption-depth
# ═══════════════════════════════════════════════════════════════════════════════

def _legal_ai_disruption_depth(data, summary):
    legal_kw = ["advogad", "jurídic", "juiz", "tabeliã", "cartorár"]
    matches = [o for o in data
               if any(kw in o.get("titulo", "").lower() for kw in legal_kw)
               and o.get("exposicao") is not None]
    matches.sort(key=lambda o: o["exposicao"], reverse=True)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    nat_avg = round(_safe_avg([o["exposicao"] for o in data if o.get("exposicao") is not None]), 1)
    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": "exposição média do setor jurídico",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["exposicao"],
             "formatted": str(o["exposicao"]).replace(".", ",")}
            for o in matches[:10]
        ],
        "details": {
            "occupations": [
                {"titulo": o.get("titulo", ""),
                 "exposicao": str(o["exposicao"]).replace(".", ","),
                 "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D",
                 "empregados": _fmt_num(o.get("empregados") or 0)}
                for o in matches
            ],
            "avg_exposicao_legal": str(avg_exp).replace(".", ","),
            "avg_exposicao_national": str(nat_avg).replace(".", ","),
            "total_legal": str(len(matches)),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 270: finance-ai-adoption
# ═══════════════════════════════════════════════════════════════════════════════

def _finance_ai_adoption(data, summary):
    fin_kw = ["contab", "financ", "banc", "audit"]
    matches = [o for o in data
               if any(kw in o.get("titulo", "").lower() for kw in fin_kw)
               and o.get("vantagem") is not None]
    matches.sort(key=lambda o: o["vantagem"], reverse=True)
    avg_van = round(_safe_avg([o["vantagem"] for o in matches]), 1)
    nat_avg = round(_safe_avg([o["vantagem"] for o in data if o.get("vantagem") is not None]), 1)
    diff = round(avg_van - nat_avg, 1)
    return {
        "headline_stat": str(avg_van).replace(".", ","),
        "headline_label": "vantagem média do setor financeiro com IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["vantagem"],
             "formatted": str(o["vantagem"]).replace(".", ",")}
            for o in matches[:10]
        ],
        "details": {
            "occupations": [
                {"titulo": o.get("titulo", ""),
                 "vantagem": str(o["vantagem"]).replace(".", ","),
                 "exposicao": str(o.get("exposicao", "N/D")).replace(".", ","),
                 "empregados": _fmt_num(o.get("empregados") or 0)}
                for o in matches
            ],
            "avg_vantagem_finance": str(avg_van).replace(".", ","),
            "avg_vantagem_national": str(nat_avg).replace(".", ","),
            "diff": ("+" if diff >= 0 else "") + str(diff).replace(".", ","),
            "total_finance": str(len(matches)),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template 271: agriculture-ai-future
# ═══════════════════════════════════════════════════════════════════════════════

def _agriculture_ai_future(data, summary):
    matches = [o for o in data
               if o.get("grande_grupo") and "agro" in o["grande_grupo"].lower()
               and (o.get("oportunidade") is not None or o.get("crescimento") is not None)]
    matches.sort(key=lambda o: (o.get("oportunidade") or 0), reverse=True)
    avg_opp = round(_safe_avg([o["oportunidade"] for o in matches if o.get("oportunidade") is not None]), 1)
    avg_cresc = round(_safe_avg([o["crescimento"] for o in matches if o.get("crescimento") is not None]), 1)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    top10 = matches[:10]
    return {
        "headline_stat": str(avg_opp).replace(".", ","),
        "headline_label": "oportunidade média no agronegócio",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("oportunidade") or 0,
             "formatted": str(round(o.get("oportunidade") or 0, 1)).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o.get("titulo", ""),
                 "oportunidade": str(round(o.get("oportunidade") or 0, 1)).replace(".", ","),
                 "crescimento": str(o.get("crescimento", "N/D")).replace(".", ","),
                 "empregados": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
            "avg_oportunidade": str(avg_opp).replace(".", ","),
            "avg_crescimento": str(avg_cresc).replace(".", ","),
            "total_workers": _fmt_num(total_w),
            "total_occupations": str(len(matches)),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template list
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES_BATCH_D1 = [
    # 247
    {
        "id": "salary-exposure-quartiles",
        "category": "Mercado",
        "tags": ["salário", "exposição", "quartil", "comparativo"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_exposure_quartiles,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a relação entre faixa salarial e exposição à IA no Brasil, dividindo as ocupações em quartis.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações analisadas: {total_occupations}
- Quartis salariais: {quartiles}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 248
    {
        "id": "salary-vantagem-quartiles",
        "category": "Mercado",
        "tags": ["salário", "vantagem", "quartil", "comparativo"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_vantagem_quartiles,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a vantagem com IA varia por faixa salarial no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {total_occupations}
- Quartis salariais com vantagem média: {quartiles}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 249
    {
        "id": "regional-salary-inequality",
        "category": "Regional",
        "tags": ["estados", "salário", "desigualdade", "regional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _regional_salary_inequality,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a desigualdade salarial entre estados brasileiros no contexto da IA.

DADOS (use APENAS estes números, não invente dados):
- Razão maior/menor salário médio: {ratio}x
- Top 5 estados por salário: {top5}
- Bottom 5 estados por salário: {bottom5}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 250
    {
        "id": "regional-exposure-spread",
        "category": "Regional",
        "tags": ["estados", "exposição", "dispersão", "regional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _regional_exposure_spread,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a dispersão da exposição à IA entre os estados brasileiros.

DADOS (use APENAS estes números, não invente dados):
- Amplitude (max - min): {spread}
- Estado líder: {top_state} ({top_score})
- Estado menor: {bottom_state} ({bottom_score})
- Todos os estados: {all_states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 251
    {
        "id": "top-50-employers-profile",
        "category": "Mercado",
        "tags": ["empregadores", "concentração", "mercado"],
        "chart_type": "ranking_table",
        "analysis_fn": _top_50_employers_profile,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o perfil das 50 maiores ocupações por número de empregados no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores nas top 50: {total_top50} ({pct_workforce} do total nacional de {total_national})
- Exposição média à IA: {avg_exposicao}
- Salário médio: {avg_salary}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 252
    {
        "id": "smallest-occupations",
        "category": "Ocupações",
        "tags": ["micro-ocupações", "nicho", "ocupações"],
        "chart_type": "ranking_table",
        "analysis_fn": _smallest_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as menores ocupações do Brasil e como a IA as afeta.

DADOS (use APENAS estes números, não invente dados):
- Exposição média: {avg_exposicao}
- Salário médio: {avg_salary}
- Ocupações: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 253
    {
        "id": "saldo-per-thousand",
        "category": "Mercado",
        "tags": ["saldo", "crescimento", "normalizado", "mercado"],
        "chart_type": "ranking_table",
        "analysis_fn": _saldo_per_thousand,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com maior taxa de crescimento normalizada (saldo por mil empregados).

DADOS (use APENAS estes números, não invente dados):
- Top 10 ocupações por saldo/mil empregados: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 254
    {
        "id": "hiring-efficiency",
        "category": "Mercado",
        "tags": ["admissões", "saldo", "eficiência", "mercado"],
        "chart_type": "ranking_table",
        "analysis_fn": _hiring_efficiency,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações onde a maior proporção das contratações se converte em crescimento líquido.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por eficiência de contratação (saldo/admissões): {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 255
    {
        "id": "occupations-missing-salary",
        "category": "Mercado",
        "tags": ["dados", "lacunas", "qualidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _occupations_missing_salary,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as lacunas nos dados do mercado de trabalho brasileiro e o que elas revelam.

DADOS (use APENAS estes números, não invente dados):
- Ocupações sem salário: {no_salary} de {total} ({pct_no_salary})
- Ocupações sem empregados: {no_empregados}
- Sem ambos os dados: {both_missing}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 256
    {
        "id": "data-completeness",
        "category": "Mercado",
        "tags": ["dados", "completude", "qualidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _data_completeness,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a completude dos dados ocupacionais brasileiros (empregados, salário, saldo, admissões, salário de admissão).

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {total}
- Distribuição por campos preenchidos: {breakdown}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 257
    {
        "id": "most-common-subgrupo",
        "category": "Setores",
        "tags": ["subgrupo", "concentração", "setores"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _most_common_subgrupo,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre quais subgrupos ocupacionais concentram mais profissões no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Total de subgrupos distintos: {total_subgrupos}
- Top 10 subgrupos por número de ocupações: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 258
    {
        "id": "salary-by-5-regions",
        "category": "Regional",
        "tags": ["regiões", "salário", "regional", "macro"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _salary_by_5_regions,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as diferenças salariais entre as 5 macrorregiões brasileiras.

DADOS (use APENAS estes números, não invente dados):
- Salário médio ponderado por região: {regions}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 259
    {
        "id": "exposure-by-5-regions",
        "category": "Regional",
        "tags": ["regiões", "exposição", "regional", "macro"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _exposure_by_5_regions,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a exposição à IA varia entre as 5 macrorregiões do Brasil.

DADOS (use APENAS estes números, não invente dados):
- Exposição média ponderada por região: {regions}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 260
    {
        "id": "women-salary-structure",
        "category": "Demografia",
        "tags": ["gênero", "salário", "feminino", "comparativo"],
        "chart_type": "comparison_pair",
        "analysis_fn": _women_salary_structure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença salarial entre ocupações predominantemente femininas e masculinas no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Salário médio em ocupações >60%% femininas: {avg_salary_fem} ({count_fem} ocupações)
- Salário médio em ocupações >60%% masculinas: {avg_salary_masc} ({count_masc} ocupações)
- Diferença: {gap_pct}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 261
    {
        "id": "race-occupational-profile",
        "category": "Demografia",
        "tags": ["raça", "salário", "exposição", "comparativo"],
        "chart_type": "comparison_pair",
        "analysis_fn": _race_occupational_profile,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o perfil ocupacional comparado por raça no Brasil, analisando salário e exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Ocupações >60%% branca: salário médio {avg_salary_branca}, exposição {avg_exposicao_branca} ({count_branca} ocupações)
- Ocupações >60%% negra: salário médio {avg_salary_negra}, exposição {avg_exposicao_negra} ({count_negra} ocupações)

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 262
    {
        "id": "technology-adoption-ready",
        "category": "Setores",
        "tags": ["adoção", "vantagem", "exposição", "oportunidade"],
        "chart_type": "ranking_table",
        "analysis_fn": _technology_adoption_ready,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações prontas para adotar IA — alta vantagem mas exposição moderada.

DADOS (use APENAS estes números, não invente dados):
- Ocupações com vantagem ≥7 e exposição 4-6: {count}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 263
    {
        "id": "most-volatile-occupations",
        "category": "Mercado",
        "tags": ["volatilidade", "saldo", "instabilidade"],
        "chart_type": "ranking_table",
        "analysis_fn": _most_volatile_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações mais voláteis do mercado de trabalho brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por volatilidade (|saldo|/empregados): {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 264
    {
        "id": "most-stable-occupations",
        "category": "Mercado",
        "tags": ["estabilidade", "saldo", "segurança"],
        "chart_type": "ranking_table",
        "analysis_fn": _most_stable_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações mais estáveis do mercado de trabalho brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por estabilidade (menor |saldo|/empregados, mín. 5.000 empregados): {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 265
    {
        "id": "education-premium-analysis",
        "category": "Educação",
        "tags": ["escolaridade", "salário", "prêmio educacional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _education_premium_analysis,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o prêmio salarial por nível de escolaridade no Brasil. Mais educação significa mais salário?

DADOS (use APENAS estes números, não invente dados):
- Salário médio por nível de escolaridade: {levels}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 266
    {
        "id": "exposure-by-escolaridade-cross",
        "category": "Educação",
        "tags": ["escolaridade", "exposição", "cruzamento"],
        "chart_type": "ranking_table",
        "analysis_fn": _exposure_by_escolaridade_cross,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o cruzamento entre nível de escolaridade e exposição à IA. Quem é mais vulnerável?

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações: {total_occupations}
- Tabela cruzada (educação × exposição baixa/média/alta): {cross_table}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 267
    {
        "id": "health-ai-opportunity-focus",
        "category": "Setores",
        "tags": ["saúde", "oportunidade", "setor"],
        "chart_type": "ranking_table",
        "analysis_fn": _health_ai_opportunity_focus,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as oportunidades da IA no setor de saúde brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações de saúde: {total_health}
- Top 10 por oportunidade: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 268
    {
        "id": "education-ai-transformation",
        "category": "Educação",
        "tags": ["professor", "ensino", "oportunidade", "transformação"],
        "chart_type": "ranking_table",
        "analysis_fn": _education_ai_transformation,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a IA pode transformar o ensino no Brasil. Onde a IA mais ajuda os professores?

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações de professor: {total_professors}
- Oportunidade média: {avg_oportunidade}
- Top 10 por oportunidade: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 269
    {
        "id": "legal-ai-disruption-depth",
        "category": "Setores",
        "tags": ["jurídico", "exposição", "disrupção", "setor"],
        "chart_type": "ranking_table",
        "analysis_fn": _legal_ai_disruption_depth,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a profundidade da disrupção da IA no setor jurídico brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações jurídicas: {total_legal}
- Exposição média jurídica: {avg_exposicao_legal} vs nacional: {avg_exposicao_national}
- Ocupações ordenadas por exposição: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 270
    {
        "id": "finance-ai-adoption",
        "category": "Setores",
        "tags": ["financeiro", "vantagem", "adoção", "setor"],
        "chart_type": "ranking_table",
        "analysis_fn": _finance_ai_adoption,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o setor financeiro como líder na adoção de IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações financeiras: {total_finance}
- Vantagem média financeira: {avg_vantagem_finance} vs nacional: {avg_vantagem_national} (diferença: {diff})
- Ocupações: {occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 271
    {
        "id": "agriculture-ai-future",
        "category": "Setores",
        "tags": ["agronegócio", "oportunidade", "crescimento", "setor"],
        "chart_type": "ranking_table",
        "analysis_fn": _agriculture_ai_future,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o futuro da agricultura com IA no Brasil. Foque em oportunidade e crescimento.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações agrícolas: {total_occupations}
- Total de trabalhadores: {total_workers}
- Oportunidade média: {avg_oportunidade}
- Crescimento médio: {avg_crescimento}
- Top 10 por oportunidade: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates_batch_d1():
    return TEMPLATES_BATCH_D1
