# Minutes projection and injury-designation outcomes (RSCH-002)

Researched 2026-09-27 by the researcher subagent; every new reference opened and checked at the source. New IDs R-99..R-105. Quality: peer-reviewed / practitioner / anecdotal; preprints flagged.

## Answers (conclusion first)

1. **Injury-designation play rates** (Probable / Questionable / Doubtful): **no peer-reviewed or reputable measured source exists.** Numbers like "Probable 90-95 %, Questionable 50 %, Doubtful < 25 %" that circulate online could not be traced to any primary source. The ESPN article on the NBA's December 2025 injury-report changes, fetched directly, states no such percentages. They appear to restate the labels' *definitions*, not measured outcomes. **Decision support: do not hard-code them.** The existing fallback stands: estimate play rate by designation from our own point-in-time injury-report history (2021-22+), with confidence intervals.
2. **Return-to-play duration by injury type** is peer-reviewed (R-99, R-100, R-105):
   - Severe hip, knee and ankle injuries: mean about 227-260 days to return, with no significant difference by site. Only 37 % of players are back to their pre-injury game count after 2 years (R-99).
   - Ankle sprains resolve fastest.
   - Lower-extremity injuries are 40.7-62.4 % of all injuries, and lateral ankle sprain is the most common (13.2 %) (R-105).
   - Confidence: medium. The CIs are wide and the per-injury-type samples small.
3. **Minutes projection**: **no dedicated peer-reviewed paper** predicts NBA minutes per game or rotation share.
   - The adjacent peer-reviewed work concerns availability: injury forecasting (R-104) and load management (R-101-R-103).
   - The best treatment of the in-game mechanics (back-to-backs, blowouts, a teammate's absence) is practitioner only: Rotogrinders, "Accurately Predicting Minutes in NBA DFS". It has no peer review and no error bars. Its heuristics are hypotheses to test, not coefficients to adopt:
     - baseline = 0.75 x season average + 0.25 x last-5 average;
     - about -1.5 % minutes per point of spread above 7;
     - backups absorb an injured starter's minutes, with no quantified split.
   - Confidence: low-medium.

## Search log (2026-09-27)

| Query | Database / site | Hits used |
|---|---|---|
| NBA injury report probable/questionable/doubtful play rate study | Google | 0 (AI-summary numbers, unverifiable) |
| NBA injury report designation predictive value peer-reviewed | Google | led to PMC/MDPI injury papers |
| "questionable" NBA play rate fantasy data study | Google | 0 usable |
| NBA 2023 injury report policy percentages official | Google + ESPN (fetched) | ESPN memo article: no percentages |
| NBA return to play duration by injury type | Google | R-99, R-100 |
| predicting NBA minutes rotation machine learning peer-reviewed | Google | none dedicated |
| NBA back-to-back rest load management minutes study | Google | R-101, R-102, R-103 |
| backup minutes increase when starter injured NBA | Google | Rotogrinders (practitioner) only |
| arxiv NBA minutes prediction rotation garbage time blowout | Google | confirms Rotogrinders as the best available |
| forecasting playing time / injury forecasting NBA peer-reviewed | Google | R-104 |
| Drakos 2010 17-year NBA injury overview | Google + PubMed | R-105 |
| ACL basketball return-to-play meta-analysis | Google | 2025 J. ISAKOS review found; authors not confirmable (PubMed CAPTCHA, publisher 403): **excluded, UNVERIFIED** |

## References

| R-xx | Topic | Status | Citation | Access | Quality | Supports |
|---|---|---|---|---|---|---|
| R-99 | Return to performance after severe injury (NBA) | Verified | Bullock, G. S., Ferguson, T., Arundale, A. H., Martin, C. L., Collins, G. S., & Kluzek, S. (2022). Return to performance following severe ankle, knee, and hip injuries in National Basketball Association players. *PNAS Nexus*, 1(4), pgac176. https://doi.org/10.1093/pnasnexus/pgac176 | Full text | Peer-reviewed | C5 duration priors by injury site; the long tail of reduced availability |
| R-100 | Ankle injury risk factors and time loss (NBA) | Verified | Tummala, S. V., Morikawa, L., Brinkman, J. C., et al. (2023). Characterization of ankle injuries and associated risk factors in the NBA: minutes per game and usage rate associated with time loss. *Orthopaedic Journal of Sports Medicine*. https://doi.org/10.1177/23259671231184459 | Full text | Peer-reviewed | Minutes per game and usage as risk factors for longer absence (554 injuries, 2015-21) |
| R-101 | Rest / load management vs later injury (NBA) | Verified | Herzog, M. M., Brink, A., Gondalia, R., DiFiori, J. P., & Mack, C. D. (2026). The relationship between games missed for rest or load management and injury in the NBA, 2014-15 through 2022-23. *Sports Medicine*, 56(9), 2313-2323. https://doi.org/10.1007/s40279-026-02457-w | Full text (PMC) | Peer-reviewed | Rest did not reduce later injury hazard (all CIs cross 1; 1,233 player-seasons) |
| R-102 | Survivor bias in workload-injury models | Verified (preprint) | Yu, Y., & Hu, G. (2026). The load management paradox: correcting the healthy-worker survivor effect in NBA injury modeling. arXiv:2603.26935 | Full text | Preprint, not peer-reviewed | Naive models understate workload risk; marginal structural models as a remedy |
| R-103 | Age-conditioned effect of rest (NBA) | Verified (preprint) | Nakamura-Sakai, S., Forastiere, L., & Macdonald, B. (2024). Estimating the age-conditioned average treatment effects curves: an application for assessing load-management strategies in the NBA. arXiv:2402.12400 | Abstract | Preprint, not peer-reviewed | Rest effects vary with age: age as a covariate in C2 and C5 |
| R-104 | Deep-learning injury forecasting (NBA) | Verified | Cohan, A., Schuster, J., & Fernandez, J. (2021). A deep learning approach to injury forecasting in NBA basketball. *Journal of Sports Analytics*, 7, 277-289. https://doi.org/10.3233/JSA-200529 | Abstract | Peer-reviewed | Precedent for an injury/availability model with imbalanced-data handling |
| R-105 | NBA injury epidemiology | Verified | Drakos, M. C., Domb, B., Starkey, C., Callahan, L., & Allen, A. A. (2010). Injury in the National Basketball Association: a 17-year overview. *Sports Health*, 2(4), 284-290. https://doi.org/10.1177/1941738109357303 | Abstract | Peer-reviewed | Base rates for the injury-type mix |

Practitioner (not given an R-id): Rotogrinders, "Accurately Predicting Minutes in NBA DFS" (web). Heuristics only.

## Implications for C2 (minutes) and C5 (availability): PROPOSAL

- C2 has no peer-reviewed baseline to cite. The plan should say so and keep the project-specific empirical model (ridge M1, already backtested in DRAFT-007/008) rather than borrow a formula.
- Include age and prior-workload trend as covariates in C2 and C5 (R-100, R-103). Per R-102, beware selection/collider bias when conditioning on "played, not rested".
- Don't treat rest as protective in C5 (R-101). A rest game says something about role and management, not about lower future risk.
- "Backup gains minutes": estimate a project-specific redistribution (minutes-share regression on teammate-out flags by position group). No published coefficient exists.
- Blowout / garbage-time reduction: test the Rotogrinders heuristic on our own data; don't adopt it as a fixed rule.
- C5 duration priors by injury type can start from R-99/R-100/R-105, then be recalibrated on our own data.
- Designation to P(plays) stays an empirically estimated, project-owned parameter; no external number is hard-coded.
- If C5 grows into a survival/hazard model, R-104 and R-102 are the precedents.

## Open items

1. Confirm the authors of the 2025 J. ISAKOS ACL meta-analysis before citing it.
2. A small empirical spike, once injury-report history is ingested: play rate by designation for 2023-24 and 2024-25, with CIs.
3. R-104 and R-105 were read at abstract level only; treat their method details cautiously.
