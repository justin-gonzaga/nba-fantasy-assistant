# Commercial View — the build in plain English

_Last updated: 2026-09-28 · Stage: **draft tools built; the daily brief (first useful in-season output) is built and waits for the real league data**_

This is a running, jargon-free account of what the project is, how far along it is, and how it would look if
it were ever turned into a product. The project is a **personal tool**, and nothing here commits it to becoming a
business. This page keeps that option visible and keeps an honest account of what would stand in the way.

---

## 1. The one-paragraph pitch

Fantasy basketball managers make dozens of small decisions every week: who to start, who to pick up,
who to drop, whether a trade is fair. Most tools give generic player rankings. This assistant instead looks at
**your team, your league's exact rules, and this week's opponent**, then says what to do, why, and how confident it
is. It also keeps score of its own advice, so you can see whether following it actually helped.

## 2. Progress at a glance

| Area | Status | In plain English |
|---|---|---|
| Plan and design | ✅ Done (awaiting owner choices) | We know what to build, in what order, and why. The key technical choices are laid out as options for the owner. |
| Data collection | ✅ Running daily | Every morning it records the NBA schedule, results, stats and the official injury report (the league's own data arrives by paste after the draft) |
| First useful output | 🟨 Built, launching 20 Oct | A daily Telegram message: who to start, who is hurt, who to pick up. Tested end to end on a sample league; needs the real rosters after the 18 Oct draft |
| Proof that it works | ⬜ Not started | Replaying past weeks to show the advice beats simple alternatives, target around late December |
| Smarter predictions | ⬜ Not started | Machine-learning upgrades that are only kept if they measurably help |
| App / dashboard | 🟨 Designed and started | The screens were designed and picked by the owner; the app runs on sample data and gets real data once the service layer exists |
| Always-on service | ⬜ Not started | Runs by itself without the laptop, target around February |

**Demo-ability today**: the draft board and a sample-league daily brief can be shown now; the real daily brief starts 20 Oct.

## 3. What makes it different (the potential "moat")

1. **It's matchup-aware, not just a ranking.** It values a player by how much he helps *you win this week against this opponent*, under your league's scoring format. That approach follows published research on fantasy basketball strategy (the Rosenof papers in our literature review).
2. **It works for every Yahoo scoring format.** Head-to-head categories, one-win, points, rotisserie, and total points all run on the same engine.
3. **It shows its working.** Every suggestion comes with the facts and numbers behind it, not just an opinion.
4. **It keeps a track record.** Every recommendation is logged and scored afterwards. A season of verified results is persuasive evidence that most tools can't show.
5. **It has a time machine.** Because it records what was known each day, it can honestly test "would this advice have worked last month?" Competitors that only keep current data can't do this. It also can't be caught up on later: the history has to be recorded as it happens.

## 4. What stands between this and a sellable product (honest blockers)

| Blocker | Why it matters | What it would take |
|---|---|---|
| **Yahoo's API terms forbid monetisation** | You can't charge for a product built on Yahoo's API without Yahoo's permission | A partnership or permission from Yahoo, or support for platforms with friendlier terms (e.g. ESPN or Sleeper: to be researched) |
| **The NBA data comes from unofficial free sources** | Fine for personal use, but not something a business should rely on or resell | Licensed data from a commercial provider. Expect roughly $10–$40/month at hobby tier, and substantially more for commercial redistribution rights (to be researched) |
| **Built for one user and one league** | A product needs accounts, many leagues, and per-user Yahoo logins | Multi-user support: account system, per-user data separation, per-user Yahoo authorisation |
| **Privacy** | League data includes other managers' names | Privacy policy, data minimisation, deletion on request |
| **No proof yet** | The track record doesn't exist until a season is logged | Run it for the 2026-27 season and publish the results |

## 5. What keeps its value either way

Even if this never becomes a product, the following parts are reusable:
- the **decision engine**: format-aware simulation and optimisation
- the **evaluation framework**: honest backtesting and a track record
- the **data platform design**
- the **AI-assisted development setup**: how Claude builds and maintains the project

Each of these would carry over to a commercial version, or to other fantasy sports.

## 6. Running cost

| Stage | Monthly cost | Notes |
|---|---|---|
| Today (personal, on the laptop) | $0 | Plus the existing Claude Pro subscription |
| Always-on on Google Cloud (serverless) | ~$0–10 | Mostly free tiers (Cloud Run, BigQuery), plus small Claude API usage for the question-answering feature; a budget alert at $10 |
| Hypothetical small product (a few hundred users) | Rough guess: $50–$500+ | Dominated by licensed sports data, not servers. To be researched properly if pursued |

## 7. Key risks, in plain English

- **Timing**: if data collection doesn't start by tip-off, this season can't be used to prove the advice works.
- **Data sources could break**: the free NBA sources can change without warning. We'll detect this within a day, and a paid backup exists.
- **The smart models might not beat the simple ones**: that's fine, and it's measured. We keep whichever works better.
- **Platform dependence**: Yahoo controls access to league data.

## 8. Commercial decision points (none taken; noted for later)

| When | Question |
|---|---|
| Now (D-31) | How much should the design keep a commercial path open? |
| After M3 (proof it works) | Is the advice good enough that others would pay for it? |
| End of season | Does the track record justify exploring data licensing and platform permissions? |

## 9. Change log

| Date | What changed, commercially speaking |
|---|---|
| 2026-09-24 | Project planned. The differentiators and blockers were identified. No product claims can be made until M3. |
| 2026-09-24 | The owner chose "usable by other people, not built for massive scale": each user connects their own Yahoo account, and friends can be invited. This lowers the "built for one user" blocker; scaling and billing still aren't built. |
| 2026-09-28 | The daily brief is built (data refresh, projections, measured injury odds, lineup and pickup advice, Telegram, a 07:30 schedule). One finding worth a headline: players listed "doubtful" played only 1 % of the time over two seasons. |
