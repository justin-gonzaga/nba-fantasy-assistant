# Project command surface (devops standard §1). Humans, Claude and CI all use these recipes.
# Recipes only call uv/python/git, so they behave the same under PowerShell (Windows) and sh (Linux/CI).

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

# List the available recipes
default:
    @just --list

# Install the Python toolchain + dependencies and the pre-commit git hook
setup:
    uv sync
    uv run pre-commit install

# Fast checks: format, lint, types, unit tests, task-file validation
check:
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy
    uv run lint-imports
    uv run pytest -q -m "not integration"
    uv run python tools/tasks.py validate
    uv run python tools/manifest_check.py

# Full local CI: the fast checks + tests with the coverage gate
ci-local: check
    uv run pytest -q --cov --cov-report=term

# Run tests (pass extra pytest args, e.g. `just test packages/core -k clock`)
test *args:
    uv run pytest {{args}}

# Project status (tasks + gates; data freshness joins in DATA-023)
status:
    uv run python tools/tasks.py status

# Task CLI passthrough, e.g. `just task next`, `just task show FND-003`
task *args:
    uv run python tools/tasks.py {{args}}

# Tools, logins and secret presence (never prints secret values)
doctor:
    uv run python tools/doctor.py

# dbt passthrough against the warehouse project, e.g. `just dbt build`, `just dbt source freshness`
dbt *args:
    uv run --group warehouse dbt {{args}} --project-dir warehouse --profiles-dir warehouse

# Web app (apps/web) through pnpm, e.g. `just web test`, `just web dev`, `just web build`
web *args:
    corepack pnpm@10 --dir apps/web {{args}}

# Persona e2e (WEB-008): the normal build carries no e2e code, then Playwright builds the demo and
# e2e-live modes and runs every persona on iPhone 13, Pixel 7 and desktop, e.g. `just web-e2e -g stranger`
web-e2e *args:
    corepack pnpm@10 --dir apps/web build
    node apps/web/scripts/check-no-e2e.mjs apps/web/dist
    node apps/web/scripts/check-chunk-size.mjs
    corepack pnpm@10 --dir apps/web exec playwright test {{args}}

# Visual QA (design-language §9): full-page screenshots of every route, phone + desktop, into apps/web/screens/
web-screens $SCREENS="1":
    corepack pnpm@10 --dir apps/web build
    corepack pnpm@10 --dir apps/web exec playwright test e2e/screens.spec.ts --project=desktop-chrome --project=iphone-13

# The API contract -> TypeScript: refresh apps/api/openapi.json, then the SPA's generated types
api-client:
    uv run fantasy-api --write-openapi
    corepack pnpm@10 --dir apps/web api:types

# Auction board for draft night (HTML + CSV) from the latest predictions
draft-sheet *args:
    uv run python -m fantasy_pipeline draft-sheet {{args}}

# Full mock auction on the live values; times every helper update (DRAFT-005)
draft-mock *args:
    uv run python -m fantasy_pipeline draft-mock {{args}}
