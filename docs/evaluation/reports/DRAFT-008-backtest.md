# DRAFT-008 backtest: pre-season role signal

Generated 2026-09-26 05:31 UTC by `python -m fantasy_pipeline draft-preseason` (BigQuery dev).
Rules pre-registered in docs/architecture/ml-methodology-plan.md §12 (G-24 / D-57, PR #23) before this data existed in the warehouse. Pre-season features use only exhibition games up to 2 days before each opening night; starts are missing before 2017-18 (source quality) and flagged explicitly. Holdout folds only; bootstrap stratified by fold [R-54].

## Minutes model with pre-season role: SHIPS

- (a) holdout mpg MAE M1+pre-season - M1: -0.404 (95 % CI -0.492 to -0.321) -> PASS
- (b) holdout season-total rank H1+aging+M1pre - H1+aging+M1: +0.020 (95 % CI +0.014 to +0.025), positive in 4/4 folds -> PASS

| target | M1 (current) | M1 + pre-season |
|---|---|---|
| 2022-23 | 4.049 | 3.495 |
| 2023-24 | 3.903 | 3.550 |
| 2024-25 | 3.670 | 3.368 |
| 2025-26 | 4.122 | 3.716 |

## Growth breakout chance with pre-season role (played >= 60 % of games; D-55 rule): SHIPS

Breakout = season-total 9-cat value rank improves by >= 50 places and finishes inside the top 150.

- pooled precision@20 - base rate: +0.135 (95 % CI +0.077 to +0.207) -> PASS
- pooled Brier: model 0.1008 vs base-rate forecast 0.1021 -> PASS

| target | players | base rate | precision@20 | precision@50 | Brier | Brier (base rate) | nDCG@20 |
|---|---|---|---|---|---|---|---|
| 2018-19 | 285 | 8.4% | 15% | 18% | 0.0915 | 0.0807 | 0.20 |
| 2019-20 | 274 | 12.8% | 15% | 26% | 0.1158 | 0.1114 | 0.12 |
| 2020-21 | 277 | 11.6% | 30% | 16% | 0.1019 | 0.1023 | 0.41 |
| 2021-22 | 282 | 14.2% | 30% | 28% | 0.1164 | 0.1221 | 0.26 |
| 2022-23 | 272 | 8.8% | 25% | 20% | 0.0790 | 0.0819 | 0.39 |
| 2023-24 | 282 | 13.1% | 30% | 30% | 0.1075 | 0.1141 | 0.30 |
| 2024-25 | 288 | 10.4% | 25% | 28% | 0.0866 | 0.0936 | 0.20 |
| 2025-26 | 276 | 12.7% | 30% | 28% | 0.1079 | 0.1108 | 0.37 |

Reliability (all folds pooled; predicted vs observed breakout rate):

| predicted bin | mean predicted | observed | players |
|---|---|---|---|
| 0.0-0.1 | 4.8% | 6.3% | 1341 |
| 0.1-0.2 | 14.0% | 16.6% | 512 |
| 0.2-0.3 | 24.2% | 21.2% | 208 |
| 0.3-0.4 | 34.9% | 27.8% | 97 |
| 0.4-0.5 | 44.6% | 22.4% | 49 |
| 0.5-0.6 | 54.6% | 7.7% | 13 |
| 0.6-0.7 | 65.7% | 25.0% | 8 |
| 0.7-0.8 | 75.1% | 33.3% | 6 |
| 0.8-0.9 | 81.1% | 0.0% | 2 |

Sensitivity (holdout folds 2022-23..2025-26; U9):

| jump | base rate | precision@20 |
|---|---|---|
| >= 30 ranks | 16.3% | 41% |
| >= 50 ranks | 11.3% | 28% |
| >= 80 ranks | 5.7% | 15% |

## Hindsight 2025-26: what the model flagged using data up to 2024-25 plus that season's pre-season games before the draft cutoff

Top 20 flags, plus every actual breakout (hit = broke out). Ranks are season-total 9-cat value.

| model rank | player | P(breakout) | value rank last season | value rank this season | broke out |
|---|---|---|---|---|---|
| 1 | Reed Sheppard | 70% | 344 | 42 | yes |
| 2 | Cody Williams | 68% | 413 | 270 | no |
| 3 | Craig Porter Jr. | 45% | 359 | 227 | no |
| 4 | Kris Murray | 44% | 386 | 276 | no |
| 5 | Adem Bona | 40% | 215 | 197 | no |
| 6 | Tidjane Salaün | 38% | 363 | 360 | no |
| 7 | Oso Ighodaro | 38% | 281 | 156 | no |
| 8 | Ausar Thompson | 36% | 156 | 96 | yes |
| 9 | Rayan Rupert | 36% | 433 | 309 | no |
| 10 | Blake Wesley | 34% | 397 | 500 | no |
| 11 | Aaron Holiday | 34% | 305 | 335 | no |
| 12 | Keyonte George | 33% | 181 | 57 | yes |
| 13 | Johnny Furphy | 32% | 389 | 401 | no |
| 14 | Donovan Clingan | 31% | 118 | 22 | yes |
| 15 | Jabari Walker | 29% | 306 | 327 | no |
| 16 | Jett Howard | 28% | 406 | 325 | no |
| 17 | Matas Buzelis | 27% | 135 | 35 | yes |
| 18 | Pelle Larsson | 27% | 358 | 155 | no |
| 19 | Jusuf Nurkić | 26% | 260 | 273 | no |
| 20 | Jaime Jaquez Jr. | 26% | 237 | 97 | yes |
| 21 | Jabari Smith Jr. | 25% | 165 | 48 | yes |
| 25 | Kel'el Ware | 24% | 98 | 31 | yes |
| 26 | Ryan Rollins | 24% | 266 | 40 | yes |
| 34 | Sandro Mamukelashvili | 21% | 267 | 72 | yes |
| 38 | Moussa Diabaté | 20% | 221 | 85 | yes |
| 39 | Brandin Podziemski | 19% | 138 | 69 | yes |
| 41 | Neemias Queta | 18% | 240 | 29 | yes |
| 45 | Kevin Porter Jr. | 18% | 193 | 124 | yes |
| 69 | Kyle Filipowski | 14% | 199 | 92 | yes |
| 71 | AJ Green | 14% | 211 | 143 | yes |
| 75 | Jake LaRavia | 14% | 232 | 111 | yes |
| 76 | Tyrese Maxey | 13% | 59 | 4 | yes |
| 78 | Scottie Barnes | 13% | 73 | 8 | yes |
| 95 | Wendell Carter Jr. | 11% | 166 | 58 | yes |
| 117 | Stephon Castle | 9% | 216 | 133 | yes |
| 126 | Andrew Wiggins | 8% | 115 | 51 | yes |
| 130 | CJ McCollum | 8% | 160 | 80 | yes |
| 138 | Duncan Robinson | 7% | 169 | 108 | yes |
| 149 | Tristan da Silva | 7% | 245 | 115 | yes |
| 151 | Donte DiVincenzo | 7% | 141 | 66 | yes |
| 157 | Gary Payton II | 6% | 214 | 141 | yes |
| 166 | Luka Dončić | 5% | 65 | 12 | yes |
| 190 | Jay Huff | 4% | 206 | 32 | yes |
| 191 | Luke Kennard | 4% | 168 | 112 | yes |
| 194 | Jaylen Brown | 4% | 103 | 44 | yes |
| 204 | Davion Mitchell | 4% | 182 | 129 | yes |
| 226 | Javonte Green | 3% | 234 | 122 | yes |
| 235 | Nickeil Alexander-Walker | 3% | 139 | 13 | yes |
| 258 | Tim Hardaway Jr. | 1% | 183 | 106 | yes |
