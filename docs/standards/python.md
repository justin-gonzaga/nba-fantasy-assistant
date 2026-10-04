# Python Standard

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

| Topic | Rule |
|---|---|
| Version | Python **3.13** (`requires-python = ">=3.13,<3.14"`), pinned via `.python-version`; uv installs it |
| Env & deps | **uv workspace**: root `pyproject.toml` lists members `packages/*` and `apps/*`; single `uv.lock` committed; `uv sync --frozen` in CI |
| Adding deps | `uv add --package <member> <dep>`; justify non-trivial deps in the PR; prefer the stdlib or already-present deps |
| Packaging | Each member is a package with a `src/` layout: `packages/ingest/src/fantasy_ingest/`. Distribution names are `fantasy-<name>`, import names `fantasy_<name>` |
| Formatting | `ruff format` (line length 100) |
| Linting | `ruff check` with rule sets `E,F,W,I,B,UP,SIM,C4,C90,N,S,PT,RUF,DTZ,TID,PL` (DTZ bans naive datetimes; TID bans relative parent imports) |
| Types | `mypy --strict` on all packages and apps; `# type: ignore[code]` needs a comment explaining why |
| Tests | `pytest`, `pytest-cov`, `hypothesis`, `pytest-recording`/`respx` for HTTP fixtures; tests live in `<member>/tests/` |
| Coverage | ≥ 85 % line coverage on `packages/*` (the decision and evaluation packages ≥ 90 %); apps ≥ 70 %. Coverage is a floor, not a goal |
| Docstrings | Public functions and classes: one-line summary + Args/Returns only when not obvious. Google style |
| Dataframes | Polars by default; pandas only at library boundaries (e.g. SHAP). Column names are `snake_case` |
| Notebooks | Only in `experiments/`, never imported by packages; outputs stripped by nbstripout; anything reusable graduates into a package with tests |
| Commands | Always `uv run …` or `just …`; never bare `pip` |
