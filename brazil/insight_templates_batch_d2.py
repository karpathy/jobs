"""Insight templates batch D2: future-oriented + summary stories."""
import statistics
from insight_templates import _fmt_pct, _fmt_num, _safe_avg


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: keyword-based sector filter
# ═══════════════════════════════════════════════════════════════════════════════

def _keyword_filter(data, keywords):
    """Return occupations whose titulo contains any keyword (case-insensitive)."""
    matches = []
    for o in data:
        titulo = o.get("titulo", "").lower()
        if any(kw in titulo for kw in keywords):
            matches.append(o)
    return matches


# ─── 272: construction-ai-lag ────────────────────────────────────────────────

def _construction_ai_lag(data, summary):
    keywords = ["constru", "pedreiro", "eletricist", "encanad", "pintor de obra"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top8 = matches[:8]
    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": "exposição média — construção resiste à IA",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 273: transport-ai-revolution ────────────────────────────────────────────

def _transport_ai_revolution(data, summary):
    keywords = ["motorist", "transport", "caminhoneir", "piloto"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_cresc = round(_safe_avg([o.get("crescimento") for o in matches if o.get("crescimento") is not None]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores — exposição média {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_crescimento": str(avg_cresc).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 274: creative-ai-paradox ────────────────────────────────────────────────

def _creative_ai_paradox(data, summary):
    keywords = ["artist", "design", "músic", "fotógraf", "publicit", "ator", "cineasta"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("exposicao") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_van = round(_safe_avg([o.get("vantagem") for o in matches if o.get("vantagem") is not None]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top8 = matches[:8]
    return {
        "headline_stat": str(avg_exp).replace(".", ","),
        "headline_label": f"exposição vs {str(avg_van).replace('.', ',')} vantagem — o paradoxo criativo",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_vantagem": str(avg_van).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "exposicao": str(o.get("exposicao", 0)).replace(".", ","), "vantagem": str(o.get("vantagem", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 275: retail-ai-transformation ───────────────────────────────────────────

def _retail_ai_transformation(data, summary):
    matches = []
    for o in data:
        gg = (o.get("grande_grupo") or "").upper()
        titulo = o.get("titulo", "").lower()
        if "vendedor" in gg.lower() or "serviços, vendedores" in gg.lower() or "vendedor" in titulo:
            matches.append(o)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_saldo = round(_safe_avg([o.get("saldo") for o in matches if o.get("saldo") is not None]))
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores no varejo — exposição {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_saldo": _fmt_num(avg_saldo),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 276: security-ai-impact ─────────────────────────────────────────────────

def _security_ai_impact(data, summary):
    keywords = ["vigilant", "seguranç", "guarda"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top8 = matches[:8]
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores em segurança — exposição {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 277: brazil-workforce-snapshot ──────────────────────────────────────────

def _brazil_workforce_snapshot(data, summary):
    valid = [o for o in data if o.get("exposicao") is not None]
    total_occs = len(valid)
    total_w = sum(o.get("empregados") or 0 for o in valid)
    avg_sal = round(_safe_avg([o["salario"] for o in valid if o.get("salario")])) if any(o.get("salario") for o in valid) else 0
    avg_exp = round(_safe_avg([o["exposicao"] for o in valid]), 1)
    avg_van = round(_safe_avg([o.get("vantagem") for o in valid if o.get("vantagem") is not None]), 1)
    avg_cresc = round(_safe_avg([o.get("crescimento") for o in valid if o.get("crescimento") is not None]), 1)
    avg_oport = round(_safe_avg([o.get("oportunidade") for o in valid if o.get("oportunidade") is not None]), 1)
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores em {total_occs} ocupações analisadas",
        "chart_data": [
            {"label": "Exposição média", "value": avg_exp, "formatted": str(avg_exp).replace(".", ",")},
            {"label": "Vantagem média", "value": avg_van, "formatted": str(avg_van).replace(".", ",")},
            {"label": "Crescimento médio", "value": avg_cresc, "formatted": str(avg_cresc).replace(".", ",")},
            {"label": "Oportunidade média", "value": avg_oport, "formatted": str(avg_oport).replace(".", ",")},
        ],
        "details": {
            "total_occupations": str(total_occs),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_vantagem": str(avg_van).replace(".", ","),
            "avg_crescimento": str(avg_cresc).replace(".", ","),
            "avg_oportunidade": str(avg_oport).replace(".", ","),
        },
    }


# ─── 278: demographic-entry-risk ─────────────────────────────────────────────

def _demographic_entry_risk(data, summary):
    candidates = [o for o in data if o.get("admissoes") and o.get("exposicao") is not None and o["exposicao"] >= 7]
    candidates.sort(key=lambda o: o["admissoes"], reverse=True)
    top10 = candidates[:10]
    if not top10:
        return {"headline_stat": "0", "headline_label": "ocupações de risco com admissões", "chart_data": [], "details": {}}
    total_admissoes = sum(o["admissoes"] for o in top10)
    total_w = sum(o.get("empregados") or 0 for o in top10)
    return {
        "headline_stat": _fmt_num(total_admissoes),
        "headline_label": "admissões nas 10 ocupações de alto risco mais contratadas",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["admissoes"], "formatted": _fmt_num(o["admissoes"])}
            for o in top10
        ],
        "details": {
            "total_admissoes": _fmt_num(total_admissoes),
            "total_workers": _fmt_num(total_w),
            "num_high_risk": str(len(candidates)),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "admissoes": _fmt_num(o["admissoes"]), "exposicao": str(o["exposicao"]).replace(".", ",")}
                for o in top10
            ],
        },
    }


# ─── 279: export-sectors ─────────────────────────────────────────────────────

def _export_sectors(data, summary):
    keywords = ["exportaç", "comércio exterior", "portuári", "navegaç"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if len(matches) < 3:
        fallback_kw = ["transport", "logístic"]
        extra = _keyword_filter(data, fallback_kw)
        extra = [o for o in extra if o.get("exposicao") is not None and o not in matches]
        matches.extend(extra)
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top8 = matches[:8]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupações ligadas a exportação — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("exposicao", 0), "formatted": str(o.get("exposicao", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 280: green-jobs ─────────────────────────────────────────────────────────

def _green_jobs(data, summary):
    keywords = ["ambiental", "florestal", "reciclage", "sustentab", "energia", "saneament"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_oport = round(_safe_avg([o.get("oportunidade") for o in matches if o.get("oportunidade") is not None]), 1)
    top8 = matches[:8]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"empregos verdes — oportunidade média {str(avg_oport).replace('.', ',')}",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("oportunidade") or 0, "formatted": str(o.get("oportunidade", 0)).replace(".", ",")}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_oportunidade": str(avg_oport).replace(".", ","),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ","), "oportunidade": str(o.get("oportunidade", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 281: ai-augmented-elite ─────────────────────────────────────────────────

def _ai_augmented_elite(data, summary):
    matches = [
        o for o in data
        if o.get("exposicao") is not None
        and 5 <= o["exposicao"] <= 8
        and (o.get("vantagem") or 0) >= 8
        and (o.get("salario") or 0) >= 8000
    ]
    if not matches:
        return {"headline_stat": "0", "headline_label": "profissionais da elite IA", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("salario") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"profissionais potencializados pela IA — salário médio R$ {_fmt_num(avg_sal)}",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("salario") or 0, "formatted": "R$ " + _fmt_num(round(o.get("salario") or 0))}
            for o in top10
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "occupations_list": [
                {"titulo": o.get("titulo", ""), "salario": "R$ " + _fmt_num(round(o.get("salario") or 0)), "exposicao": str(o.get("exposicao", 0)).replace(".", ","), "vantagem": str(o.get("vantagem", 0)).replace(".", ",")}
                for o in top10
            ],
        },
    }


# ─── 282: informal-economy-proxy ─────────────────────────────────────────────

def _informal_economy_proxy(data, summary):
    matches = [
        o for o in data
        if o.get("salario") is not None and o["salario"] < 1500 and o.get("empregados")
    ]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações de baixo salário", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    top_setores = {}
    for o in matches:
        gg = o.get("grande_grupo") or "Outros"
        top_setores[gg] = top_setores.get(gg, 0) + (o.get("empregados") or 0)
    setores_sorted = sorted(top_setores.items(), key=lambda x: x[1], reverse=True)[:5]
    top8 = matches[:8]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupações com salário < R$ 1.500 — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top8
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "top_setores": [{"setor": s, "workers": _fmt_num(w)} for s, w in setores_sorted],
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "salario": "R$ " + _fmt_num(round(o.get("salario") or 0))}
                for o in top8
            ],
        },
    }


# ─── 283: public-private-contrast ────────────────────────────────────────────

def _public_private_contrast(data, summary):
    keywords = ["dirigent", "serviço público", "gestor público", "magistrad"]
    matches = _keyword_filter(data, keywords)
    matches = [o for o in matches if o.get("exposicao") is not None]
    all_valid = [o for o in data if o.get("exposicao") is not None]
    nat_avg_exp = round(_safe_avg([o["exposicao"] for o in all_valid]), 1)
    nat_avg_sal = round(_safe_avg([o["salario"] for o in all_valid if o.get("salario")])) if any(o.get("salario") for o in all_valid) else 0
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações públicas encontradas", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("salario") or 0), reverse=True)
    avg_exp_pub = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    avg_sal_pub = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top8 = matches[:8]
    return {
        "headline_stat": "R$ " + _fmt_num(avg_sal_pub),
        "headline_label": f"salário médio público vs R$ {_fmt_num(nat_avg_sal)} nacional",
        "chart_data": [
            {"label": "Setor público", "value": avg_exp_pub, "formatted": str(avg_exp_pub).replace(".", ",")},
            {"label": "Média nacional", "value": nat_avg_exp, "formatted": str(nat_avg_exp).replace(".", ",")},
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "avg_exposicao_public": str(avg_exp_pub).replace(".", ","),
            "avg_exposicao_national": str(nat_avg_exp).replace(".", ","),
            "avg_salary_public": "R$ " + _fmt_num(avg_sal_pub),
            "avg_salary_national": "R$ " + _fmt_num(nat_avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "salario": "R$ " + _fmt_num(round(o.get("salario") or 0)), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top8
            ],
        },
    }


# ─── 284: occupation-name-length ─────────────────────────────────────────────

def _occupation_name_length(data, summary):
    valid = [o for o in data if o.get("titulo") and o.get("exposicao") is not None]
    valid.sort(key=lambda o: len(o["titulo"]), reverse=True)
    top10 = valid[:10]
    if not top10:
        return {"headline_stat": "0", "headline_label": "ocupações", "chart_data": [], "details": {}}
    longest = top10[0]
    return {
        "headline_stat": str(len(longest["titulo"])),
        "headline_label": "caracteres no título mais longo",
        "chart_data": [
            {"label": o["titulo"][:50] + "…" if len(o["titulo"]) > 50 else o["titulo"], "value": len(o["titulo"]), "formatted": str(len(o["titulo"]))}
            for o in top10
        ],
        "details": {
            "longest_title": longest["titulo"],
            "longest_chars": str(len(longest["titulo"])),
            "longest_exposicao": str(longest.get("exposicao", 0)).replace(".", ","),
            "top_occupations": [
                {"titulo": o["titulo"], "chars": str(len(o["titulo"])), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top10
            ],
        },
    }


# ─── 285: most-workers-single-state ──────────────────────────────────────────

def _most_workers_single_state(data, summary):
    best_occ = None
    best_uf = None
    best_pct = 0
    best_ativos = 0
    for o in data:
        por_uf = o.get("por_uf")
        emp = o.get("empregados") or 0
        if not por_uf or emp == 0:
            continue
        for uf_code, uf_data in por_uf.items():
            ativos = uf_data.get("ativos") or uf_data.get("total", 0)
            if ativos and emp > 0:
                pct = ativos / emp
                if pct > best_pct:
                    best_pct = pct
                    best_occ = o
                    best_uf = summary["por_uf"].get(uf_code, {}).get("nome", uf_code)
                    best_ativos = ativos
    if not best_occ:
        return {"headline_stat": "N/D", "headline_label": "dados insuficientes", "chart_data": [], "details": {}}
    return {
        "headline_stat": _fmt_pct(round(best_pct * 100, 1)),
        "headline_label": f"de {best_occ['titulo']} concentrados em {best_uf}",
        "chart_data": [
            {"label": best_occ.get("titulo", ""), "value": round(best_pct * 100, 1), "formatted": _fmt_pct(round(best_pct * 100, 1))},
        ],
        "details": {
            "occupation": best_occ.get("titulo", ""),
            "state": best_uf,
            "state_workers": _fmt_num(best_ativos),
            "total_workers": _fmt_num(best_occ.get("empregados") or 0),
            "concentration_pct": _fmt_pct(round(best_pct * 100, 1)),
        },
    }


# ─── 286: salary-above-20k ──────────────────────────────────────────────────

def _salary_above_20k(data, summary):
    matches = [o for o in data if o.get("salario") is not None and o["salario"] >= 20000]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações com salário ≥ R$ 20.000", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: o["salario"], reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupações pagam R$ 20.000+ — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["salario"], "formatted": "R$ " + _fmt_num(round(o["salario"]))}
            for o in top10
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "occupations_list": [
                {"titulo": o.get("titulo", ""), "salario": "R$ " + _fmt_num(round(o["salario"])), "exposicao": str(o.get("exposicao", "N/D")).replace(".", ",")}
                for o in matches
            ],
        },
    }


# ─── 287: exposure-7-exactly ─────────────────────────────────────────────────

def _exposure_7_exactly(data, summary):
    matches = [o for o in data if o.get("exposicao") == 7]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações com exposição 7", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupações no ponto de inflexão — exposição exata 7",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
        },
    }


# ─── 288: vantagem-10-spotlight ──────────────────────────────────────────────

def _vantagem_10_spotlight(data, summary):
    matches = [o for o in data if o.get("vantagem") == 10]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações com vantagem máxima", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupações com vantagem IA máxima (10/10)",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "occupations_list": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "exposicao": str(o.get("exposicao", 0)).replace(".", ",")}
                for o in top10
            ],
        },
    }


# ─── 289: crescimento-0-spotlight ────────────────────────────────────────────

def _crescimento_0_spotlight(data, summary):
    matches = [o for o in data if o.get("crescimento") is not None and o["crescimento"] <= 1]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações em retração", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupações com demanda em queda — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0), "crescimento": str(o.get("crescimento", 0))}
                for o in top10
            ],
        },
    }


# ─── 290: oportunidade-9-plus ────────────────────────────────────────────────

def _oportunidade_9_plus(data, summary):
    matches = [o for o in data if o.get("oportunidade") is not None and o["oportunidade"] >= 9.0]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações com oportunidade ≥ 9", "chart_data": [], "details": {}}
    matches.sort(key=lambda o: o["oportunidade"], reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupações de máxima oportunidade — salário médio R$ {_fmt_num(avg_sal)}",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o["oportunidade"], "formatted": str(o["oportunidade"]).replace(".", ",")}
            for o in top10
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "occupations_list": [
                {"titulo": o.get("titulo", ""), "oportunidade": str(o["oportunidade"]).replace(".", ","), "salario": "R$ " + _fmt_num(round(o.get("salario") or 0))}
                for o in top10
            ],
        },
    }


# ─── 291: salary-vs-crescimento ──────────────────────────────────────────────

def _salary_vs_crescimento(data, summary):
    high_cresc = [o for o in data if o.get("crescimento") is not None and o["crescimento"] >= 7 and o.get("salario")]
    low_cresc = [o for o in data if o.get("crescimento") is not None and o["crescimento"] <= 3 and o.get("salario")]
    avg_sal_high = round(_safe_avg([o["salario"] for o in high_cresc])) if high_cresc else 0
    avg_sal_low = round(_safe_avg([o["salario"] for o in low_cresc])) if low_cresc else 0
    return {
        "headline_stat": "R$ " + _fmt_num(avg_sal_high),
        "headline_label": f"salário médio (crescimento alto) vs R$ {_fmt_num(avg_sal_low)} (baixo)",
        "chart_data": [
            {"label": "Crescimento ≥ 7", "value": avg_sal_high, "formatted": "R$ " + _fmt_num(avg_sal_high)},
            {"label": "Crescimento ≤ 3", "value": avg_sal_low, "formatted": "R$ " + _fmt_num(avg_sal_low)},
        ],
        "details": {
            "num_high_crescimento": str(len(high_cresc)),
            "num_low_crescimento": str(len(low_cresc)),
            "avg_salary_high": "R$ " + _fmt_num(avg_sal_high),
            "avg_salary_low": "R$ " + _fmt_num(avg_sal_low),
            "diff": "R$ " + _fmt_num(abs(avg_sal_high - avg_sal_low)),
        },
    }


# ─── 292: exposure-by-codigo-prefix ──────────────────────────────────────────

def _exposure_by_codigo_prefix(data, summary):
    groups = {}
    for o in data:
        codigo = o.get("codigo") or o.get("grande_grupo_codigo")
        if not codigo or o.get("exposicao") is None:
            continue
        prefix = str(codigo)[0]
        if prefix not in groups:
            groups[prefix] = {"exposicoes": [], "label": o.get("grande_grupo", prefix)}
        groups[prefix]["exposicoes"].append(o["exposicao"])
    if not groups:
        return {"headline_stat": "0", "headline_label": "grupos", "chart_data": [], "details": {}}
    result = []
    for prefix in sorted(groups.keys()):
        avg = round(_safe_avg(groups[prefix]["exposicoes"]), 1)
        result.append({"prefix": prefix, "label": groups[prefix]["label"], "avg_exposicao": avg, "count": len(groups[prefix]["exposicoes"])})
    result.sort(key=lambda r: r["avg_exposicao"], reverse=True)
    top = result[0]
    return {
        "headline_stat": str(top["avg_exposicao"]).replace(".", ","),
        "headline_label": f"exposição média do grupo {top['prefix']} — {top['label'][:40]}",
        "chart_data": [
            {"label": f"{r['prefix']} - {r['label'][:30]}", "value": r["avg_exposicao"], "formatted": str(r["avg_exposicao"]).replace(".", ",")}
            for r in result
        ],
        "details": {
            "groups": [
                {"prefix": r["prefix"], "label": r["label"], "avg_exposicao": str(r["avg_exposicao"]).replace(".", ","), "num_occupations": str(r["count"])}
                for r in result
            ],
        },
    }


# ─── 293: admissoes-to-saldo-ratio ──────────────────────────────────────────

def _admissoes_to_saldo_ratio(data, summary):
    valid = [o for o in data if o.get("admissoes") and o["admissoes"] > 0 and o.get("saldo") is not None]
    if not valid:
        return {"headline_stat": "N/D", "headline_label": "dados insuficientes", "chart_data": [], "details": {}}
    ratios = [o["saldo"] / o["admissoes"] for o in valid]
    overall = round(statistics.mean(ratios), 3)
    tiers = {"Baixa (0-3)": [], "Média (4-6)": [], "Alta (7-8)": [], "Crítica (9-10)": []}
    for o in valid:
        exp = o.get("exposicao")
        r = o["saldo"] / o["admissoes"]
        if exp is None:
            continue
        if exp <= 3:
            tiers["Baixa (0-3)"].append(r)
        elif exp <= 6:
            tiers["Média (4-6)"].append(r)
        elif exp <= 8:
            tiers["Alta (7-8)"].append(r)
        else:
            tiers["Crítica (9-10)"].append(r)
    tier_results = []
    for label, vals in tiers.items():
        avg = round(statistics.mean(vals), 3) if vals else 0
        tier_results.append({"label": label, "avg_ratio": avg, "count": len(vals)})
    return {
        "headline_stat": str(round(overall * 100, 1)).replace(".", ",") + "%",
        "headline_label": "do saldo líquido em relação às admissões",
        "chart_data": [
            {"label": t["label"], "value": t["avg_ratio"], "formatted": str(round(t["avg_ratio"] * 100, 1)).replace(".", ",") + "%"}
            for t in tier_results
        ],
        "details": {
            "overall_ratio": str(round(overall * 100, 1)).replace(".", ",") + "%",
            "num_occupations": str(len(valid)),
            "tier_breakdown": [
                {"tier": t["label"], "avg_ratio": str(round(t["avg_ratio"] * 100, 1)).replace(".", ",") + "%", "count": str(t["count"])}
                for t in tier_results
            ],
        },
    }


# ─── 294: escolaridade-missing ───────────────────────────────────────────────

def _escolaridade_missing(data, summary):
    matches = [o for o in data if not o.get("escolaridade") or o["escolaridade"].strip() == ""]
    if not matches:
        return {"headline_stat": "0", "headline_label": "ocupações sem escolaridade classificada", "chart_data": [], "details": {}}
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    avg_sal = round(_safe_avg([o["salario"] for o in matches if o.get("salario")])) if any(o.get("salario") for o in matches) else 0
    total_w = sum(o.get("empregados") or 0 for o in matches)
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupações sem escolaridade classificada — {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top10
        ],
        "details": {
            "num_occupations": str(len(matches)),
            "total_workers": _fmt_num(total_w),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0)}
                for o in top10
            ],
        },
    }


# ─── 295: subgrupo-exposure-ranking ──────────────────────────────────────────

def _subgrupo_exposure_ranking(data, summary):
    groups = {}
    for o in data:
        sub = o.get("subgrupo_principal")
        if not sub or o.get("exposicao") is None:
            continue
        if sub not in groups:
            groups[sub] = []
        groups[sub].append(o["exposicao"])
    if not groups:
        return {"headline_stat": "0", "headline_label": "subgrupos", "chart_data": [], "details": {}}
    ranked = [(sub, round(_safe_avg(vals), 1), len(vals)) for sub, vals in groups.items()]
    ranked.sort(key=lambda x: x[1], reverse=True)
    top10 = ranked[:10]
    bottom10 = ranked[-10:] if len(ranked) > 10 else ranked
    return {
        "headline_stat": str(top10[0][1]).replace(".", ","),
        "headline_label": f"exposição média — {top10[0][0][:40]}",
        "chart_data": [
            {"label": s[:40], "value": avg, "formatted": str(avg).replace(".", ",")}
            for s, avg, _ in top10
        ],
        "details": {
            "total_subgrupos": str(len(ranked)),
            "top10": [
                {"subgrupo": s, "avg_exposicao": str(avg).replace(".", ","), "num_occupations": str(cnt)}
                for s, avg, cnt in top10
            ],
            "bottom10": [
                {"subgrupo": s, "avg_exposicao": str(avg).replace(".", ","), "num_occupations": str(cnt)}
                for s, avg, cnt in bottom10
            ],
        },
    }


# ─── 296: overall-risk-summary ───────────────────────────────────────────────

def _overall_risk_summary(data, summary):
    categories = {
        "Seguro (0-3)": {"occs": [], "min": 0, "max": 3},
        "Moderado (4-6)": {"occs": [], "min": 4, "max": 6},
        "Em Risco (7-8)": {"occs": [], "min": 7, "max": 8},
        "Crítico (9-10)": {"occs": [], "min": 9, "max": 10},
    }
    for o in data:
        exp = o.get("exposicao")
        if exp is None:
            continue
        for cat_name, cat in categories.items():
            if cat["min"] <= exp <= cat["max"]:
                cat["occs"].append(o)
                break
    chart_data = []
    details_cats = []
    for cat_name, cat in categories.items():
        occs = cat["occs"]
        total_w = sum(o.get("empregados") or 0 for o in occs)
        avg_sal = round(_safe_avg([o["salario"] for o in occs if o.get("salario")])) if any(o.get("salario") for o in occs) else 0
        avg_oport = round(_safe_avg([o.get("oportunidade") for o in occs if o.get("oportunidade") is not None]), 1)
        chart_data.append({"label": cat_name, "value": total_w, "formatted": _fmt_num(total_w)})
        details_cats.append({
            "category": cat_name,
            "num_occupations": str(len(occs)),
            "total_workers": _fmt_num(total_w),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "avg_oportunidade": str(avg_oport).replace(".", ","),
        })
    total_all = sum(c["value"] for c in chart_data)
    return {
        "headline_stat": _fmt_num(total_all),
        "headline_label": "trabalhadores classificados por nível de risco",
        "chart_data": chart_data,
        "details": {
            "total_workers": _fmt_num(total_all),
            "categories": details_cats,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Template definitions
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES_BATCH_D2 = [
    # 272
    {
        "id": "construction-ai-lag",
        "category": "Setores",
        "tags": ["construção", "pedreiro", "baixa exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _construction_ai_lag,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre por que a construção civil resiste à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 273
    {
        "id": "transport-ai-revolution",
        "category": "Setores",
        "tags": ["transporte", "motorista", "veículos autônomos"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _transport_ai_revolution,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a revolução dos veículos autônomos e o impacto da IA no setor de transporte brasileiro.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Crescimento médio: {avg_crescimento} (escala 0-10)
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 274
    {
        "id": "creative-ai-paradox",
        "category": "Setores",
        "tags": ["criativo", "design", "arte", "paradoxo"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _creative_ai_paradox,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o paradoxo das profissões criativas: alta exposição à IA mas também alta vantagem com ela.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações criativas: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Vantagem média com IA: {avg_vantagem} (escala 0-10)
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 275
    {
        "id": "retail-ai-transformation",
        "category": "Setores",
        "tags": ["varejo", "vendedor", "serviços"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _retail_ai_transformation,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a transformação digital no varejo brasileiro e o impacto da IA nos vendedores.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Saldo médio de emprego: {avg_saldo}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 276
    {
        "id": "security-ai-impact",
        "category": "Setores",
        "tags": ["segurança", "vigilância", "tecnologia"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _security_ai_impact,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA e câmeras inteligentes no setor de segurança privada do Brasil.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 277
    {
        "id": "brazil-workforce-snapshot",
        "category": "Mercado",
        "tags": ["resumo", "panorama", "nacional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _brazil_workforce_snapshot,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) com o panorama geral da força de trabalho brasileira diante da IA.

DADOS (use APENAS estes números, não invente dados):
- Total de ocupações analisadas: {total_occupations}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Vantagem média com IA: {avg_vantagem} (escala 0-10)
- Crescimento médio: {avg_crescimento} (escala 0-10)
- Oportunidade média: {avg_oportunidade} (escala 0-10)

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 278
    {
        "id": "demographic-entry-risk",
        "category": "Mercado",
        "tags": ["admissões", "risco", "novos trabalhadores"],
        "chart_type": "ranking_table",
        "analysis_fn": _demographic_entry_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre novos trabalhadores entrando em ocupações de alto risco de exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Total de admissões nas top 10: {total_admissoes}
- Total de trabalhadores afetados: {total_workers}
- Número de ocupações de alto risco com admissões: {num_high_risk}
- Top ocupações por admissões: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 279
    {
        "id": "export-sectors",
        "category": "Setores",
        "tags": ["exportação", "comércio exterior", "portuário"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _export_sectors,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA nos setores ligados à exportação e comércio exterior do Brasil.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 280
    {
        "id": "green-jobs",
        "category": "Setores",
        "tags": ["verde", "ambiental", "sustentabilidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _green_jobs,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os empregos verdes no Brasil e como a IA afeta o setor ambiental e de sustentabilidade.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações verdes: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Oportunidade média: {avg_oportunidade} (escala 0-10)
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 281
    {
        "id": "ai-augmented-elite",
        "category": "Ocupações",
        "tags": ["elite", "alta vantagem", "alto salário"],
        "chart_type": "ranking_table",
        "analysis_fn": _ai_augmented_elite,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os profissionais que mais se beneficiam da IA: exposição 5-8, vantagem alta e salários acima de R$ 8.000.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações na elite IA: {num_occupations}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Lista de ocupações: {occupations_list}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 282
    {
        "id": "informal-economy-proxy",
        "category": "Mercado",
        "tags": ["informalidade", "baixo salário", "vulnerabilidade"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _informal_economy_proxy,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os trabalhadores de baixo salário (< R$ 1.500) e sua exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Principais setores: {top_setores}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 283
    {
        "id": "public-private-contrast",
        "category": "Setores",
        "tags": ["setor público", "comparação", "salário"],
        "chart_type": "comparison_pair",
        "analysis_fn": _public_private_contrast,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando a exposição à IA e salários entre ocupações do setor público e a média nacional.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações públicas: {num_occupations}
- Exposição média (público): {avg_exposicao_public} (escala 0-10)
- Exposição média (nacional): {avg_exposicao_national} (escala 0-10)
- Salário médio (público): {avg_salary_public}
- Salário médio (nacional): {avg_salary_national}
- Top ocupações públicas: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 284
    {
        "id": "occupation-name-length",
        "category": "Ocupações",
        "tags": ["curiosidade", "nomes longos", "fun"],
        "chart_type": "ranking_table",
        "analysis_fn": _occupation_name_length,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) com uma abordagem leve sobre as ocupações com os nomes mais longos do Brasil e sua exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Título mais longo: {longest_title} ({longest_chars} caracteres)
- Exposição do mais longo: {longest_exposicao} (escala 0-10)
- Top 10 nomes mais longos: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 285
    {
        "id": "most-workers-single-state",
        "category": "Regional",
        "tags": ["concentração", "estado", "regional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _most_workers_single_state,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a ocupação com maior concentração de trabalhadores em um único estado.

DADOS (use APENAS estes números, não invente dados):
- Ocupação: {occupation}
- Estado com maior concentração: {state}
- Trabalhadores no estado: {state_workers}
- Total de trabalhadores: {total_workers}
- Percentual de concentração: {concentration_pct}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 286
    {
        "id": "salary-above-20k",
        "category": "Mercado",
        "tags": ["alto salário", "elite", "remuneração"],
        "chart_type": "ranking_table",
        "analysis_fn": _salary_above_20k,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações que pagam R$ 20.000 ou mais e sua relação com a IA.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações: {num_occupations}
- Total de trabalhadores: {total_workers}
- Lista completa: {occupations_list}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 287
    {
        "id": "exposure-7-exactly",
        "category": "Ocupações",
        "tags": ["exposição", "ponto de inflexão", "limiar"],
        "chart_type": "ranking_table",
        "analysis_fn": _exposure_7_exactly,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com exposição exatamente 7 — o ponto de inflexão entre adaptação e substituição pela IA.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações com exposição 7: {num_occupations}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 288
    {
        "id": "vantagem-10-spotlight",
        "category": "Ocupações",
        "tags": ["vantagem máxima", "IA aliada", "benefício"],
        "chart_type": "ranking_table",
        "analysis_fn": _vantagem_10_spotlight,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações que têm vantagem máxima (10/10) com a IA — onde a tecnologia é aliada total.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações com vantagem 10: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Lista de ocupações: {occupations_list}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 289
    {
        "id": "crescimento-0-spotlight",
        "category": "Ocupações",
        "tags": ["retração", "demanda em queda", "crescimento zero"],
        "chart_type": "ranking_table",
        "analysis_fn": _crescimento_0_spotlight,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com crescimento zero ou mínimo — profissões com demanda em queda.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações em retração: {num_occupations}
- Total de trabalhadores afetados: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 290
    {
        "id": "oportunidade-9-plus",
        "category": "Ocupações",
        "tags": ["oportunidade", "máxima", "futuro"],
        "chart_type": "ranking_table",
        "analysis_fn": _oportunidade_9_plus,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações com oportunidade máxima (9+) — as profissões do futuro no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações: {num_occupations}
- Total de trabalhadores: {total_workers}
- Salário médio: {avg_salary}
- Lista de ocupações: {occupations_list}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 291
    {
        "id": "salary-vs-crescimento",
        "category": "Mercado",
        "tags": ["salário", "crescimento", "comparação"],
        "chart_type": "comparison_pair",
        "analysis_fn": _salary_vs_crescimento,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a relação entre crescimento da demanda e salário: ocupações em alta pagam melhor?

DADOS (use APENAS estes números, não invente dados):
- Ocupações com crescimento alto (≥ 7): {num_high_crescimento}
- Salário médio (crescimento alto): {avg_salary_high}
- Ocupações com crescimento baixo (≤ 3): {num_low_crescimento}
- Salário médio (crescimento baixo): {avg_salary_low}
- Diferença salarial: {diff}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 292
    {
        "id": "exposure-by-codigo-prefix",
        "category": "Ocupações",
        "tags": ["grande grupo", "código", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _exposure_by_codigo_prefix,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a exposição à IA varia entre os grandes grupos ocupacionais (agrupados pelo primeiro dígito do código CBO).

DADOS (use APENAS estes números, não invente dados):
- Grupos ocupacionais e suas exposições médias: {groups}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 293
    {
        "id": "admissoes-to-saldo-ratio",
        "category": "Mercado",
        "tags": ["admissões", "saldo", "eficiência"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _admissoes_to_saldo_ratio,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a eficiência das contratações: qual fração das admissões resulta em saldo líquido positivo, e como isso varia por nível de exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Razão geral saldo/admissões: {overall_ratio}
- Número de ocupações analisadas: {num_occupations}
- Breakdown por faixa de exposição: {tier_breakdown}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 294
    {
        "id": "escolaridade-missing",
        "category": "Educação",
        "tags": ["escolaridade", "dados faltantes", "educação"],
        "chart_type": "ranking_table",
        "analysis_fn": _escolaridade_missing,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações sem escolaridade classificada e o que isso revela sobre lacunas nos dados do mercado de trabalho.

DADOS (use APENAS estes números, não invente dados):
- Número de ocupações sem escolaridade: {num_occupations}
- Total de trabalhadores: {total_workers}
- Exposição média à IA: {avg_exposicao} (escala 0-10)
- Salário médio: {avg_salary}
- Top ocupações: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 295
    {
        "id": "subgrupo-exposure-ranking",
        "category": "Setores",
        "tags": ["subgrupo", "ranking", "exposição"],
        "chart_type": "ranking_table",
        "analysis_fn": _subgrupo_exposure_ranking,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o ranking dos subgrupos ocupacionais por exposição à IA — quais setores lideram e quais ficam atrás.

DADOS (use APENAS estes números, não invente dados):
- Total de subgrupos: {total_subgrupos}
- Top 10 mais expostos: {top10}
- Bottom 10 menos expostos: {bottom10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    # 296
    {
        "id": "overall-risk-summary",
        "category": "Mercado",
        "tags": ["resumo", "risco", "categorias"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _overall_risk_summary,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) com o resumo geral de risco: quantos trabalhadores estão em cada faixa de exposição à IA (Seguro, Moderado, Em Risco, Crítico).

DADOS (use APENAS estes números, não invente dados):
- Total de trabalhadores classificados: {total_workers}
- Categorias de risco: {categories}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates_batch_d2():
    return TEMPLATES_BATCH_D2
