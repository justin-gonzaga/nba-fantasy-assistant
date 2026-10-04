# Reuse register — what Courtside gives the next project

The owner plans a second, **commercial** product built on what this repo teaches: a Japanese kanji trainer for JLPT
preparation. This register is the single place that says what is reusable, where it lives, and what must change.
It sits beside the lessons ledger (`lessons.md`, the "what we learned") and the generalisation plan
(`generalisation-plan.md`, the "how we extract it").

## How it stays current (the rule)

1. Closing a task: if anything in it is reusable, add a row to `lessons.md` (layer H, P or D) and, for a file or
   pattern, a row below. A task that adds a platform or harness file also classifies it in `platform-manifest.yaml`.
2. Platform and harness files stay project-agnostic (D-46, D-58): no NBA words, no fantasy imports. If a feature is
   generic but written with domain names (an e2e route list, a copy string), put the generic part in a platform file
   and the names in a domain file.
3. At each milestone, re-read this page and move "candidate" rows to "ready" when the extraction is tested.

## Reuse map

Status: **ready** = copy or template it now; **candidate** = generic in spirit, still carries NBA names;
**rewrite** = idea carries over, code does not.

| Asset | Where | Status | For the kanji project |
|---|---|---|---|
| Task harness: `tools/tasks.py`, task spec standard, board, gates, owner decision menus (D-xx, S-xx) | `tools/`, `docs/project/tasks/README.md`, `.claude/` | ready (HARN-002/003 package it) | Use as is; first task is the spec |
| Standards: engineering, testing, definition of done, git workflow, design language, ML evidence rule (`[R-xx]` per method) | `docs/standards/` | ready | Edit domain words; keep the evidence rule |
| Accounts, privacy and security ruleset | `docs/standards/user-data-and-auth.md` | ready | A commercial app starts from it; add payments and app-store terms |
| Lessons ledger and layer manifest | `docs/platform/`, `platform-manifest.yaml` | ready | Same process in the new repo |
| Evaluation kernel: scoring rules, calibration, bootstrap, the `eval-gate` | `packages/core`, `packages/evaluation` | candidate | Calibrate recall probabilities (log loss, Brier, reliability); gate every model against a baseline first |
| Point-in-time reads (`AsOfReader`, injected `Clock`) | `packages/core` | ready | Needed for honest replay of a learner's history (no leaking later answers into earlier predictions) |
| Medallion data layout: raw (immutable) → dbt → marts | `warehouse/`, `packages/ingest` | candidate | Data sets here are small and static; BigQuery may be more than needed. Decide in a menu item |
| Terraform GCP, CI, workload identity, secrets | `infra/terraform`, `.github/` | candidate | Same module with a prefix; hosting, scheduler and Cloud Run job patterns carry over |
| Web shell: React 19, Vite, Tailwind v4 tokens, UI kit, tab bar, sheets, motion rules, reduced-motion | `apps/web/src/components/ui`, `index.css` | candidate | Strong start for a phone-first study app; swap the brand tokens |
| Phone persona e2e: fit at 320 to 390 px, 16 px controls, steady tab bar, axe, screenshot loop | `apps/web/e2e/` (`phone.spec.ts`; `mobile-fit.spec.ts` is in PR 134, WEB-040) | candidate | Move the route list into a config so the spec is platform |
| Sound and motion kit: audio port, cue player, prefs, ring clock (DRAFT-020) | `apps/web/src/features/draft/fx/` (in progress, DRAFT-020, not yet merged) | candidate | A review session wants the same: correct/wrong cues, timer ring, mute and reduced motion |
| Decision log pattern: structured evidence → recommendation → explanation, no invented facts | `packages/decision`, architecture §2 | rewrite | "Why this kanji next" explained from evidence (your misses, frequency rank) |
| Fantasy domain: scoring formats, auctions, Yahoo, projections | `packages/features`, `models`, `apps/pipeline` | not reusable | Leave behind |

## Early notes for the kanji project (not decisions)

- **What it is**: all kanji by JLPT level (N5 to N1); multiple-choice drills; a model of what the learner knows,
  used to pick the next question and to show which kanji need work; frequency data so common kanji come first.
- **Model direction** (to be chosen from a menu with `[R-xx]` sources, baselines first): a per-kanji recall
  probability from answer history (Elo or item-response style), then spaced-repetition scheduling (FSRS is open
  source) and distractor choice from confusable kanji. The baseline is "fixed order by frequency".
- **Data and licences** (researched 2026-10-04, `docs/research/kanji-datasets-licensing.md`; not legal advice, a lawyer
  must review before launch):
  - Safe, attribution only: Waller's tanos.co.uk N5-N1 kanji lists (CC "BY", version unstated), Japanese government
    Joyo and grade tables, Tatoeba sentences (CC0 subset), FSRS scheduling (MIT), and your own character counts from
    public-domain Aozora Bunko text.
  - Usable with conditions: KANJIDIC2, JMdict, KRADFILE (EDRDG = CC BY-SA 4.0, commercial use allowed, but derived
    data must stay share-alike and there is a "regular updating" duty) and KanjiVG (CC BY-SA 3.0). Keep these in a
    separate, clearly licensed data package and ask a lawyer how far share-alike reaches.
  - Avoid: BCCWJ (no commercial use without a NINJAL contract), Kanjium as a whole, Tatoeba audio, Wikipedia text.
    Google Books Ngram has no Japanese data. The Leeds list licence is still unverified.
  - No official N5-N1 kanji list exists (the JLPT stopped publishing lists), and the KANJIDIC2 `jlpt` field is the old
    1-4 scale where N3 cannot be recovered. Say "JLPT-aligned", never "official", and do not use the JLPT logo.
- **Commercial extras** this repo never needed: payments, app-store rules, a minors policy (the learner base skews
  young), refund and consumer law, and a trademark check on the name.
- **First step there**: a spec (user stories, edge cases, ACs) and a licence-and-data research task, as here.
