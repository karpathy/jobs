# Australian Job Market Visualiser

A research tool for visually exploring [Jobs and Skills Australia](https://www.jobsandskills.gov.au/data/occupation-and-industry-profiles) occupation data (ANZSCO classification). This is not a report, a paper, or a serious economic publication — it is a development tool for exploring Australian labour market data visually.

## What's here

Jobs and Skills Australia provides detailed occupation profiles covering employment levels, median earnings, employment projections, demographics, and education requirements across the Australian economy. We scrape these profiles and build an interactive treemap visualisation where each rectangle's **area** is proportional to total employment and **colour** shows the selected metric — toggle between projected growth outlook, median pay, education requirements, and AI exposure.

## LLM-powered colouring

The repo includes scrapers, parsers, and a pipeline for writing custom LLM prompts to score and colour occupations by any criteria. You write a prompt, the LLM scores each occupation, and the treemap colours accordingly. The "Digital AI Exposure" layer is one example — it estimates how much current AI (which is primarily digital) will reshape each occupation. But you could write a different prompt for any question — e.g. exposure to humanoid robotics, offshoring risk, climate impact — and re-run the pipeline to get a different colouring. See `score.py` for the prompt and scoring pipeline.

**What "AI Exposure" is NOT:**
- It does **not** predict that a job will disappear. Software developers score 9/10 because AI is transforming their work — but demand for software could easily *grow* as each developer becomes more productive.
- It does **not** account for demand elasticity, latent demand, regulatory barriers, or social preferences for human workers.
- The scores are rough LLM estimates (Gemini Flash via OpenRouter), not rigorous predictions. Many high-exposure jobs will be reshaped, not replaced.

## Data pipeline

1. **Build occupation list** (`build_occupations.py`) — Scrapes the Jobs and Skills Australia occupations index to build `occupations.json` with ANZSCO codes, titles, categories, and URLs.
2. **Scrape** (`scrape.py`) — Playwright (non-headless to avoid bot blocking) downloads raw HTML for all occupation profile pages into `html/`.
3. **Parse** (`parse_detail.py`, `process.py`) — BeautifulSoup converts raw HTML into clean Markdown files in `pages/`.
4. **Tabulate** (`make_csv.py`) — Extracts structured fields (median weekly earnings, education, employment level, growth projections, ANZSCO code) into `occupations.csv`.
5. **Score** (`score.py`) — Sends each occupation's Markdown description to an LLM with a scoring rubric. Each occupation gets an AI Exposure score from 0-10 with a rationale. Results saved to `scores.json`. Fork this to write your own prompts.
6. **Build site data** (`build_site_data.py`) — Merges CSV stats and AI exposure scores into a compact `site/data.json` for the frontend.
7. **Website** (`site/index.html`) — Interactive treemap visualisation with four colour layers: Growth Outlook, Median Pay, Education, and Digital AI Exposure.

## Key files

| File | Description |
|------|-------------|
| `occupations.json` | Master list of Australian occupations with title, URL, ANZSCO code, category, slug |
| `occupations.csv` | Summary stats: median weekly earnings (AUD), education, employment level, growth projections |
| `scores.json` | AI exposure scores (0-10) with rationales for all occupations |
| `prompt.md` | All data in a single file, designed to be pasted into an LLM for analysis |
| `html/` | Raw HTML pages from Jobs and Skills Australia (source of truth) |
| `pages/` | Clean Markdown versions of each occupation page |
| `site/` | Static website (treemap visualisation) |

## Data sources

- **[Jobs and Skills Australia](https://www.jobsandskills.gov.au/)** — Occupation profiles (employment, earnings, demographics, education)
- **[Employment Projections](https://www.jobsandskills.gov.au/data/employment-projections)** — 5 and 10 year employment projections by occupation (Victoria University modelling)
- **[ABS Labour Force Survey](https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia/latest-release)** — Underlying employment data
- **ANZSCO** — Australian and New Zealand Standard Classification of Occupations

## LLM prompt

[`prompt.md`](prompt.md) packages all the data — aggregate statistics, tier breakdowns, exposure by pay/education, growth projections, and all occupations with their scores and rationales — into a single file designed to be pasted into an LLM. This lets you have a data-grounded conversation about AI's impact on the Australian job market without needing to run any code. Regenerate it with `uv run python make_prompt.py`.

## Setup

```
uv sync
uv run playwright install chromium
```

Requires an OpenRouter API key in `.env`:
```
OPENROUTER_API_KEY=your_key_here
```

## Usage

```bash
# Build the occupations list from JSA
uv run python build_occupations.py

# Scrape JSA occupation pages (only needed once, results are cached in html/)
uv run python scrape.py

# Generate Markdown from HTML
uv run python process.py

# Generate CSV summary
uv run python make_csv.py

# Score AI exposure (uses OpenRouter API)
uv run python score.py

# Build website data
uv run python build_site_data.py

# Serve the site locally
cd site && python -m http.server 8000
```

## Notes on Australian data

- **Currency**: All pay figures are in Australian dollars (AUD). Median weekly full-time earnings are converted to annual by multiplying by 52.
- **Classification**: Occupations use the ANZSCO (Australian and New Zealand Standard Classification of Occupations) system, with 4-digit unit groups and 6-digit individual occupations.
- **Employment projections**: Sourced from Jobs and Skills Australia / Victoria University Employment Forecasting model. These do not currently reflect the labour market implications of generative AI adoption.
- **Education**: Uses the Australian Qualifications Framework (AQF) levels rather than US degree classifications.
