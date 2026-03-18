# JobsCY — Cyprus Job Market Visualizer

An interactive treemap visualization of the Cyprus labour market, with AI exposure scoring for occupations. Built on data from EU/Cyprus sources including [HRDA/AnAD](https://www.anad.org.cy), [Eurostat](https://ec.europa.eu/eurostat), and [EURES Cyprus](https://eures.europa.eu).

## What's here

The Cyprus labour market covers **309 occupations** (per HRDA 2022-2032 forecasts) spanning every sector of the economy. We collect structured data on employment counts, wages, education requirements, and growth projections from EU and Cypriot statistical sources, then build an interactive treemap where each rectangle's **area** is proportional to total employment and **color** shows the selected metric — toggle between projected growth, median pay (EUR), education level, and AI exposure.

## Data sources

| Source | What it provides | Format |
|--------|-----------------|--------|
| **HRDA/AnAD** | 309 occupation forecasts (2022-2032), expansion + replacement demand | PDF / web tool |
| **Eurostat API** | Employment by ISCO-08 (2-digit), wages by ISCO-08 (1-digit), filtered to Cyprus (`geo=CY`) | REST API (CSV/JSON) |
| **EURES** | Shortage/surplus occupations, vacancy statistics by ESCO occupation | Web dashboard |
| **CEDEFOP** | Skills forecasts to 2035 by sector and occupation group | PDF / interactive tool |
| **CYSTAT** | Aggregate employment, unemployment, labour costs | CYSTAT-DB / data.gov.cy |
| **Job boards** | Current demand signals (Ergodotisi, Carierista) | Web scraping |

## LLM-powered coloring

The repo includes a pipeline for scoring occupations using LLMs via OpenRouter. You write a prompt, the LLM scores each occupation, and the treemap colors accordingly. The "Digital AI Exposure" layer estimates how much current AI will reshape each occupation. Fork `score.py` to write your own scoring criteria — e.g. green economy relevance, remote work potential, EU Digital Decade alignment.

**What "AI Exposure" is NOT:**
- It does **not** predict that a job will disappear. Software developers score high because AI is transforming their work — but demand could easily *grow*.
- It does **not** account for demand elasticity, regulatory barriers, or social preferences for human workers.
- The scores are LLM estimates, not rigorous predictions.

## Data pipeline

1. **Fetch** — Retrieve occupation data from Eurostat API and HRDA sources into structured format.
2. **Parse** — Extract and normalize occupation descriptions, employment figures, and wage data.
3. **Tabulate** (`make_csv.py`) — Build `occupations.csv` with structured fields: pay (EUR), education, job count, growth outlook, ISCO code.
4. **Score** (`score.py`) — Send each occupation description to an LLM with a scoring rubric. Each occupation gets an AI Exposure score (0-10) with rationale. Results saved to `scores.json`.
5. **Build site data** (`build_site_data.py`) — Merge CSV stats and AI exposure scores into `site/data.json`.
6. **Website** (`site/index.html`) — Interactive treemap with colour layers: Growth Outlook, Median Pay (EUR), Education, and Digital AI Exposure.

## Key files

| File | Description |
|------|-------------|
| `occupations.json` | Master list of occupations with title, ISCO code, category, slug |
| `occupations.csv` | Summary stats: pay (EUR), education, job count, growth projections |
| `scores.json` | AI exposure scores (0-10) with rationales |
| `prompt.md` | All data in a single file for LLM analysis |
| `site/` | Static website (treemap visualization) |

## Setup

```bash
uv sync
uv sync --extra dev   # includes pytest, ruff for development
```

Requires an OpenRouter API key in `.env` (for LLM scoring only):
```
OPENROUTER_API_KEY=your_key_here
```

## Usage

```bash
# Generate CSV summary from data sources
uv run python make_csv.py

# Score AI exposure (uses OpenRouter API)
uv run python score.py

# Build website data
uv run python build_site_data.py

# Serve the site locally
cd site && python -m http.server 8000
```

## Development

```bash
# Run tests
uv run pytest -v

# Run linter
uv run ruff check .

# Auto-format
uv run ruff format .
```

CI runs automatically on push via GitHub Actions (lint + test).

## Currency and metrics

All monetary values are in **EUR (€)**. Employment projections follow EU/Cyprus statistical frameworks (ISCO-08, NACE Rev. 2, ISCED 2011). Growth projections are sourced from HRDA 2022-2032 forecasts and Eurostat Labour Force Survey data.

## License

This project adapts the visualization approach from [karpathy/jobs](https://github.com/karpathy/jobs) for the Cyprus labour market using EU data sources.
