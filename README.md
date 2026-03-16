# Australian Job Market Visualiser

An Australian adaptation of [Andrej Karpathy's US Job Market Visualizer](https://github.com/karpathy/jobs), rebuilt with real Australian labour market data from government sources.

**[View the live visualisation](https://ychua.github.io/jobs/)**

## What was adapted

The original repo scraped US Bureau of Labor Statistics (BLS) occupation data, scored AI exposure via an LLM, and rendered an interactive treemap. This fork replaces the entire data pipeline with Australian equivalents:

| Original (US) | Adapted (Australia) |
|---|---|
| Bureau of Labor Statistics (BLS) | Jobs and Skills Australia (JSA) |
| SOC occupation codes | ANZSCO 4-digit unit groups (361 occupations) |
| USD pay figures | AUD median weekly full-time earnings x 52 |
| US degree classifications | Australian Qualifications Framework (AQF) |
| BLS 10-year employment projections | JSA/Victoria University **5-year** projections |
| 143M total employment | 14.4M total employment |
| 24% of jobs in declining occupations | 5% of jobs in declining occupations |

## What's here

An interactive treemap where each rectangle's **area** is proportional to total employment and **colour** shows the selected metric — toggle between projected growth outlook, median pay, education requirements, and AI exposure. Click any tile to view its full JSA profile.

## Data sources

All data is from official Australian government publications:

- **[JSA Occupation Profiles (Nov 2025)](https://www.jobsandskills.gov.au/data/occupation-and-industry-profiles)** — Employment levels, median weekly earnings, demographics, education attainment for 358 ANZSCO 4-digit occupations
- **[JSA Employment Projections (May 2025–2035)](https://www.jobsandskills.gov.au/data/employment-projections)** — 5 and 10 year growth projections by occupation (Victoria University modelling)
- **[ABS Employee Earnings and Hours (May 2025)](https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions/employee-earnings-and-hours-australia/latest-release)** — Detailed earnings data cubes

The raw Excel files are in `data/`.

## Data pipeline

1. **Build occupation list** (`build_occupations.py`) — Scrapes the JSA occupations index to build `occupations.json` with ANZSCO codes, titles, categories, and URLs.
2. **Scrape** (`scrape.py`) — Playwright downloads raw HTML for all occupation profile pages into `html/`.
3. **Parse** (`parse_detail.py`, `process.py`) — BeautifulSoup converts raw HTML into clean Markdown files in `pages/`.
4. **Tabulate** (`make_csv.py`) — Extracts structured fields into `occupations.csv`.
5. **Score** (`score.py`) — Sends each occupation's Markdown description to an LLM with a scoring rubric (0–10 AI exposure). Results saved to `scores.json`.
6. **Build site data** (`build_real_data.py`) — Parses the JSA and ABS Excel files directly and merges with AI exposure scores into `site/data.json`.
7. **Website** (`index.html`) — Interactive treemap with four colour layers: Growth Outlook, Median Pay, Education, and Digital AI Exposure.

## LLM-powered colouring

The "Digital AI Exposure" layer estimates how much current AI will reshape each occupation. But you could write a different prompt for any question — e.g. exposure to humanoid robotics, offshoring risk, climate impact — and re-run the pipeline. See `score.py` for the prompt and scoring pipeline.

**Caveat:** These are rough LLM estimates, not rigorous predictions. A high score does not predict a job will disappear. Software developers score 9/10 because AI is transforming their work — but demand could easily *grow* as productivity increases. The scores do not account for demand elasticity, latent demand, regulatory barriers, or social preferences for human workers.

## Key files

| File | Description |
|------|-------------|
| `build_real_data.py` | Parses government Excel files into `site/data.json` |
| `occupations.json` | Master list of 361 ANZSCO 4-digit occupations |
| `scores.json` | AI exposure scores (0–10) with rationales |
| `data/` | Raw government Excel data files (JSA, ABS) |
| `site/` | Static website (treemap visualisation) |
| `index.html` | Treemap (also at repo root for GitHub Pages) |

## Setup

```
uv sync
uv run playwright install chromium
```

Requires an OpenRouter API key in `.env` for AI exposure scoring:
```
OPENROUTER_API_KEY=your_key_here
```

## Usage

```bash
# Build site data from government Excel files (no API needed)
python build_real_data.py

# Serve the site locally
cd site && python -m http.server 8000

# Or re-run the full pipeline from scratch:
uv run python build_occupations.py   # build occupation list
uv run python scrape.py              # scrape JSA pages
uv run python process.py             # parse HTML to Markdown
uv run python make_csv.py            # generate CSV
uv run python score.py               # score AI exposure (needs API key)
uv run python build_site_data.py     # merge into site/data.json
```

## Methodology differences vs US version

The Australian visualisation looks noticeably more optimistic than the US version. Key reasons:

- **Projection horizon**: Australia uses **5-year** growth projections (May 2025–May 2030) while the US uses **10-year** BLS projections. The magnitudes are roughly comparable (+6.6% AU 5yr vs +3.4% US 10yr), but they measure different time spans.
- **Fewer declining occupations**: Only 5% of Australian jobs are in occupations with negative 5-year growth, vs 24% for US 10-year projections. This reflects Australia's strong population growth from immigration, which sustains demand across most occupations. Even over 10 years, only 13 of 358 Australian occupations are projected to decline.
- **The projections do not account for AI**: The JSA/Victoria University model projects employment based on historical trends, demographics, and industry structure. It does not currently reflect the potential labour market impact of generative AI adoption.
- **Currency**: AUD pay figures are not directly comparable to USD. At current exchange rates (~0.65 USD/AUD), an Australian median of A$92K is roughly US$60K.
- **Education system**: Australia uses the Australian Qualifications Framework (AQF) — Certificate I–IV, Diploma, Bachelor degree, etc. — rather than US degree classifications (Associate's, Bachelor's, Master's). The education groups are not directly comparable.
- **Coverage**: 296 of 361 occupations have real earnings data from JSA; the remaining 65 (mostly farmers, defence, niche trades) are estimated from ANZSCO skill levels.

## Notes on Australian data

- **Currency**: All pay figures are in Australian dollars (AUD). Median weekly full-time earnings are converted to annual by multiplying by 52.
- **Classification**: ANZSCO (Australian and New Zealand Standard Classification of Occupations) 4-digit unit groups. 8 major groups: Managers, Professionals, Technicians & Trades, Community & Personal Service, Clerical & Admin, Sales, Machinery Operators & Drivers, Labourers.
- **Employment projections**: JSA / Victoria University Employment Forecasting model (May 2025–May 2035). These do not currently reflect the labour market implications of generative AI adoption.
- **Education**: Uses the Australian Qualifications Framework (AQF) — from Year 10 through Doctoral degree — rather than US degree classifications.
