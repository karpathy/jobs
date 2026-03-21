"""Insight templates batch A: state deep dives + occupation spotlights."""
import statistics
from insight_templates import _fmt_pct, _fmt_num, _safe_avg


# ═══════════════════════════════════════════════════════════════════════════════
# State deep-dive helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_state_fn(uf_code, state_name, state_abbr):
    """Factory that returns an analysis function for a given UF."""

    def _fn(data, summary):
        st = summary["por_uf"].get(uf_code, {})
        total = st.get("total_workers", 0)
        national = sum(v["total_workers"] for v in summary["por_uf"].values())
        pct_national = round(total / national * 100, 1) if national else 0
        top_occs = st.get("top_occupations", [])
        return {
            "headline_stat": _fmt_num(total),
            "headline_label": f"trabalhadores em {state_abbr} \u2014 {_fmt_pct(pct_national)} do total nacional",
            "chart_data": [
                {"label": o["titulo"], "value": o["workers"], "formatted": _fmt_num(o["workers"])}
                for o in top_occs[:8]
            ],
            "details": {
                "total_workers": _fmt_num(total),
                "pct_national": _fmt_pct(pct_national),
                "avg_salary": "R$ " + _fmt_num(st.get("avg_salary", 0)),
                "avg_exposicao": str(st.get("avg_exposicao", 0)).replace(".", ","),
                "top_occupations": [
                    {"titulo": o["titulo"], "workers": _fmt_num(o["workers"])}
                    for o in top_occs
                ],
            },
        }

    _fn.__name__ = f"_state_{state_abbr.lower()}_deep_dive"
    return _fn


def _make_state_template(template_id, uf_code, state_name, state_abbr, slug):
    """Build a complete template dict for a state deep dive."""
    fn = _make_state_fn(uf_code, state_name, state_abbr)
    return {
        "id": slug,
        "category": "Regional",
        "tags": [state_name, state_abbr, "regional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": fn,
        "prompt_template": f"""Voc\u00ea \u00e9 um jornalista de dados escrevendo para uma publica\u00e7\u00e3o como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o impacto da IA no mercado de trabalho de {state_name}.

DADOS (use APENAS estes n\u00fameros, n\u00e3o invente dados):
- Total de trabalhadores: {{total_workers}}
- Participa\u00e7\u00e3o nacional: {{pct_national}}
- Sal\u00e1rio m\u00e9dio: {{avg_salary}}
- Exposi\u00e7\u00e3o m\u00e9dia: {{avg_exposicao}}
- Top ocupa\u00e7\u00f5es: {{top_occupations}}

Retorne JSON com exatamente estes campos:
{{{{"title": "t\u00edtulo impactante (m\u00e1x 10 palavras)", "subtitle": "subt\u00edtulo explicativo (m\u00e1x 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}}}""",
    }


# ─── State definitions ────────────────────────────────────────────────────────

_STATE_DEFS = [
    # (id_num, uf_code, state_name, abbr, slug)
    (97,  "42", "Santa Catarina",         "SC", "santa-catarina-deep-dive"),
    (98,  "26", "Pernambuco",             "PE", "pernambuco-deep-dive"),
    (99,  "23", "Cear\u00e1",             "CE", "ceara-deep-dive"),
    (100, "52", "Goi\u00e1s",             "GO", "goias-deep-dive"),
    (101, "51", "Mato Grosso",            "MT", "mato-grosso-deep-dive"),
    (102, "50", "Mato Grosso do Sul",     "MS", "mato-grosso-sul-deep-dive"),
    (103, "15", "Par\u00e1",              "PA", "para-deep-dive"),
    (104, "13", "Amazonas",               "AM", "amazonas-deep-dive"),
    (105, "21", "Maranh\u00e3o",          "MA", "maranhao-deep-dive"),
    (106, "22", "Piau\u00ed",             "PI", "piaui-deep-dive"),
    (107, "24", "Rio Grande do Norte",    "RN", "rio-grande-norte-deep-dive"),
    (108, "25", "Para\u00edba",           "PB", "paraiba-deep-dive"),
    (109, "27", "Alagoas",                "AL", "alagoas-deep-dive"),
    (110, "28", "Sergipe",                "SE", "sergipe-deep-dive"),
    (111, "32", "Esp\u00edrito Santo",    "ES", "espirito-santo-deep-dive"),
    (112, "17", "Tocantins",              "TO", "tocantins-deep-dive"),
    (113, "11", "Rond\u00f4nia",          "RO", "rondonia-deep-dive"),
    (114, "12", "Acre",                   "AC", "acre-deep-dive"),
    (115, "14", "Roraima",                "RR", "roraima-deep-dive"),
    (116, "16", "Amap\u00e1",             "AP", "amapa-deep-dive"),
]

_STATE_TEMPLATES = [
    _make_state_template(id_num, code, name, abbr, slug)
    for id_num, code, name, abbr, slug in _STATE_DEFS
]


# ═══════════════════════════════════════════════════════════════════════════════
# Occupation spotlight helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _spotlight_fn(data, summary, keywords, exclude_keywords=None):
    """Generic occupation spotlight analysis."""
    matches = []
    for o in data:
        titulo = o.get("titulo", "").lower()
        if o.get("exposicao") is None:
            continue
        if any(kw in titulo for kw in keywords):
            if exclude_keywords and any(ek in titulo for ek in exclude_keywords):
                continue
            matches.append(o)
    if not matches:
        matches = [o for o in data if o.get("exposicao") is not None][:1]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    main = matches[0]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    avg_van = round(_safe_avg([o.get("vantagem") for o in matches if o.get("vantagem") is not None]), 1)
    top5 = matches[:5]

    dem = main.get("demographics") or {}
    fem = dem.get("total_feminino", 0)
    masc = dem.get("total_masculino", 0)
    total_dem = fem + masc if (fem or masc) else 0
    pct_fem = round(fem / total_dem * 100, 1) if total_dem else 0

    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores \u2014 exposi\u00e7\u00e3o m\u00e9dia {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {
                "label": o.get("titulo", ""),
                "value": o.get("empregados") or 0,
                "formatted": _fmt_num(o.get("empregados") or 0),
            }
            for o in top5
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "num_occupations": str(len(matches)),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "avg_vantagem": str(avg_van).replace(".", ","),
            "pct_feminino": _fmt_pct(pct_fem) if total_dem else "N/D",
            "main_occupation": main.get("titulo", ""),
            "main_workers": _fmt_num(main.get("empregados") or 0),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0)}
                for o in top5
            ],
        },
    }


def _make_spotlight_template(slug, occ_name, keywords, exclude_keywords=None):
    """Build a complete template dict for an occupation spotlight."""

    def _fn(data, summary):
        return _spotlight_fn(data, summary, keywords, exclude_keywords)

    _fn.__name__ = f"_spotlight_{slug.replace('-', '_')}"

    return {
        "id": slug,
        "category": "Ocupa\u00e7\u00f5es",
        "tags": [occ_name, "spotlight", "ocupa\u00e7\u00e3o"],
        "chart_type": "ranking_table",
        "analysis_fn": _fn,
        "prompt_template": f"""Voc\u00ea \u00e9 um jornalista de dados escrevendo para uma publica\u00e7\u00e3o como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a IA afeta os profissionais de {occ_name} no Brasil.

DADOS (use APENAS estes n\u00fameros, n\u00e3o invente dados):
- Total de trabalhadores: {{total_workers}}
- N\u00famero de ocupa\u00e7\u00f5es relacionadas: {{num_occupations}}
- Exposi\u00e7\u00e3o m\u00e9dia \u00e0 IA: {{avg_exposicao}} (escala 0-10)
- Sal\u00e1rio m\u00e9dio: {{avg_salary}}
- Vantagem m\u00e9dia com IA: {{avg_vantagem}} (escala 0-10)
- Percentual feminino: {{pct_feminino}}
- Principal ocupa\u00e7\u00e3o: {{main_occupation}} ({{main_workers}} trabalhadores)
- Top ocupa\u00e7\u00f5es: {{top_occupations}}

Retorne JSON com exatamente estes campos:
{{{{"title": "t\u00edtulo impactante (m\u00e1x 10 palavras)", "subtitle": "subt\u00edtulo explicativo (m\u00e1x 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}}}""",
    }


# ─── Spotlight definitions ────────────────────────────────────────────────────

_SPOTLIGHT_DEFS = [
    # (slug, display_name, keywords, exclude_keywords)
    ("advogados-spotlight",            "advocacia",          ["advogad"],            None),
    ("medicos-spotlight",              "medicina",           ["m\u00e9dic"],         None),
    ("contadores-spotlight",           "contabilidade",      ["contad"],             None),
    ("programadores-spotlight",        "programa\u00e7\u00e3o", ["programa"],        ["professor"]),
    ("motoristas-spotlight",           "transporte",         ["motorist"],           None),
    ("enfermeiros-spotlight",          "enfermagem",         ["enfermeir"],          None),
    ("professores-basico-spotlight",   "ensino b\u00e1sico", ["professor"],          None),
    ("caixas-spotlight",               "caixas",             ["caixa"],              None),
    ("secretarios-spotlight",          "secretariado",       ["secret\u00e1ri"],     None),
    ("vendedores-spotlight",           "vendas",             ["vendedor"],           None),
    ("agricultores-spotlight",         "agricultura",        ["agricultor", "agropecu\u00e1ri"], None),
    ("garcons-cozinheiros-spotlight",  "gastronomia",        ["gar\u00e7on", "cozinheir"], None),
    ("porteiros-spotlight",            "portaria e zeladoria", ["porteir", "zelador"], None),
    ("vigilantes-spotlight",           "vigil\u00e2ncia",    ["vigilant"],           None),
    ("mecanicos-spotlight",            "mec\u00e2nica",      ["mec\u00e2nic"],       None),
    ("dentistas-spotlight",            "odontologia",        ["dentist", "odont\u00f3log"], None),
    ("psicologos-spotlight",           "psicologia",         ["psic\u00f3log"],      None),
    ("farmaceuticos-spotlight",        "farm\u00e1cia",      ["farmac"],             None),
    ("arquitetos-spotlight",           "arquitetura",        ["arquitet"],           None),
    ("jornalistas-spotlight",          "jornalismo",         ["jornalist"],          None),
]

# Special handling for professores-basico: needs compound filter
def _professores_basico_fn(data, summary):
    matches = []
    for o in data:
        titulo = o.get("titulo", "").lower()
        if o.get("exposicao") is None:
            continue
        if "professor" in titulo and any(kw in titulo for kw in ["b\u00e1sic", "fundamental", "infantil"]):
            matches.append(o)
    if not matches:
        # Fallback: any professor
        matches = [o for o in data if "professor" in o.get("titulo", "").lower() and o.get("exposicao") is not None]
    if not matches:
        matches = [o for o in data if o.get("exposicao") is not None][:1]
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    main = matches[0]
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o["exposicao"] for o in matches]), 1)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    avg_van = round(_safe_avg([o.get("vantagem") for o in matches if o.get("vantagem") is not None]), 1)
    top5 = matches[:5]
    dem = main.get("demographics") or {}
    fem = dem.get("total_feminino", 0)
    masc = dem.get("total_masculino", 0)
    total_dem = fem + masc if (fem or masc) else 0
    pct_fem = round(fem / total_dem * 100, 1) if total_dem else 0
    return {
        "headline_stat": _fmt_num(total_w),
        "headline_label": f"trabalhadores \u2014 exposi\u00e7\u00e3o m\u00e9dia {str(avg_exp).replace('.', ',')}",
        "chart_data": [
            {"label": o.get("titulo", ""), "value": o.get("empregados") or 0, "formatted": _fmt_num(o.get("empregados") or 0)}
            for o in top5
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "num_occupations": str(len(matches)),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "avg_vantagem": str(avg_van).replace(".", ","),
            "pct_feminino": _fmt_pct(pct_fem) if total_dem else "N/D",
            "main_occupation": main.get("titulo", ""),
            "main_workers": _fmt_num(main.get("empregados") or 0),
            "top_occupations": [
                {"titulo": o.get("titulo", ""), "workers": _fmt_num(o.get("empregados") or 0)}
                for o in top5
            ],
        },
    }


_SPOTLIGHT_TEMPLATES = []
for _slug, _name, _kws, _excl in _SPOTLIGHT_DEFS:
    if _slug == "professores-basico-spotlight":
        _tpl = {
            "id": _slug,
            "category": "Ocupa\u00e7\u00f5es",
            "tags": [_name, "spotlight", "ocupa\u00e7\u00e3o"],
            "chart_type": "ranking_table",
            "analysis_fn": _professores_basico_fn,
            "prompt_template": """Voc\u00ea \u00e9 um jornalista de dados escrevendo para uma publica\u00e7\u00e3o como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a IA afeta os profissionais de ensino b\u00e1sico no Brasil.

DADOS (use APENAS estes n\u00fameros, n\u00e3o invente dados):
- Total de trabalhadores: {total_workers}
- N\u00famero de ocupa\u00e7\u00f5es relacionadas: {num_occupations}
- Exposi\u00e7\u00e3o m\u00e9dia \u00e0 IA: {avg_exposicao} (escala 0-10)
- Sal\u00e1rio m\u00e9dio: {avg_salary}
- Vantagem m\u00e9dia com IA: {avg_vantagem} (escala 0-10)
- Percentual feminino: {pct_feminino}
- Principal ocupa\u00e7\u00e3o: {main_occupation} ({main_workers} trabalhadores)
- Top ocupa\u00e7\u00f5es: {top_occupations}

Retorne JSON com exatamente estes campos:
{{"title": "t\u00edtulo impactante (m\u00e1x 10 palavras)", "subtitle": "subt\u00edtulo explicativo (m\u00e1x 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
        }
        _SPOTLIGHT_TEMPLATES.append(_tpl)
    else:
        _SPOTLIGHT_TEMPLATES.append(_make_spotlight_template(_slug, _name, _kws, _excl))


# ═══════════════════════════════════════════════════════════════════════════════
# Subgrupo analysis helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _subgrupo_fn(data, summary, keywords):
    """Generic subgrupo analysis."""
    matches = []
    for o in data:
        sub = (o.get("subgrupo_principal") or "").upper()
        if any(kw in sub for kw in keywords):
            matches.append(o)
    if not matches:
        return {
            "headline_stat": "0",
            "headline_label": "ocupa\u00e7\u00f5es encontradas",
            "chart_data": [],
            "details": {},
        }
    matches.sort(key=lambda o: (o.get("empregados") or 0), reverse=True)
    total_w = sum(o.get("empregados") or 0 for o in matches)
    avg_exp = round(_safe_avg([o.get("exposicao") for o in matches if o.get("exposicao") is not None]), 1)
    sal_vals = [o["salario"] for o in matches if o.get("salario")]
    avg_sal = round(_safe_avg(sal_vals)) if sal_vals else 0
    top10 = matches[:10]
    return {
        "headline_stat": str(len(matches)),
        "headline_label": f"ocupa\u00e7\u00f5es \u2014 {_fmt_num(total_w)} trabalhadores",
        "chart_data": [
            {
                "label": o.get("titulo", ""),
                "value": o.get("empregados") or 0,
                "formatted": _fmt_num(o.get("empregados") or 0),
            }
            for o in top10
        ],
        "details": {
            "total_workers": _fmt_num(total_w),
            "num_occupations": str(len(matches)),
            "avg_exposicao": str(avg_exp).replace(".", ","),
            "avg_salary": "R$ " + _fmt_num(avg_sal),
            "top_occupations": [
                {
                    "titulo": o.get("titulo", ""),
                    "workers": _fmt_num(o.get("empregados") or 0),
                    "exposicao": str(o.get("exposicao", "N/D")).replace(".", ","),
                }
                for o in top10
            ],
        },
    }


def _make_subgrupo_template(slug, subgrupo_name, keywords):
    """Build a complete template dict for a subgrupo analysis."""

    def _fn(data, summary):
        return _subgrupo_fn(data, summary, keywords)

    _fn.__name__ = f"_subgrupo_{slug.replace('-', '_')}"

    return {
        "id": slug,
        "category": "Setores",
        "tags": [subgrupo_name, "subgrupo", "setor"],
        "chart_type": "ranking_table",
        "analysis_fn": _fn,
        "prompt_template": f"""Voc\u00ea \u00e9 um jornalista de dados escrevendo para uma publica\u00e7\u00e3o como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como a IA afeta o setor de {subgrupo_name} no Brasil.

DADOS (use APENAS estes n\u00fameros, n\u00e3o invente dados):
- Total de trabalhadores: {{total_workers}}
- N\u00famero de ocupa\u00e7\u00f5es: {{num_occupations}}
- Exposi\u00e7\u00e3o m\u00e9dia \u00e0 IA: {{avg_exposicao}} (escala 0-10)
- Sal\u00e1rio m\u00e9dio: {{avg_salary}}
- Top ocupa\u00e7\u00f5es: {{top_occupations}}

Retorne JSON com exatamente estes campos:
{{{{"title": "t\u00edtulo impactante (m\u00e1x 10 palavras)", "subtitle": "subt\u00edtulo explicativo (m\u00e1x 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}}}""",
    }


# ─── Subgrupo definitions ────────────────────────────────────────────────────

_SUBGRUPO_DEFS = [
    ("subgrupo-ciencias-exatas",    "ci\u00eancias exatas",       ["CI\u00caCIAS EXATAS", "CI\u00caNCIAS EXATAS"]),
    ("subgrupo-ensino-superior",    "ensino superior",            ["ENSINO SUPERIOR"]),
    ("subgrupo-saude",              "sa\u00fade",                 ["SA\u00daDE"]),
    ("subgrupo-juridico",           "setor jur\u00eddico",        ["JUR\u00cdDIC"]),
    ("subgrupo-artes",              "artes e espet\u00e1culos",   ["ARTES", "ESPET\u00c1CULO"]),
    ("subgrupo-informatica",        "inform\u00e1tica e TI",      ["INFORM\u00c1TICA", "INFORMA\u00c7\u00c3O"]),
    ("subgrupo-metalurgia",         "metalurgia e siderurgia",    ["METAL\u00daRG", "SIDER\u00daRG"]),
    ("subgrupo-alimentacao",        "alimenta\u00e7\u00e3o",      ["ALIMENTA\u00c7\u00c3O", "ALIMENTO"]),
    ("subgrupo-textil",             "t\u00eaxtil e confec\u00e7\u00e3o", ["T\u00caXTIL", "CONFEC\u00c7"]),
    ("subgrupo-meios-transporte",   "transporte",                 ["TRANSPORTE"]),
]

_SUBGRUPO_TEMPLATES = [
    _make_subgrupo_template(slug, name, kws)
    for slug, name, kws in _SUBGRUPO_DEFS
]


# ═══════════════════════════════════════════════════════════════════════════════
# Combined template list
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES_BATCH_A = _STATE_TEMPLATES + _SPOTLIGHT_TEMPLATES + _SUBGRUPO_TEMPLATES


def get_templates_batch_a():
    return TEMPLATES_BATCH_A
