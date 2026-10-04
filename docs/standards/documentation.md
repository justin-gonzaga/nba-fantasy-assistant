# Documentation Standard

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

## 1. What lives where
| Doc | Path | Updated when |
|---|---|---|
| Project spec | `docs/specification/project-spec.md` | scope or requirements change (Tier B) |
| Architecture | `docs/architecture/system-architecture.md`, `ml-and-decision-design.md` | a component/interface/flow changes, together with an ADR |
| ADRs | `docs/architecture/adr/NNNN-title.md` | any decision that is hard to reverse, costs money, or changes a boundary |
| Component docs | `packages/<x>/README.md`, `apps/<x>/README.md` | the component's public interface changes |
| Data contracts | the Pydantic contracts + dbt YAML (the docs **are** the code); summarised in `docs/data/sources.md` | a source changes |
| API | generated OpenAPI (`just api-docs`) | automatically |
| Methodology | `ml-and-decision-design.md`, model cards, `docs/research/ml-literature-review.md` | a model or method changes |
| Evaluation reports | `docs/evaluation/reports/` | every experiment, gate, and weekly report |
| Runbooks | `docs/runbooks/<topic>.md` | any operational procedure (token refresh, backfill, restore, deploy) |
| Local dev guide | `docs/guides/local-development.md` | setup changes |
| Project state | `docs/project/STATUS.md`, `roadmap.md`, `tasks/`, `human-approval-gates.md` | every task transition |
| Research | `docs/research/` | new findings. **Cite, don't repeat** |

## 2. Style
- Put the conclusion first and the details after. Use tables for comparisons.
- Write for phone reading: short sections, no wide ASCII art, and Mermaid for diagrams.
- Every doc starts with version/date/status.
- Link to docs rather than duplicating them. If two docs disagree, **the ADR wins**, then the architecture, then everything else, and the conflict is fixed in the same PR.
- Research claims carry a source URL and an access date. Assumptions are labelled `A-xx` or `UNVERIFIED`.

## 3. ADR process
- Template: `docs/architecture/adr/0000-template.md`. Statuses: `Proposed`, `Accepted`, `Superseded by NNNN`, `Rejected`, `Deprecated`.
- Create one with `/adr <title>` (the skill) or by copying the template. Numbers are sequential.
- An agent may write `Proposed` ADRs. **Only the owner** moves an ADR to `Accepted`, directly or by approving the linked gate.
- ADRs are immutable once accepted. To change one, write a new ADR that supersedes it.

## 4. Doc checks (CI)
- Task-file schema validation (`tools/tasks.py validate`)
- Broken relative links
- The ADR index is up to date
- Every `[R-xx]` cited exists in the literature review
