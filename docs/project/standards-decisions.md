# Standards Decisions — pick your options

Version 0.1 · 2026-09-24 · Status: **ALL ITEMS SELECTED** (2026-09-24; gate G-10 approved)

The files in `docs/standards/` are **drafts** that assume the ★ recommended option for each item below. Nothing
becomes a standard until you pick. Once you reply, task **STD-001** rewrites the affected standards to match
and marks them `Accepted`.

**How to reply** (from your phone):
- `accept all recommended`, or
- `accept recommended except S-07 B, S-12 B`, or
- `discuss S-12`, and Claude will expand on that one item.

Items that are also architecture or approval gates are marked 🔗 G-xx; answering here answers both.

---

## Python & code quality → `python.md`, `software-engineering.md`

### S-01 Python version
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **3.13** | Already installed; mature ML wheel support in 2026 | Not the newest |
| B | 3.14 | Newest features and performance | Some ML libs may lag; would need to install it |
| C | 3.12 | Maximum library compatibility | Older; would need to install it |

### S-02 Dependency / environment manager
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **uv (workspace)** | Very fast; one lockfile for the monorepo; manages Python versions; a single binary | Newer tool; config differs from Poetry |
| B | Poetry | Mature, popular | Slower; weak monorepo support |
| C | pip + pip-tools | Minimal, standard | Manual; no workspaces |

### S-03 Type checker
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **mypy --strict** | The reference checker; clear CLI errors; well understood by agents | Slower on large codebases (not an issue at our size) |
| B | pyright / basedpyright | Fast; great in-editor experience (VS Code) | Slightly different semantics from mypy; Node-based |
| C | Astral `ty` | Extremely fast; same vendor as uv/ruff | Young; rule coverage still maturing |

### S-04 Lint & format
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Ruff with a broad rule set** (bugs, security, naive-datetime ban, complexity) | Catches real bugs (e.g. timezone-naive datetimes that cause leakage); one fast tool | More initial noise |
| B | Ruff, minimal rules (style + pyflakes) | Low friction | Misses the classes of bug we care about |
| C | black + isort + flake8 | Classic | Three tools; slower |

### S-05 Test coverage policy
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Floors: 85 % packages, 90 % decision/evaluation, 70 % apps** | Protects the logic that matters most; CI-enforced | Can encourage low-value tests if treated as a goal |
| B | A single 80 % floor | Simple | Treats UI glue the same as decision math |
| C | No floor; review-based | No gaming | Relies on judgement, and agents drift without a gate |

### S-06 TDD strictness
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **TDD required for `packages/*`; test-alongside allowed for apps/UI; exempt for spikes and config** | Rigour where correctness matters; pragmatic elsewhere | Needs judgement at the boundaries |
| B | Strict TDD everywhere | Maximum rigour | Slow for UI/config work; burns Claude usage |
| C | Tests required but order not enforced | Fastest | Weaker design pressure; tests written to fit the code |

### S-07 Dataframe library
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Polars (+ DuckDB SQL)** | Fast, strict typing, lazy engine; pairs well with DuckDB/Arrow | Some libraries (SHAP) need pandas conversion |
| B | pandas | Universal; every example uses it | Slower, looser types, index pitfalls |
| C | DuckDB SQL only | One language | Awkward for ML feature code |

### S-08 Logging
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **structlog, JSON output with run/task/job context** | Queryable; context propagation; good for the dashboard's System page | Less readable raw (a pretty console renderer is used in dev) |
| B | stdlib logging, text | Zero dependencies | Hard to query; no structured context |

---

## Data engineering → `data-engineering.md`

### S-09 Transformation tool
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **dbt-core + dbt-duckdb** | Tests, contracts, SCD2 snapshots, lineage docs; huge community; agents write it well | Jinja-SQL can get messy; dbt Labs/Fivetran merger adds a stewardship risk (Apache-2.0 core) |
| B | SQLMesh | Virtual dev environments, column-level lineage, built-in audits; can read dbt projects | Smaller community; less agent familiarity |
| C | Dataform | Clean SQLX + assertions | **BigQuery-only**, so it forces a cloud warehouse and breaks local-first and $0 cost |
| D | Python/Polars only | One language | No lineage or test framework; logic scatters |

### S-10 Medallion layer naming
**Selected**: **B — dbt-native naming** — 2026-09-24:
- raw files (bronze equivalent)
- `staging/` (`stg_`, silver equivalent)
- `intermediate/` (`int_`)
- `marts/` (`dim_`/`fct_`/`mart_`, gold equivalent)

The medallion *concept* (quality gates between layers) is unchanged; only the names are dbt's. ARCH-001 updates the architecture docs and ADR-0006.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **bronze / silver / gold schemas**; dbt model prefixes `stg_` (silver), `dim_`/`fct_`/`mart_` (gold) | The medallion vocabulary you asked for, plus the dbt conventions agents know | Two vocabularies to map (documented once) |
| B | dbt-native `staging / intermediate / marts` only | Pure dbt convention | Less explicit about quality gates between layers |
| C | raw / clean / curated | Plain English | Non-standard |

### S-11 Data-quality tooling
**Selected**: A (dbt tests + dbt_utils/dbt_expectations; Pydantic at ingest; Pandera on feature frames) — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **dbt tests + dbt_utils + dbt_expectations (SQL layers); Pydantic contracts (ingest); Pandera (feature frames)** | Checks live next to the code they protect; no extra service | Three mechanisms (each is small) |
| B | Great Expectations | A comprehensive DQ framework with data docs | Heavy; lots of config; a large context cost for agents |
| C | Soda Core | Readable YAML checks | Another tool, and it overlaps with dbt tests |

### S-12 DQ failure policy
**Selected**: A (error blocks promotion + alert; warn flags) — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Two severities: `error` blocks promotion to the next layer; `warn` promotes but shows on the dashboard. Failed bronze payloads are quarantined** | Safe, and it doesn't halt everything for cosmetic issues | Classifying severity needs judgement |
| B | Everything blocks | Maximum safety | One flaky check stops daily recommendations |
| C | Everything warns (Phase 2), tighten later | Fast start | Bad data can reach recommendations |

### S-13 Orchestration 🔗 ADR-0008
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Typer CLI + job DAG + cron/Task Scheduler; move to Dagster when there are > 15 jobs** | Minimal; cheap for agents; fastest to get snapshots running before tip-off | No lineage/backfill UI (dbt docs covers SQL lineage) |
| B | Dagster from day one | Asset lineage, partitions, backfill UI, great observability | ~0.5–1 GB RAM daemon; big API surface; slower start before 20 Oct |
| C | Prefect | Pleasant Python API | Cloud-leaning; less asset-centric |

---

## ML & evaluation → `ml.md`, `evaluation.md`

### S-14 Literature grounding rule (your requirement)
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Mandatory: every method cites `[R-xx]`; ML approval gates restate references with one-line justifications; ungrounded methods must beat a grounded baseline** | Meets your requirement; forces principled designs | Some research effort per component |
| B | Citations only for gated (major) ML decisions | Less overhead | Smaller choices (e.g. loss functions) go unjustified |

### S-15 Experiment tracking
**Selected**: **B — MLflow** — 2026-09-24 (CV value). Hosting is decided in the ops round.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **JSON run manifests + a `ml_runs` DuckDB table + generated markdown reports** | No server; git-friendly; cheap for agents to read; phone-readable reports | No interactive comparison UI |
| B | MLflow (local, SQLite backend) | Standard UI, model registry, artefact store | Another service; UI isn't mobile-friendly; more context for agents |
| C | Weights & Biases | Best UI | SaaS; data leaves the machine; free tier limits |

### S-16 Model promotion gate
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Statistical: paired block-bootstrap 95 % CI of the improvement excludes 0 on ≥ 2 seasons of walk-forward, no category regresses > 2 %, calibration within bounds** [R-50, R-53–R-55] | Principled; prevents shipping noise | Can block small real gains |
| B | A fixed threshold (e.g. ≥ 3 % MAE improvement) | Simple | Ignores variance; may ship noise |
| C | Owner judgement on a report | Flexible | Needs your time; inconsistent |

### S-17 Validation scheme
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Walk-forward (rolling origin) by week; the most recent season held out** [R-50, R-51] | The standard for temporal data; no leakage | More compute (still minutes) |
| B | Expanding window by season only | Simple | Too few folds; noisy estimates |

---

## Git, CI/CD & releases → `git-workflow.md`, `devops.md`

### S-18 Branching model
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Trunk-based: short-lived `task/<ID>-slug` branches, squash-merged, one task = one commit on main** | Clean history mapped to tasks; minimal merge conflicts between agent sessions; standard for CD | Needs good CI (planned) |
| B | GitHub Flow with merge commits | Preserves the branch history | Noisier `main` history |
| C | Git-flow (`develop`, `release/*`, `hotfix/*`) | Explicit release staging | Heavy for one owner; long-lived branches conflict |

### S-19 Commit messages
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Conventional Commits + a `Task: <ID>` trailer** | Machine-parsable (changelogs, metrics); links commits to tasks | Slight ceremony |
| B | Free-form with the task ID | Simple | Harder to automate |

### S-20 Merge autonomy tiers 🔗 G-11
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Tier A auto-merge when CI is green and the reviewer subagent passes; Tier B (standards, architecture, CI, infra, `.claude/`) needs your approval; Tier C gated work can't start until approved** | Minimal interruptions; you control what matters | Trusts CI and the reviewer for routine code |
| B | You approve every PR | Maximum control | You become the bottleneck; many phone pings |
| C | Everything auto-merges | Fastest | Standards and architecture could drift unnoticed |

### S-21 GitHub plan / branch protection 🔗 G-01
**Selected**: **C — public repo** (revised 2026-09-24 for the CV showcase). Server-side branch protection/rulesets are now free and replace local-only enforcement.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Private repo on GitHub Free, protection enforced by local hooks + the `just ship` script + manual prod deploy** | $0; private | Protection is by convention and hooks, not server-enforced |
| B | Private + GitHub Pro (~US$4/mo) | Real server-side branch protection and environment reviewers | Recurring cost |
| C | Public repo | All protection features free | League data and architecture become public; fixtures must be scrubbed |

### S-22 Release versioning & deployment
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **CalVer tags (`v2026.11.02`) promote a tested image; main auto-deploys to the dev project; prod on tag; automatic rollback** | Clear, dated releases; safe | A manual step per release (one command) |
| B | Continuous deploy of main to prod | Zero ceremony | A bad merge hits your lineup decisions immediately |
| C | SemVer | Familiar | Meaningless without external API consumers |

### S-23 Containers
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **One multi-stage image (non-root, python-slim) + compose; used locally and in prod** | Local = prod parity | You need Docker Desktop on Windows |
| B | No containers until production (Phase 8) | Nothing to install now | Parity problems surface late |
| C | Distroless images | Smaller attack surface | Harder to debug |

---

## Frontend & backend → `frontend.md`, `backend.md`

### S-24 Dashboard framework 🔗 G-07
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **React + Vite + TypeScript SPA served by FastAPI** | Best mobile UX; testable; typed API client | Most code to write (more Claude usage) |
| B | Streamlit | Fastest to build; Python-only | Poor mobile layout; hard to test; reruns the whole app |
| C | HTMX + server templates | Light; Python-centric | Weaker charts and interactivity (e.g. the trade analyser) |
| D | Evidence.dev | Beautiful SQL reports | Weak for interactive tools |

### S-25 Frontend testing depth
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Vitest + Testing Library for components; Playwright e2e for the top 3 flows; axe accessibility checks** | Balanced | Some setup |
| B | Component tests only | Cheaper | Misses integration breaks |

### S-26 API style
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **REST (FastAPI) + OpenAPI → a generated TypeScript client, checked in CI** | Typed end to end; simple | — |
| B | GraphQL | Flexible queries | Overkill for one client |

---

## Security & operations → `security.md`, `devops.md`

### S-27 Secrets management
**Selected (2026-09-24, via I6)**: Google Secret Manager per environment; local `.env` holds dev values only; gitleaks; Claude is denied reads of `.env*`/`secrets/`.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **`.env` + a gitignored `secrets/` dir (owner-only), gitleaks, Claude denied read access** | Simple; standard | Plain files on disk |
| B | OS keychain via `keyring` | Encrypted at rest | Awkward in Docker/VPS |
| C | SOPS + age encrypted files in the repo | Versioned, encrypted | A key to manage; more ceremony |

### S-28 Alerting channel
**Selected**: D (same Telegram bot, 'system' message type + healthchecks.io dead-man's switch) — 2026-09-24

> Note (2026-09-24): the owner chose a **Telegram bot** for product notifications (D-34). The simplest setup sends system alerts to the same bot. That option is added as D below.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **ntfy.sh push notifications + a healthchecks.io dead-man's switch (both free)** | Instant phone alerts; catches "the job never ran" | Two small external services |
| B | Email only | Simple | Easy to miss |
| C | Dashboard only | No external services | You must look to notice |
| D | **Same Telegram bot as D-34** (separate "system" messages) + healthchecks.io dead-man's switch | One app for everything; free | Mixes ops noise with advice (mitigated by message types) |

---

## Documentation & project management → `documentation.md`, `docs/project/tasks/README.md`

### S-29 Task tracking format (you asked for markdown in the repo)
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **One `.md` file per task with YAML front matter (ID, status, deps, acceptance criteria), a generated `BOARD.md`, and a small `tools/tasks.py` CLI (next / validate / claim)** | Diff-friendly; agents load one small file; a script picks the next task, not Claude | A tiny script to maintain |
| B | One big `backlog.md` | Simplest | Merge conflicts; agents must read the whole file |
| C | GitHub Issues | Nice UI and mobile app | Not in the repo; needs `gh`; you asked for markdown files |

### S-30 Docs format
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Markdown in the repo + Mermaid diagrams (render on GitHub mobile)** | Versioned with the code; phone-readable | No search UI |
| B | MkDocs Material site | Nice navigation and search | A build step; hosting |

### S-31 Agent/skill evaluation
**Selected**: A — 2026-09-24

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **2–5 scenario evals per skill/agent, run headlessly on change + monthly; never in CI** | Treats agents as software; catches regressions | Costs some Claude usage per change |
| B | Manual spot checks | Free | Regressions go unnoticed |

---

---

## Task specification (added 2026-09-24, owner request: "a standardized approach to task creation")
| Item | Options | Selected |
|---|---|---|
| S-32 (T1) AC format | ★testable outcome + `Verify:` line · Given/When/Then · free-form checklist | **A** — 2026-09-24 |
| S-33 (T2) Evidence | ★evidence table in the task (one row per AC) · PR description only · CI artefacts only | **A** — 2026-09-24 |
| S-34 (T3) Enforcement | ★script (`tasks.py validate`/`done`) + reviewer quality check · reviewer only | **A** — 2026-09-24 |
| S-35 (T4) Creation | ★`/new-task` skill + `_template.md` · manual template copy | **A** — 2026-09-24 |

## Claude Code usage (added 2026-09-25, owner request: "maximise Claude using best practices")
Source: code.claude.com/docs/en/best-practices (fetched 2026-09-25).

| Item | Options | Selected |
|---|---|---|
| S-36 (C1) Verification gate | ★Stop hook (`just check`) + `/goal` with the task ACs · Stop hook only · prompt-level only | **Stop hook + /goal** |
| S-37 (C2) Review | ★reviewer subagent + built-in `/code-review` · + GitHub Action review · reviewer only | **Reviewer only** (owner) |
| S-38 (C3) Session setup | status line · Python code intelligence plugin · compaction rules · permissions tune-up (auto mode + allowlist + sandbox) | **All four** |
| S-39 (C4) Scheduled Claude work | ★weekly light routine · on request only · daily | **Weekly light routine** (after the GitHub repo exists) |

## Accounts, privacy and hygiene (added 2026-10-04, owner requests: user-data ruleset; "no duplication or orphaned code")

### S-40 The user-data and authentication standard
**Learn**: a standard is a rule set that tasks must satisfy and that CI or a reviewer can check. `docs/standards/user-data-and-auth.md`
has rules UDR-01..UDR-40, each with an "Enforced by" task, built from NIST SP 800-63B, OWASP ASVS and Cheat Sheets and
Google's Identity Platform docs (research note `docs/research/user-data-privacy-and-auth.md`). It was a PROPOSAL until you approved it on 2026-10-04; you
approve it. Not legal advice.
| Option | Pros | Cons |
|---|---|---|
| ★ A Approve as written, with the four unverified facts settled by RSCH-010 | Rules exist before code; SEC-002 can check them | Some values (retention, session limits) are design values you may want to change |
| B Approve only the rules for Google + email/password now, add phone rules when phone is enabled | Smaller | Two review passes |
| C Keep as guidance, not a standard | No process | Nothing enforces it; SEC-002 has nothing to check against |
**CV value**: a compliance matrix mapped to NIST/ASVS is a strong security-engineering artefact.

### S-41 Dead-code and duplication tooling (HYG-002)
**Learn**: *dead code* is code nothing calls; *duplication* is copy-pasted blocks. Tools find them from the code alone.
| Option | Pros | Cons | Cost |
|---|---|---|---|
| ★ A `vulture` (Python), `knip` (TypeScript), `jscpd` (both, duplicates) | Widely used, one per job, run offline from the lock file | Three dev dependencies; framework entry points need a whitelist; a few false positives to triage | US$0 |
| B Only `ruff` rules for unused imports/variables plus the TS compiler's `noUnusedLocals` | No new dependencies | Misses unused functions, exports and files; no duplication check | US$0 |
| C Skip tools; rely on the reviewer subagent | No setup | Not repeatable; misses what a diff does not show | review time |
**CV value**: automated code-health gates read well on a DE/SWE CV.

## Summary of recommendations

S-01 A · S-02 A · S-03 A · S-04 A · S-05 A · S-06 A · S-07 A · S-08 A · S-09 A · S-10 A · S-11 A · S-12 A ·
S-13 A · S-14 A · S-15 A · S-16 A · S-17 A · S-18 A · S-19 A · S-20 A · S-21 A · S-22 A · S-23 A · S-24 A ·
S-25 A · S-26 A · S-27 A · S-28 A · S-29 A · S-30 A · S-31 A · S-40 A · S-41 A
