# Courtside

A free-to-play NBA fantasy simulator: practise an auction draft against a calibrated room of 15 other
managers, then play the season week by week on real box scores. Every number it shows comes with its
evidence, and its projections are published as calibrated distributions and scored against what happened.

Status: in active development. The web app, the data pipeline, the projection baselines and the draft practice
room are built; user accounts, saved leagues and a free NBA data provider are in progress. Current state:
[`docs/project/STATUS.md`](docs/project/STATUS.md).

## What is in here

| Part | Where |
|---|---|
| Web app (React 19, Vite, Tailwind v4) | [`apps/web`](apps/web) |
| API (FastAPI) and pipeline jobs (Cloud Run) | [`apps/api`](apps/api), [`apps/pipeline`](apps/pipeline) |
| Python libraries: core, ingest, features, models, decision, evaluation | [`packages`](packages) |
| Warehouse (dbt on BigQuery: staging, intermediate, marts) | [`warehouse`](warehouse) |
| Infrastructure as code (Terraform, GCP) | [`infra/terraform`](infra/terraform) |
| Specification, architecture and decision records | [`docs`](docs) |
| Research paper (LaTeX) | [`paper`](paper) |

## How it is built

- Point-in-time correctness: time-varying data is read only as of a given instant, so evaluations cannot leak
  the future.
- Medallion data platform: immutable raw files, dbt models, BigQuery marts, on serverless GCP.
- Baselines before machine learning; a method ships only if it beats the baseline in a logged evaluation.
- One format-agnostic decision engine; scoring formats differ only through a single objective interface.
- Explanations are built from structured evidence, never invented text.

Start with the [specification](docs/specification/project-spec.md) and the
[system architecture](docs/architecture/system-architecture.md). Decisions are recorded in
[`docs/architecture/adr`](docs/architecture/adr).

## Working on it

```
python tools/tasks.py status | next | show <ID> | board | validate
```

Work is organised as small tasks with measurable acceptance criteria
([`docs/project/tasks`](docs/project/tasks)). [`CLAUDE.md`](CLAUDE.md) and
[`docs/agents`](docs/agents/agent-architecture.md) describe how an AI coding agent is used on the repository.

## Privacy

Other managers' identities are pseudonymised when data is ingested, and live fantasy-site data is never shown
publicly. No secrets are kept in the repository; configuration comes from environment variables and a secret
manager (see [`env.example`](env.example)).

## Licence

[PolyForm Noncommercial 1.0.0](LICENSE). You may read, run and learn from the code for noncommercial purposes.
For anything commercial, contact the author through GitHub.

NBA names and statistics belong to their owners; this project is not affiliated with the NBA or any fantasy
provider.
