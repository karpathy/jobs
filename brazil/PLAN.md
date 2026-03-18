# Brazil AI Jobs Impact Visualizer — Build Plan

## Architecture Decision

**Approach:** `brazil/` directory in same repo, on `brazil` branch.
- US code stays untouched at repo root
- Brazil pipeline lives under `brazil/`
- Shared logic can be imported from root when useful
- Spec lives in `spec/` (shared, not under `brazil/`)

```
ai-jobs-impact/
├── scrape.py, score.py, ...     # US pipeline (don't touch)
├── site/                         # US site
├── spec/                         # Shared spec (TSV for Google Sheets)
└── brazil/
    ├── PLAN.md                   # This file
    ├── scrape_cbo.py             # Step 1: Get CBO occupations
    ├── scrape_caged.py           # Step 2: Get CAGED employment/salary data
    ├── parse_cbo.py              # Parse CBO into structured data
    ├── make_csv_br.py            # Generate occupations_br.csv
    ├── score_br.py               # LLM scoring with PT prompts
    ├── build_site_data_br.py     # Merge all → site data
    ├── data/                     # Raw downloaded data (CBO, CAGED, RAIS)
    ├── pages/                    # Occupation descriptions (markdown)
    ├── site/                     # Brazil site build output
    └── scores/                   # LLM score outputs
```

## Build Steps

### Step 1: Get CBO Occupation List + Descriptions
**Script:** `brazil/scrape_cbo.py`
**Source:** cbo.mte.gov.br
**Output:** `brazil/data/cbo_occupations.json`
**What it does:**
- Scrape or download CBO occupation codes (Família, 4 digits — ~600 occupations)
- Get title + description for each (atividades, formação, etc.)
- Structure as JSON: `{codigo, titulo, grande_grupo, subgrupo, descricao, atividades[]}`
**Blocks:** Everything — this is the foundation.
**Status:** TODO

### Step 2: Get CAGED/RAIS Employment & Salary Data
**Script:** `brazil/scrape_caged.py`
**Source:** MTE BI portal / microdados FTP
**Output:** `brazil/data/caged_stats.json`
**What it does:**
- Download employment stock by CBO code (RAIS or CAGED BI)
- Get median salary by CBO code
- Get admissions/separations (saldo) for growth calculation
- Optionally: breakdown by UF (state) for regional data later
**Blocks:** Real data in CSV, but can mock for pipeline testing.
**Status:** TODO

### Step 3: Build Brazil CSV
**Script:** `brazil/make_csv_br.py`
**Input:** `cbo_occupations.json` + `caged_stats.json`
**Output:** `brazil/occupations_br.csv`
**Columns:** codigo_cbo, titulo, grande_grupo, salario_mediano, estoque_empregados, saldo_12m, escolaridade_tipica, setor_cnae, descricao
**Status:** TODO

### Step 4: Generate Occupation Descriptions for LLM
**Script:** `brazil/make_pages_br.py`
**Input:** CBO data (descriptions, activities, formation)
**Output:** `brazil/pages/*.md` (one per occupation)
**Purpose:** LLM needs rich text descriptions to score accurately.
**Status:** TODO

### Step 5: Adapt LLM Scoring
**Script:** `brazil/score_br.py`
**Based on:** `score.py` (root)
**Changes:**
- Prompts in Portuguese
- Calibration anchors: pedreiro, motorista de app, desenvolvedor, caixa, médico
- 3 existing metrics: exposição, vantagem, crescimento
- 2 new metrics: risco_automação (0-10), facilidade_transição (0-10, pair-wise)
- Same OpenRouter/Gemini approach
**Output:** `brazil/scores/scores_exposicao.json`, etc.
**Status:** TODO

### Step 6: Build Site Data
**Script:** `brazil/build_site_data_br.py`
**Input:** CSV + all score files
**Output:** `brazil/site/data.json`
**Computed fields:** oportunidade = avg(vantagem, crescimento)
**Status:** TODO

### Step 7: Adapt Treemap + Build Site
**Source:** `site/index.html` (copy and adapt)
**Changes:**
- CBO Grandes Grupos (10) replace SOC categories (22)
- Portuguese labels, tooltips, stats
- Same canvas treemap engine
**Output:** `brazil/site/index.html`
**Status:** TODO

### Step 8: New Views (incremental)
Each is independent and can be built in any order:
- Scatter plot (risco x oportunidade) — P0
- Painel pessoal (personal dashboard) — P0
- Barras por setor (sector bars) — P2
- Mapa regional (choropleth) — P1
- Sankey (career paths) — P1
- Waterfall salarial — P1
- Radar de habilidades — P2

## Open Questions (resolve with João)

1. **CBO granularity:** 4-digit Família (~600) vs 6-digit Ocupação (~2500)?
   - Recommendation: Start with 4-digit, expand later
2. **CBO descriptions quality:** Are they rich enough for LLM scoring?
   - Need to inspect actual CBO text before deciding
3. **CAGED access:** FTP microdados vs BI portal API?
   - Try BI portal first (easier), fall back to microdados
4. **Course data source:** SENAI catalog scrapable? Or manual curation?
5. **Informal economy mapping:** How to map informal → formal CBO codes?

## Current Status

- [x] Spec created (8 TSV files in `spec/`)
- [x] Plan documented (this file)
- [x] Branch created (`brazil`)
- [x] Step 1: Scrape CBO (626 families, 7 CSVs from gov.br, perfil ocupacional with activities)
- [x] Step 4: Generate descriptions (626 markdown pages with deduplicated activities from perfil)
- [x] Step 2: Get CAGED data (12 months 2025, 51.4M rows from MTE FTP, 623 families with salary/employment)
- [x] Step 3: Build CSV (626 rows merging CBO + CAGED, 608 with employment data)
- [ ] Step 5: LLM scoring
- [ ] Step 6: Build site data
- [ ] Step 7: Adapt treemap
- [ ] Step 8: New views
