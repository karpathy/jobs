# Contributing to JobsCY

## Development setup

```bash
# Clone and install
git clone https://github.com/alezenonos/jobscy.git
cd jobscy
uv sync --extra dev
```

## Branch conventions

- **Default branch:** `master`
- Feature branches: `claude/<description>`
- PRs target `master`

## Code quality

All code must pass lint and tests before merging:

```bash
uv run ruff check .          # lint — must be clean
uv run ruff format --check . # format — must be clean
uv run pytest -v             # tests — must all pass
```

CI enforces these automatically on push and PR.

### Ruff configuration

- Target: Python 3.10+
- Line length: 120
- Rules: E, F, W, I, N, UP, B, SIM (E501 ignored)

## Testing

Tests are in `tests/` and use `pytest`. Run with:

```bash
uv run pytest -v                         # all tests
uv run pytest tests/test_eurostat.py -v  # single file
uv run pytest --cov=. --cov-report=term  # with coverage
```

When adding new functionality:
- Add tests in the corresponding `tests/test_<module>.py` file
- Use mocked HTTP responses for external API calls (Eurostat, OpenRouter)
- Keep test data minimal — avoid large fixtures

## Project conventions

### Currency and classifications
- **EUR (€)** — never USD. Use `fmt_pay()` for formatting.
- **ISCO-08** for occupations (10 major groups, 39 sub-major groups at 2-digit level)
- **NACE Rev. 2** for economic sectors
- **ISCED 2011** for education levels
- **Eurostat dataset codes:** `LFSA_EGAI2D` (employment), `earn_ses_pub1s` (earnings)

### Data pipeline
The Cyprus pipeline flows: `generate_cy_occupations.py` → `make_cy_csv.py` → `score.py` → `build_site_data.py` → `site/index.html`. Each step can be run independently if its inputs exist.

### File naming
- Cyprus data files: `occupations_cy.json`, `occupations_cy.csv`
- Legacy BLS files: `occupations.json`, `occupations.csv`
- Scripts auto-detect format and prefer Cyprus files when both exist

## Pull request process

1. Create a feature branch from `master`
2. Make changes, add/update tests
3. Run `uv run ruff check . && uv run ruff format --check . && uv run pytest -v`
4. Update `HANDOVER.md` if the change affects project status
5. Open PR against `master`
