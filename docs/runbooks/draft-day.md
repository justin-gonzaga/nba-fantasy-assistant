# Draft day runbook

**Draft:** Sun 18 Oct 2026, 17:00 Sydney (02:00 EDT). 16 teams, $200, 30 s to nominate, 20 s to bid.
**Board:** https://claude.ai/artifact/XLR6im1meRD3VSyN96xJAU (private; sign in to claude.ai)

---

## Thu 15 Oct: dry run (30 min, with Claude)
1. Open the board on your **phone and laptop**.
2. **My team**: pick your slot number (Team 1–16 = draft order; keep your own list of who is who).
3. Record 5 fake sales (tap player → team → price → **Save**):
   - one of them yours
   - one priced above a team's max bid (you should see a warning; Save twice to force it)
4. Check the phone and laptop show the same sales. Try **Undo last pick** and **Unsell**.
5. Turn wifi off, record a sale, turn it back on: it should say "waiting to save", then "Saved online".
6. Claude clears the test sales afterwards and lists anything that broke.

## Fri 16 – Sat 17 Oct: final data (Claude runs these, laptop at home)
1. `python -m fantasy_pipeline preseason-backfill --first 2026-27 --last 2026-27` (this October's exhibition games)
2. `python -m fantasy_pipeline draft-pool --refresh commonteamroster` (final rosters)
3. `gcloud storage rsync data/raw gs://nbafa-hdfo-dev-raw/raw --recursive --no-clobber`
4. `just dbt run-operation stage_external_sources` then `just dbt build`
5. `python -m fantasy_pipeline draft-projections --method H1+aging+M1pre`
6. `python -m fantasy_pipeline draft-values --method H1+aging+M1pre`
7. `python -m fantasy_pipeline draft-breakouts` (bounce-back chance) and `python -m fantasy_pipeline draft-preseason` (growth chance)
8. `just draft-sheet`, then Claude republishes the board (same link)
9. You review the injury/absence list (availability overrides) before step 5

## Draft night
**Before 17:00**
- Phone on charge, board open, **My team** set, screen lock off.
- Laptop open as a backup, on the same board link.

**Each player sold (≈ 2 s)**
- Tap the player → pick the **winning team** → type the **price** → **Save**.
- A wrong entry? Tap the player again to correct it, or use **Unsell**.

**When you're bidding**
- **Bid ≤ $X** under each player is your ceiling. It's re-priced for money left in the league and your team fit, and never above your max bid.
- ▲/▼ = fits your build better/worse. **My max bid** is the hard limit.
- **Nominate** list = players others value more than your build does; nominate them to drain rivals' budgets.
- Late in the draft: bounce-back/growth tags are good **$1–3 gambles**, not must-buys.

## Overrides (availability caps and raises)
The file `warehouse/seeds/availability_overrides.csv` adjusts the projection from cited news. You review every row.

| Column | Meaning |
|---|---|
| `status` | `out_indefinitely`, `out_until_date`, `suspended`, `questionable_start`, `holdout` (caps), or `cleared` (raise) |
| `est_games_missed` / `expected_return` | caps only: games missed, or the return date |
| `expected_games` | `cleared` only: games you expect (1–82). Raises games, never lowers them |
| `expected_mpg` | `cleared` only: minutes per game (1–40). Sets minutes; counting stats scale by the minutes ratio, FG%/FT% unchanged |
| `source_url`, `source_date`, `quote` | required: the article, its date (on or before the draft) and a verbatim quote |

**Add a raise** (e.g. "Giannis cleared, no minutes limit"): one row, `status = cleared`, with `expected_games`
and/or `expected_mpg` plus the evidence. A player can't have both a cap row and a raise row (rejected).
**What changes**: the next daily run re-publishes values; the player shows an **Adjusted** badge whose reason quotes
the source. **Undo**: delete the row (via a PR); the next run restores the model's numbers.
Bad rows (no source, values out of range, late source date, contradictions) stop the run with a clear message.

## If something breaks
| Problem | Do this |
|---|---|
| "Saved on this device only" | Keep going; picks sync when it reconnects. Don't switch devices until it says "Saved online". |
| Board won't load | Use the laptop tab; if both fail, open `data/draft/auction_board.csv` and go by **$** and **tier**. |
| Numbers look wrong | Trust **My max bid** (the budget rule) over any advice; tell Claude after. |
| Yahoo draft room issues | Yahoo's autodraft uses Yahoo's own list; the board still tracks prices if you keep recording. |

## After the draft
- Claude reads the recorded sales (the board's saved picks) to set up your team for in-season help.
