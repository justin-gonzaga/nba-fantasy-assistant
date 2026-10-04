---
id: PAPER-001
title: "IEEE LaTeX skeleton + BibTeX from the literature review + CI PDF build"
epic: EP-95 Research paper
phase: 1
component: paper
status: todo
ready: true
size: S
autonomy: auto
gate: none
depends_on: [FND-006, RSCH-001]
areas: [paper/**, .github/workflows/**]
standards: [documentation, ml, evaluation]
assignee:
created: 2026-09-24
completed:
---
# PAPER-001 — IEEE LaTeX skeleton + BibTeX from the literature review + CI PDF build

## Objective
Set up paper/ with the official IEEEtran conference template, the section skeleton from paper/README.md, references.bib generated from verified [R-xx] entries, and a GitHub Actions job that builds the PDF as an artefact.

## Context to read (only these)
- `paper/README.md`
- `docs/project/architecture-decisions.md` Part 9

## Acceptance criteria
- [ ] AC1: paper/main.tex uses IEEEtran (conference mode) with sections I–IX and a `\todo{}` macro that is hidden in final builds
- [ ] AC2: `tools/lit2bib.py` generates paper/references.bib from ml-literature-review.md (verified entries only), with a test
- [ ] AC3: The CI workflow compiles the PDF (latexmk) on changes under paper/ and uploads it as an artefact; a page-count check warns above 7 pages + refs
- [ ] AC4: `just paper` builds locally when TeX is available, or else prints how to get the CI artefact

## Test requirements
The CI job builds the PDF with no LaTeX errors; a citation check confirms every `\cite` key exists in references.bib.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
