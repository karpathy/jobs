# Handover Document — JobsCY

> **Last updated:** 2026-03-18 (PR 4: Scoring Adaptation)
> **Branch:** `claude/cyprus-job-market-adaptation-HX1xe`
> **Repo:** https://github.com/alezenonos/jobscy

---

## Project overview

JobsCY adapts [karpathy/jobs](https://github.com/karpathy/jobs) (a US BLS occupational treemap) for the **Cyprus labour market** using EU/Cyprus data sources. The goal is an interactive treemap of Cyprus occupations sized by employment and coloured by growth outlook, median pay (EUR), education level, or AI exposure score.

## Architecture

```
Cyprus pipeline (new):
  ISCO-08 data ──► generate_cy_occupations.py ──► occupations_cy.json
  Eurostat API ──► make_cy_csv.py ─────────────► occupations_cy.csv
                                                        │
  LLM (OpenRouter) ──► score.py ──► scores.json ◄──────┘
                                         │
                     build_site_data.py ──┘──► site/data.json ──► site/index.html

Legacy BLS pipeline (still works):
  BLS HTML ──► scrape.py ──► parse/make_csv.py ──► occupations.csv ──► ...
```

### Key modules

| Module | Purpose | Status |
|--------|---------|--------|
| `eurostat.py` | Fetch Cyprus employment/wage data from Eurostat REST API | **Done (PR 2)** |
| `generate_cy_occupations.py` | Generate `occupations_cy.json` from ISCO-08 classification | **Done (PR 3)** |
| `make_cy_csv.py` | Build `occupations_cy.csv` from Eurostat data (EUR, ISCO) | **Done (PR 3)** |
| `build_site_data.py` | Merge CSV + scores → `site/data.json` (auto-detects BLS/Cyprus format) | **Done (PR 3)** |
| `scrape.py` | Scrape occupation detail pages (currently BLS) | Needs Cyprus adaptation |
| `parse_occupations.py` | Parse occupation index into `occupations.json` (legacy BLS) | Superseded by `generate_cy_occupations.py` |
| `parse_detail.py` | Convert HTML detail pages to Markdown | Needs Cyprus adaptation |
| `process.py` | Batch HTML→Markdown conversion | Works as-is |
| `make_csv.py` | Build `occupations.csv` from BLS HTML (legacy) | Superseded by `make_cy_csv.py` |
| `score.py` | LLM-based AI exposure scoring via OpenRouter | **Done (PR 4)** |
| `build_site_data.py` | Merge CSV + scores → `site/data.json` | Works as-is |
| `make_prompt.py` | Generate single-file LLM prompt | Updated for EUR/Cyprus |
| `site/index.html` | Interactive treemap visualization | Needs EUR/Cyprus UI updates |

## Data sources (Cyprus/EU)

| Source | What it provides | Access method | Priority |
|--------|-----------------|---------------|----------|
| **HRDA/AnAD** | 309 occupation forecasts (2022-2032), expansion + replacement demand | PDF / web tool (manual extract) | Primary |
| **Eurostat API** | Employment by ISCO-08 2-digit, wages by ISCO-08 1-digit, `geo=CY` | REST API (CSV/JSON) | Primary |
| **EURES** | Shortage/surplus occupations, vacancy stats by ESCO | Web dashboard | Secondary |
| **CEDEFOP** | Skills forecasts to 2035 by sector and occupation group | PDF / request form | Secondary |
| **CYSTAT** | Aggregate employment, unemployment, labour costs | CYSTAT-DB / data.gov.cy | Supporting |
| **Job boards** | Current demand signals (Ergodotisi, Carierista) | Web scraping (no API) | Optional |

### Key Eurostat datasets

| Dataset code | Content | Granularity |
|---|---|---|
| `LFSA_EGAI2D` | Employment by occupation | ISCO-08 2-digit, by country, sex, age |
| `lfsa_eisn2` | Employment by occupation × economic activity | ISCO 1-digit × NACE |
| `earn_ses_pub1s` | Median gross hourly earnings | By ISCO 1-digit, NACE, country |

### Eurostat API format

```
# CSV endpoint
https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{DATASET}?format=SDMX-CSV&geo=CY

# JSON-stat endpoint
https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{DATASET}?geo=CY
```

## Completed work

### PR 1: CI/CD + Testing + Cyprus Rebrand ✅
- GitHub Actions CI (`.github/workflows/ci.yml`) — lint (ruff) + test (pytest)
- 37 unit tests across 5 test files
- Ruff linter + formatter configured in `pyproject.toml`
- README rewritten for Cyprus/EU context
- All script docstrings updated
- Currency changed from USD → EUR in `make_prompt.py`
- Pay bands changed from US ranges to EU ranges
- `.gitignore` updated

### PR 2: Eurostat API Client + HANDOVER.md ✅
- `eurostat.py` — full client module for Eurostat SDMX 2.1 REST API
  - `fetch_sdmx_csv()` — generic CSV fetcher for any Eurostat dataset
  - `fetch_json_stat()` — JSON-stat endpoint fetcher
  - `fetch_employment_by_occupation()` — ISCO-08 2-digit employment for Cyprus
  - `fetch_earnings_by_occupation()` — ISCO-08 1-digit earnings (SES) for Cyprus
  - `build_occupation_summary()` — merges employment + earnings into unified view
  - Complete ISCO-08 reference data (10 major groups, 36 sub-major groups)
  - CLI interface with CSV/JSON output options
- 21 new tests (`tests/test_eurostat.py`) using mocked HTTP responses
- CI workflow fixed to target `master` branch (was incorrectly set to `main`)
- `HANDOVER.md` created as living project status document

### PR 3: Cyprus Data Pipeline ✅
- `generate_cy_occupations.py` — generates `occupations_cy.json` from ISCO-08 classification
  - 39 sub-major group occupations with ISCO codes, categories, and slugs
  - Optional inclusion of 10 major groups for aggregated views
  - ISCO-based category system (managers, professionals, technicians, etc.)
- `make_cy_csv.py` — builds `occupations_cy.csv` from Eurostat data
  - Merges ISCO-08 occupation list with employment counts and EUR earnings
  - Supports both live API fetching and cached JSON data
  - Education level mapping by ISCO major group (ISCED-aligned)
  - Cache save/load for offline development
- `build_site_data.py` — refactored to auto-detect BLS vs Cyprus CSV format
  - `merge_bls()` / `merge_cyprus()` / `detect_format()` functions
  - Cyprus format: ISCO codes, EUR pay, employment in thousands→absolute
  - BLS format: backward compatible with existing US data
  - CLI args for explicit CSV/scores/output paths
- 30 new tests across 3 test files (88 total)

### PR 4: Scoring Adaptation ✅
- `score.py` — fully adapted for Cyprus/EU labour market
  - New `SYSTEM_PROMPT` with Cyprus/EU context (tourism, shipping, financial services, EU Digital Decade, public sector)
  - ISCO-08 occupation examples as scoring anchors (replacing BLS examples)
  - Extracted `parse_llm_response()` — robust JSON parsing with markdown fence stripping
  - New `build_isco_prompt()` — constructs scoring prompts from ISCO-08 metadata when no markdown exists
  - New `detect_occupation_format()` — auto-detects BLS vs Cyprus occupation lists
  - Updated `main()` — auto-detects `occupations_cy.json` vs `occupations.json`
- 12 new tests in `tests/test_score.py` (97 total)

## Remaining work (roadmap)

### PR 5: Visualization + Site Update
- Update `site/index.html`: EUR currency formatting, Cyprus occupation categories
- Update treemap colour scales for EU wage ranges
- Update UI text (remove all US/BLS references)

### PR 6: Documentation Final Pass
- Architecture diagrams
- Contributing guidelines
- Troubleshooting guide

## Development setup

```bash
uv sync --extra dev          # install all deps including pytest/ruff
uv run pytest -v             # run tests
uv run ruff check .          # lint
uv run ruff format .         # format
```

Requires `.env` with `OPENROUTER_API_KEY` for LLM scoring only.

## Conventions

- **Branch:** all work on `claude/cyprus-job-market-adaptation-HX1xe`
- **Default branch:** `master` (not `main`)
- **Currency:** EUR (€), never USD
- **Classification:** ISCO-08 for occupations, NACE Rev. 2 for sectors, ISCED 2011 for education
- **Data period:** HRDA 2022-2032 forecasts, Eurostat latest available year
- **Python:** 3.10+, formatted with ruff, tested with pytest
- **CI:** GitHub Actions on push to `master` and `claude/*` branches, and on PRs to `master`
