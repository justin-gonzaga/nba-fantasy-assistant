# DRAFT-007 backtest: minutes model (M1) and breakout probability (M2)

Generated 2026-09-25 16:15 UTC by `python -m fantasy_pipeline draft-breakouts` (BigQuery dev).
Plan: docs/architecture/ml-methodology-plan.md Part 1b (§7, §8, §10a; G-23 / D-54). All rules below were pre-registered before this run. Every fold uses only earlier seasons plus the target season's opening roster (U10) [R-50, R-51]; CIs are bootstraps stratified by fold [R-54].

## M1 minutes model: SHIPS

- selection (2018-19..2021-22): pooled mpg MAE ridge 3.819, gbm 3.852 -> ridge
- (a) holdout mpg MAE ridge - last season: -0.259 (95 % CI -0.377 to -0.138) -> PASS
- (b) holdout season-total rank H1+aging+M1 - H1+aging: +0.012 (95 % CI +0.007 to +0.018), positive in 4/4 folds -> PASS

| target | last season | ridge | LightGBM | players |
|---|---|---|---|---|
| 2018-19 (selection) | 4.259 | 3.889 | 3.999 | 361 |
| 2019-20 (selection) | 4.501 | 3.853 | 3.876 | 347 |
| 2020-21 (selection) | 4.165 | 3.800 | 3.876 | 374 |
| 2021-22 (selection) | 3.943 | 3.731 | 3.659 | 374 |
| 2022-23 (holdout) | 4.154 | 4.049 | 3.807 | 380 |
| 2023-24 (holdout) | 4.087 | 3.903 | 3.648 | 386 |
| 2024-25 (holdout) | 3.934 | 3.670 | 3.495 | 390 |
| 2025-26 (holdout) | 4.603 | 4.122 | 3.993 | 390 |

## M2a bounce-back chance (all players; D-55: shown as bounce-back): SHIPS

Breakout = season-total 9-cat value rank improves by >= 50 places and finishes inside the top 150.

- pooled precision@20 - base rate: +0.194 (95 % CI +0.126 to +0.271) -> PASS
- pooled Brier: model 0.0969 vs base-rate forecast 0.0998 -> PASS

| target | players | base rate | precision@20 | precision@50 | Brier | Brier (base rate) | nDCG@20 |
|---|---|---|---|---|---|---|---|
| 2018-19 | 412 | 10.2% | 20% | 26% | 0.0904 | 0.0924 | 0.17 |
| 2019-20 | 400 | 13.0% | 20% | 24% | 0.1122 | 0.1132 | 0.12 |
| 2020-21 | 435 | 10.3% | 30% | 18% | 0.0910 | 0.0932 | 0.35 |
| 2021-22 | 450 | 12.0% | 35% | 28% | 0.1017 | 0.1056 | 0.34 |
| 2022-23 | 433 | 11.5% | 35% | 28% | 0.0980 | 0.1022 | 0.37 |
| 2023-24 | 450 | 10.0% | 35% | 18% | 0.0893 | 0.0904 | 0.29 |
| 2024-25 | 447 | 10.1% | 40% | 18% | 0.0864 | 0.0908 | 0.42 |
| 2025-26 | 464 | 12.7% | 30% | 32% | 0.1070 | 0.1111 | 0.20 |

Reliability (all folds pooled; predicted vs observed breakout rate):

| predicted bin | mean predicted | observed | players |
|---|---|---|---|
| 0.0-0.1 | 6.1% | 7.7% | 1851 |
| 0.1-0.2 | 14.0% | 12.8% | 1285 |
| 0.2-0.3 | 23.4% | 22.1% | 271 |
| 0.3-0.4 | 33.6% | 31.1% | 61 |
| 0.4-0.5 | 43.5% | 23.1% | 13 |
| 0.5-0.6 | 52.9% | 42.9% | 7 |
| 0.6-0.7 | 64.1% | 33.3% | 3 |

Sensitivity (holdout folds 2022-23..2025-26; U9):

| jump | base rate | precision@20 |
|---|---|---|
| >= 30 ranks | 14.5% | 32% |
| >= 50 ranks | 11.1% | 35% |
| >= 80 ranks | 7.4% | 28% |

## Hindsight 2025-26: what the model flagged using data up to 2024-25 only

Top 20 flags, plus every actual breakout (hit = broke out). Ranks are season-total 9-cat value.

| model rank | player | P(breakout) | value rank last season | value rank this season | broke out |
|---|---|---|---|---|---|
| 1 | Taylor Hendricks | 60% | 487 | 261 | no |
| 2 | Matisse Thybulle | 43% | 372 | 301 | no |
| 3 | Brandon Miller | 42% | 273 | 52 | yes |
| 4 | Dejounte Murray | 39% | 257 | 353 | no |
| 5 | Isaiah Jackson | 39% | 476 | 240 | no |
| 6 | Herbert Jones | 37% | 332 | 218 | no |
| 7 | Cody Williams | 35% | 413 | 270 | no |
| 8 | Dereck Lively II | 34% | 209 | 452 | no |
| 9 | Zion Williamson | 33% | 272 | 104 | yes |
| 10 | Grant Williams | 33% | 361 | 313 | no |
| 11 | De'Anthony Melton | 32% | 466 | 244 | no |
| 12 | Chet Holmgren | 32% | 195 | 14 | yes |
| 13 | Paul Reed | 28% | 295 | 140 | yes |
| 14 | Isaiah Collier | 27% | 282 | 214 | no |
| 15 | Mitchell Robinson | 27% | 362 | 165 | no |
| 16 | Tre Jones | 27% | 248 | 64 | yes |
| 17 | Cam Thomas | 27% | 284 | 386 | no |
| 18 | Tidjane Salaün | 26% | 363 | 360 | no |
| 19 | Immanuel Quickley | 26% | 254 | 50 | yes |
| 20 | Kris Murray | 26% | 386 | 276 | no |
| 23 | Joel Embiid | 23% | 275 | 102 | yes |
| 27 | Tyrese Maxey | 23% | 59 | 4 | yes |
| 29 | Donovan Clingan | 22% | 118 | 22 | yes |
| 30 | Kyle Filipowski | 22% | 199 | 92 | yes |
| 31 | Jabari Smith Jr. | 22% | 165 | 48 | yes |
| 34 | Paolo Banchero | 22% | 224 | 89 | yes |
| 35 | Jalen Johnson | 21% | 150 | 17 | yes |
| 44 | Lauri Markkanen | 19% | 158 | 74 | yes |
| 46 | Kel'el Ware | 19% | 98 | 31 | yes |
| 47 | Keyonte George | 19% | 181 | 57 | yes |
| 51 | Scottie Barnes | 18% | 73 | 8 | yes |
| 54 | Jaime Jaquez Jr. | 18% | 237 | 97 | yes |
| 59 | Stephon Castle | 18% | 216 | 133 | yes |
| 60 | Brandon Ingram | 18% | 321 | 36 | yes |
| 68 | Reed Sheppard | 17% | 344 | 42 | yes |
| 73 | Robert Williams III | 17% | 307 | 103 | yes |
| 76 | Ausar Thompson | 17% | 156 | 96 | yes |
| 77 | Jalen Suggs | 17% | 225 | 91 | yes |
| 85 | LaMelo Ball | 16% | 143 | 41 | yes |
| 89 | Matas Buzelis | 16% | 135 | 35 | yes |
| 92 | Donte DiVincenzo | 16% | 141 | 66 | yes |
| 102 | Brandin Podziemski | 15% | 138 | 69 | yes |
| 107 | Ayo Dosunmu | 15% | 200 | 65 | yes |
| 116 | Collin Gillespie | 14% | 337 | 49 | yes |
| 147 | Luka Dončić | 13% | 65 | 12 | yes |
| 153 | Cam Spencer | 13% | 407 | 71 | yes |
| 174 | Dominick Barlow | 12% | 382 | 137 | yes |
| 177 | Kevin Porter Jr. | 12% | 193 | 124 | yes |
| 201 | Jerami Grant | 11% | 207 | 139 | yes |
| 207 | Tristan da Silva | 10% | 245 | 115 | yes |
| 219 | Neemias Queta | 10% | 240 | 29 | yes |
| 221 | Jaylen Brown | 10% | 103 | 44 | yes |
| 224 | Jordan Goodwin | 10% | 340 | 145 | yes |
| 238 | Sandro Mamukelashvili | 9% | 267 | 72 | yes |
| 246 | Ryan Rollins | 9% | 266 | 40 | yes |
| 252 | Deandre Ayton | 9% | 180 | 54 | yes |
| 255 | Wendell Carter Jr. | 9% | 166 | 58 | yes |
| 271 | Jaylon Tyson | 8% | 400 | 117 | yes |
| 272 | Ajay Mitchell | 8% | 342 | 116 | yes |
| 276 | Andrew Wiggins | 8% | 115 | 51 | yes |
| 282 | Moussa Diabaté | 8% | 221 | 85 | yes |
| 284 | Davion Mitchell | 7% | 182 | 129 | yes |
| 302 | Kawhi Leonard | 7% | 149 | 6 | yes |
| 311 | AJ Green | 6% | 211 | 143 | yes |
| 312 | Nickeil Alexander-Walker | 6% | 139 | 13 | yes |
| 321 | CJ McCollum | 6% | 160 | 80 | yes |
| 329 | Jake LaRavia | 6% | 232 | 111 | yes |
| 347 | Duncan Robinson | 5% | 169 | 108 | yes |
| 351 | Luke Kennard | 5% | 168 | 112 | yes |
| 361 | Gary Payton II | 5% | 214 | 141 | yes |
| 406 | Jay Huff | 4% | 206 | 32 | yes |
| 409 | Javonte Green | 4% | 234 | 122 | yes |
| 427 | Tim Hardaway Jr. | 3% | 183 | 106 | yes |

## M2b growth breakout chance (played >= 60 % of games last season; pre-registered D-55): does not ship

Breakout = season-total 9-cat value rank improves by >= 50 places and finishes inside the top 150.

- pooled precision@20 - base rate: +0.041 (95 % CI -0.011 to +0.108) -> fail
- pooled Brier: model 0.1031 vs base-rate forecast 0.1021 -> fail

| target | players | base rate | precision@20 | precision@50 | Brier | Brier (base rate) | nDCG@20 |
|---|---|---|---|---|---|---|---|
| 2018-19 | 285 | 8.4% | 15% | 18% | 0.0815 | 0.0807 | 0.16 |
| 2019-20 | 274 | 12.8% | 20% | 12% | 0.1181 | 0.1114 | 0.17 |
| 2020-21 | 277 | 11.6% | 15% | 16% | 0.1031 | 0.1023 | 0.18 |
| 2021-22 | 282 | 14.2% | 25% | 18% | 0.1187 | 0.1221 | 0.22 |
| 2022-23 | 272 | 8.8% | 20% | 12% | 0.0829 | 0.0819 | 0.18 |
| 2023-24 | 282 | 13.1% | 15% | 28% | 0.1107 | 0.1141 | 0.15 |
| 2024-25 | 288 | 10.4% | 5% | 14% | 0.0946 | 0.0936 | 0.04 |
| 2025-26 | 276 | 12.7% | 10% | 18% | 0.1158 | 0.1108 | 0.15 |

Reliability (all folds pooled; predicted vs observed breakout rate):

| predicted bin | mean predicted | observed | players |
|---|---|---|---|
| 0.0-0.1 | 5.6% | 7.4% | 1240 |
| 0.1-0.2 | 14.1% | 16.2% | 679 |
| 0.2-0.3 | 24.2% | 17.6% | 222 |
| 0.3-0.4 | 34.2% | 19.7% | 61 |
| 0.4-0.5 | 43.9% | 12.5% | 24 |
| 0.5-0.6 | 54.1% | 20.0% | 5 |
| 0.6-0.7 | 64.6% | 0.0% | 4 |
| 0.7-0.8 | 74.2% | 0.0% | 1 |

Sensitivity (holdout folds 2022-23..2025-26; U9):

| jump | base rate | precision@20 |
|---|---|---|
| >= 30 ranks | 16.3% | 26% |
| >= 50 ranks | 11.3% | 12% |
| >= 80 ranks | 5.7% | 9% |

## Hindsight 2025-26: what the model flagged using data up to 2024-25 only

Top 20 flags, plus every actual breakout (hit = broke out). Ranks are season-total 9-cat value.

| model rank | player | P(breakout) | value rank last season | value rank this season | broke out |
|---|---|---|---|---|---|
| 1 | Cody Williams | 74% | 413 | 270 | no |
| 2 | Rayan Rupert | 53% | 433 | 309 | no |
| 3 | Tidjane Salaün | 43% | 363 | 360 | no |
| 4 | Johnny Furphy | 42% | 389 | 401 | no |
| 5 | Reed Sheppard | 42% | 344 | 42 | yes |
| 6 | Jordan Walsh | 41% | 434 | 205 | no |
| 7 | Kris Murray | 39% | 386 | 276 | no |
| 8 | Jaden Hardy | 34% | 369 | 354 | no |
| 9 | Isaiah Collier | 33% | 282 | 214 | no |
| 10 | Marcus Sasser | 31% | 286 | 391 | no |
| 11 | Blake Wesley | 29% | 397 | 500 | no |
| 12 | Adem Bona | 28% | 215 | 197 | no |
| 13 | Pelle Larsson | 28% | 358 | 155 | no |
| 14 | Craig Porter Jr. | 28% | 359 | 227 | no |
| 15 | Cam Whitmore | 26% | 297 | 414 | no |
| 16 | Day'Ron Sharpe | 26% | 204 | 178 | no |
| 17 | Ja'Kobe Walter | 26% | 289 | 176 | no |
| 18 | Ryan Rollins | 25% | 266 | 40 | yes |
| 19 | Jordan Hawkins | 25% | 287 | 402 | no |
| 20 | Jett Howard | 25% | 406 | 325 | no |
| 22 | Ausar Thompson | 24% | 156 | 96 | yes |
| 25 | Kyle Filipowski | 23% | 199 | 92 | yes |
| 28 | Donovan Clingan | 23% | 118 | 22 | yes |
| 30 | Jabari Smith Jr. | 22% | 165 | 48 | yes |
| 43 | Jaime Jaquez Jr. | 19% | 237 | 97 | yes |
| 45 | Kel'el Ware | 18% | 98 | 31 | yes |
| 49 | Keyonte George | 18% | 181 | 57 | yes |
| 58 | Brandin Podziemski | 17% | 138 | 69 | yes |
| 59 | Neemias Queta | 17% | 240 | 29 | yes |
| 62 | Matas Buzelis | 16% | 135 | 35 | yes |
| 78 | Tyrese Maxey | 14% | 59 | 4 | yes |
| 82 | Stephon Castle | 13% | 216 | 133 | yes |
| 84 | Moussa Diabaté | 13% | 221 | 85 | yes |
| 90 | Scottie Barnes | 13% | 73 | 8 | yes |
| 99 | Sandro Mamukelashvili | 12% | 267 | 72 | yes |
| 100 | Kevin Porter Jr. | 12% | 193 | 124 | yes |
| 106 | Donte DiVincenzo | 11% | 141 | 66 | yes |
| 123 | Tristan da Silva | 10% | 245 | 115 | yes |
| 157 | Gary Payton II | 8% | 214 | 141 | yes |
| 164 | Jake LaRavia | 7% | 232 | 111 | yes |
| 167 | AJ Green | 7% | 211 | 143 | yes |
| 176 | Wendell Carter Jr. | 7% | 166 | 58 | yes |
| 177 | Davion Mitchell | 7% | 182 | 129 | yes |
| 180 | Luka Dončić | 7% | 65 | 12 | yes |
| 182 | Andrew Wiggins | 6% | 115 | 51 | yes |
| 183 | Jaylen Brown | 6% | 103 | 44 | yes |
| 202 | Luke Kennard | 5% | 168 | 112 | yes |
| 208 | Jay Huff | 5% | 206 | 32 | yes |
| 211 | Javonte Green | 5% | 234 | 122 | yes |
| 218 | CJ McCollum | 4% | 160 | 80 | yes |
| 232 | Duncan Robinson | 4% | 169 | 108 | yes |
| 236 | Nickeil Alexander-Walker | 3% | 139 | 13 | yes |
| 268 | Tim Hardaway Jr. | 2% | 183 | 106 | yes |
