# JobsCY — Cyprus Job Market Visualizer

An interactive treemap visualization of the Cyprus labour market, with AI exposure scoring for occupations. Built on data from EU/Cyprus sources including [HRDA/AnAD](https://www.anad.org.cy), [Eurostat](https://ec.europa.eu/eurostat), and [EURES Cyprus](https://eures.europa.eu).

## What's here

An interactive treemap of **39 ISCO-08 occupation groups** covering the Cyprus labour market. Each rectangle's **area** is proportional to employment and **colour** shows the selected metric — toggle between growth outlook, median pay (EUR), education level, and AI exposure.

Data is sourced from the Eurostat SDMX REST API (employment by ISCO-08 2-digit, earnings by ISCO-08 1-digit, filtered to `geo=CY`) and enriched with HRDA 2022-2032 occupation forecasts.

## Data sources

| Source | What it provides | Format |
|--------|-----------------|--------|
| **Eurostat API** | Employment by ISCO-08 (2-digit), wages by ISCO-08 (1-digit), filtered to Cyprus | REST API (CSV/JSON) |
| **HRDA/AnAD** | 309 occupation forecasts (2022-2032), expansion + replacement demand | PDF / web tool |
| **EURES** | Shortage/surplus occupations, vacancy statistics by ESCO occupation | Web dashboard |
| **CEDEFOP** | Skills forecasts to 2035 by sector and occupation group | PDF / interactive tool |
| **CYSTAT** | Aggregate employment, unemployment, labour costs | CYSTAT-DB / data.gov.cy |

## Architecture

```
Cyprus pipeline:
  ISCO-08 data ──► generate_cy_occupations.py ──► occupations_cy.json
  Eurostat API ──► make_cy_csv.py ─────────────► occupations_cy.csv
                                                        │
  LLM (OpenRouter) ──► score.py ──► scores.json ◄──────┘
                                         │
                     build_site_data.py ──┘──► site/data.json ──► site/index.html

Legacy BLS pipeline (still functional):
  BLS HTML ──► scrape.py ──► parse/make_csv.py ──► occupations.csv ──► ...
```

## LLM-powered colouring

The repo includes a pipeline for scoring occupations using LLMs via OpenRouter. You write a prompt, the LLM scores each occupation, and the treemap colours accordingly. The "Digital AI Exposure" layer estimates how much current AI will reshape each occupation within the Cyprus/EU labour market context (considering tourism, shipping, financial services, EU Digital Decade targets).

Fork `score.py` to write your own scoring criteria — e.g. green economy relevance, remote work potential, EU Digital Decade alignment.

**What "AI Exposure" is NOT:**
- It does **not** predict that a job will disappear
- It does **not** account for demand elasticity, regulatory barriers, or social preferences
- The scores are LLM estimates, not rigorous predictions

## Key files

| File | Description |
|------|-------------|
| `eurostat.py` | Eurostat SDMX 2.1 REST API client (employment + earnings data) |
| `generate_cy_occupations.py` | Generate `occupations_cy.json` from ISCO-08 classification |
| `make_cy_csv.py` | Build `occupations_cy.csv` from Eurostat data (EUR, ISCO-08) |
| `score.py` | LLM-based AI exposure scoring via OpenRouter (ISCO-08 / Cyprus context) |
| `build_site_data.py` | Merge CSV + scores → `site/data.json` (auto-detects format) |
| `make_prompt.py` | Generate single-file LLM prompt from all data |
| `site/index.html` | Interactive treemap visualization (EUR, ISCO-08, Cyprus) |
| `occupations_cy.json` | Master list of 39 ISCO-08 occupation groups |
| `occupations_cy.csv` | Summary stats: pay (EUR), employment, education, ISCO codes |
| `scores.json` | AI exposure scores (0-10) with rationales |

## Setup

```bash
uv sync                  # install dependencies
uv sync --extra dev      # includes pytest, ruff for development
```

Requires an OpenRouter API key in `.env` (for LLM scoring only):
```
OPENROUTER_API_KEY=your_key_here
```

## Usage

```bash
# Generate occupation list from ISCO-08
uv run python generate_cy_occupations.py

# Fetch Eurostat data and build CSV
uv run python make_cy_csv.py

# Score AI exposure (uses OpenRouter API)
uv run python score.py

# Build website data
uv run python build_site_data.py

# Generate LLM analysis prompt
uv run python make_prompt.py

# Serve the site locally
cd site && python -m http.server 8000
```

## Development

```bash
uv run pytest -v           # run tests (97 tests)
uv run ruff check .        # lint
uv run ruff format .       # auto-format
```

CI runs automatically on push via GitHub Actions (lint + test). See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Currency and classifications

- **Currency:** EUR (€) — all monetary values
- **Occupations:** ISCO-08 (International Standard Classification of Occupations)
- **Sectors:** NACE Rev. 2 (Statistical Classification of Economic Activities)
- **Education:** ISCED 2011 (International Standard Classification of Education)
- **Data period:** Eurostat latest available year, HRDA 2022-2032 forecasts

## Acknowledgements

This project adapts the visualization approach from [karpathy/jobs](https://github.com/karpathy/jobs) for the Cyprus labour market using EU data sources.
