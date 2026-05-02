# Model Performance Comparison: `gpt-4o`

**Base directory:** `tests\output\generations`

Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.

## Database

| Database | Tables | Requests | Complexity L/M/H |
| --- | --- | --- | --- |
| battle_death | 3 | 16 | 10/4/2 |
| california_schools | 3 | 89 | 51/26/12 |
| car_1 | 6 | 92 | 37/22/30 |
| card_games | 6 | 191 | 139/37/15 |
| codebase_community | 8 | 186 | 109/51/26 |
| concert_singer | 4 | 45 | 20/15/10 |
| course_teach | 3 | 30 | 14/10/6 |
| cre_Doc_Template_Mgt | 4 | 84 | 48/18/18 |
| debit_card_specializing | 5 | 64 | 16/24/24 |
| dog_kennels | 8 | 82 | 44/18/20 |
| employee_hire_evaluation | 4 | 38 | 22/8/8 |
| european_football_2 | 7 | 129 | 75/24/30 |
| financial | 8 | 106 | 21/51/34 |
| flight_2 | 3 | 80 | 44/16/20 |
| formula_1 | 13 | 174 | 102/43/29 |
| museum_visit | 3 | 18 | 10/4/4 |
| network_1 | 3 | 56 | 18/22/16 |
| orchestra | 4 | 40 | 26/8/6 |
| pets_1 | 3 | 42 | 14/16/12 |
| poker_player | 2 | 40 | 32/6/2 |
| real_estate_properties | 5 | 4 | 3/1/0 |
| singer | 2 | 30 | 20/6/4 |
| student_club | 8 | 158 | 87/42/29 |
| student_transcripts_tracking | 11 | 78 | 46/8/24 |
| superhero | 10 | 129 | 47/45/37 |
| toxicology | 4 | 145 | 82/32/31 |
| tvshow | 3 | 62 | 44/12/6 |
| voter_1 | 3 | 15 | 9/2/4 |
| **MODEL VERDICT** | **146** | **2223** | **1190/571/459** |

## Status

| Database | Success db_conn | Success text | Success delta | Avg time db_conn | Avg time text | Avg time delta | Avg attempts db_conn | Avg attempts text | Avg attempts delta | Syntax db_conn | Syntax text | Syntax delta | Runtime db_conn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 87.5% | 6.25% | +81.25% | 8.07s | 3.56s | +4.51s | 2.12 | 1 | +1.12 | 0 | 0 | +0 | 0 |
| california_schools | 31.46% | 5.62% | +25.84% | 13.57s | 5.71s | +7.86s | 2.42 | 1.92 | +0.50 | 0 | 0 | +0 | 1 |
| car_1 | 55.43% | 11.96% | +43.47% | 10.19s | 4.32s | +5.87s | 2.14 | 1.01 | +1.13 | 0 | 0 | +0 | 1 |
| card_games | 39.79% | 6.28% | +33.51% | 13.62s | 4.08s | +9.54s | 2.39 | 1.02 | +1.37 | 0 | 0 | +0 | 1 |
| codebase_community | 51.08% | 6.99% | +44.09% | 13.6s | 3s | +10.60s | 2.35 | 1 | +1.35 | 0 | 0 | +0 | 3 |
| concert_singer | 86.67% | 20% | +66.67% | 7.04s | 3.47s | +3.57s | 1.8 | 1 | +0.80 | 0 | 0 | +0 | 0 |
| course_teach | 93.33% | 3.33% | +90% | 7.59s | 3.49s | +4.10s | 1.93 | 1 | +0.93 | 0 | 0 | +0 | 0 |
| cre_Doc_Template_Mgt | 92.86% | 0% | +92.86% | 7.19s | 3.6s | +3.59s | 2.06 | 1 | +1.06 | 0 | 0 | +0 | 0 |
| debit_card_specializing | 26.56% | 6.25% | +20.31% | 13.27s | 3.3s | +9.97s | 2.05 | 1.02 | +1.03 | 0 | 0 | +0 | 0 |
| dog_kennels | 70.73% | 1.22% | +69.51% | 9.84s | 3.81s | +6.03s | 2.15 | 1.01 | +1.14 | 0 | 0 | +0 | 5 |
| employee_hire_evaluation | 86.84% | 7.89% | +78.95% | 7.22s | 3.34s | +3.88s | 1.89 | 1 | +0.89 | 0 | 0 | +0 | 0 |
| european_football_2 | 52.71% | 4.65% | +48.06% | 13.12s | 3.77s | +9.35s | 2.22 | 1 | +1.22 | 0 | 0 | +0 | 0 |
| financial | 19.81% | 0% | +19.81% | 20.26s | 3.07s | +17.19s | 3.86 | 1.02 | +2.84 | 0 | 0 | +0 | 26 |
| flight_2 | 88.75% | 10% | +78.75% | 8.04s | 3.57s | +4.47s | 2.29 | 1 | +1.29 | 0 | 0 | +0 | 0 |
| formula_1 | 34.48% | 3.45% | +31.03% | 14.68s | 3.33s | +11.35s | 2.55 | 1.01 | +1.54 | 0 | 0 | +0 | 3 |
| museum_visit | 94.44% | 0% | +94.44% | 7.57s | 3.1s | +4.47s | 2 | 1 | +1 | 0 | 0 | +0 | 0 |
| network_1 | 69.64% | 0% | +69.64% | 9.05s | 3.35s | +5.70s | 2.09 | 1 | +1.09 | 0 | 0 | +0 | 0 |
| orchestra | 100% | 5% | +95% | 7.17s | 3.27s | +3.90s | 1.77 | 1 | +0.77 | 0 | 0 | +0 | 0 |
| pets_1 | 73.81% | 7.14% | +66.67% | 8.68s | 3.35s | +5.33s | 1.86 | 1 | +0.86 | 0 | 0 | +0 | 0 |
| poker_player | 92.5% | 72.5% | +20% | 5.44s | 3.96s | +1.48s | 1.1 | 1 | +0.10 | 0 | 0 | +0 | 0 |
| real_estate_properties | 50% | 0% | +50% | 14.71s | 8.74s | +5.97s | 3.25 | 1 | +2.25 | 0 | 0 | +0 | 0 |
| singer | 100% | 36.67% | +63.33% | 5.86s | 3.14s | +2.72s | 1.43 | 1 | +0.43 | 0 | 0 | +0 | 0 |
| student_club | 55.06% | 5.7% | +49.36% | 11.09s | 3.07s | +8.02s | 2.42 | 1.08 | +1.34 | 0 | 0 | +0 | 4 |
| student_transcripts_tracking | 62.82% | 0% | +62.82% | 10.51s | 3.76s | +6.75s | 2.45 | 1.01 | +1.44 | 0 | 0 | +0 | 1 |
| superhero | 33.33% | 3.88% | +29.45% | 18.62s | 2.85s | +15.77s | 3.92 | 1 | +2.92 | 0 | 0 | +0 | 47 |
| toxicology | 20.69% | 0% | +20.69% | 15.7s | 2.71s | +12.99s | 3.24 | 1 | +2.24 | 0 | 0 | +0 | 5 |
| tvshow | 82.26% | 3.23% | +79.03% | 7.74s | 3.55s | +4.19s | 1.84 | 1 | +0.84 | 0 | 0 | +0 | 0 |
| voter_1 | 80% | 13.33% | +66.67% | 7.45s | 3.51s | +3.94s | 2 | 1 | +1 | 0 | 0 | +0 | 0 |
| **MODEL VERDICT** | **54.21%** | **6.43%** | **+47.77%** | **12.2s** | **3.51s** | **+8.68s** | **2.45** | **1.05** | **+1.40** | **0** | **0** | **+0** | **97** |

## Correlations

| Database | Attempts Pearson float db_conn | Attempts Pearson bool db_conn | Attempts Pearson float text | Attempts Pearson bool text | Attempts Pearson delta | Attempts Spearman float db_conn | Attempts Spearman bool db_conn | Attempts Spearman float text | Attempts Spearman bool text | Attempts Spearman delta | Complexity Pearson float db_conn | Complexity Pearson bool db_conn | Complexity Pearson float text | Complexity Pearson bool text | Complexity Pearson delta | Complexity Spearman float db_conn | Complexity Spearman bool db_conn | Complexity Spearman float text | Complexity Spearman bool text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.6831 | true | N/A | N/A | N/A | -0.6831 | true | N/A | N/A | N/A | -0.2794 | false | -0.0554 | false | -0.2240 | -0.4018 | false | -0.0289 | false | -0.3729 |
| california_schools | -0.2189 | true | -0.1434 | false | -0.0755 | -0.2016 | false | -0.1525 | false | -0.0491 | -0.1567 | false | -0.0753 | false | -0.0815 | -0.1178 | false | -0.0756 | false | -0.0423 |
| car_1 | -0.1577 | false | -0.0386 | false | -0.1191 | -0.0731 | false | -0.0386 | false | -0.0345 | -0.1838 | false | 0.0099 | false | -0.1936 | -0.1371 | false | 0.0324 | false | -0.1695 |
| card_games | -0.3306 | true | -0.0188 | false | -0.3118 | -0.3129 | true | -0.0188 | false | -0.2941 | -0.2878 | true | 0.0406 | false | -0.3285 | -0.3005 | true | 0.0675 | false | -0.3680 |
| codebase_community | -0.4089 | true | N/A | N/A | N/A | -0.3692 | true | N/A | N/A | N/A | -0.2244 | true | -0.0555 | false | -0.1690 | -0.2075 | true | -0.0855 | false | -0.1221 |
| concert_singer | -0.2795 | false | N/A | N/A | N/A | -0.0150 | false | N/A | N/A | N/A | -0.1933 | false | 0.2019 | false | -0.3951 | -0.1839 | false | 0.1918 | false | -0.3757 |
| course_teach | -0.0714 | false | N/A | N/A | N/A | -0.0714 | false | N/A | N/A | N/A | -0.1187 | false | 0.0824 | false | -0.2011 | -0.1285 | false | 0.0893 | false | -0.2178 |
| cre_Doc_Template_Mgt | -0.2461 | true | N/A | N/A | N/A | -0.2682 | true | N/A | N/A | N/A | -0.1862 | false | N/A | N/A | N/A | -0.1782 | false | N/A | N/A | N/A |
| debit_card_specializing | -0.1977 | false | -0.0325 | false | -0.1652 | -0.1530 | false | -0.0325 | false | -0.1205 | -0.2328 | false | -0.0980 | false | -0.1348 | -0.3257 | true | -0.1314 | false | -0.1943 |
| dog_kennels | -0.3957 | true | -0.0123 | false | -0.3834 | -0.1913 | false | -0.0123 | false | -0.1789 | -0.3702 | true | -0.0090 | false | -0.3612 | -0.3809 | true | 0.0383 | false | -0.4193 |
| employee_hire_evaluation | 0.0826 | false | N/A | N/A | N/A | 0.0800 | false | N/A | N/A | N/A | -0.0304 | false | 0.0500 | false | -0.0804 | 0.0072 | false | 0.0544 | false | -0.0471 |
| european_football_2 | -0.3233 | true | N/A | N/A | N/A | -0.3327 | true | N/A | N/A | N/A | -0.1998 | true | 0.0239 | false | -0.2237 | -0.2450 | true | 0.0677 | false | -0.3127 |
| financial | -0.4580 | true | N/A | N/A | N/A | -0.4550 | true | N/A | N/A | N/A | -0.1316 | false | N/A | N/A | N/A | -0.1817 | false | N/A | N/A | N/A |
| flight_2 | -0.3833 | true | N/A | N/A | N/A | -0.3352 | true | N/A | N/A | N/A | -0.0256 | false | -0.0068 | false | -0.0187 | -0.0255 | false | -0.0074 | false | -0.0181 |
| formula_1 | -0.2469 | true | -0.0204 | false | -0.2265 | -0.2340 | true | -0.0204 | false | -0.2137 | -0.1556 | true | 0.1868 | true | -0.3424 | -0.1781 | true | 0.1429 | false | -0.3211 |
| museum_visit | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | -0.1706 | false | N/A | N/A | N/A | -0.2139 | false | N/A | N/A | N/A |
| network_1 | -0.3115 | true | N/A | N/A | N/A | -0.3893 | true | N/A | N/A | N/A | -0.1800 | false | N/A | N/A | N/A | -0.2171 | false | N/A | N/A | N/A |
| orchestra | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 0.1788 | false | N/A | N/A | N/A | 0.1021 | false | N/A |
| pets_1 | -0.0458 | false | N/A | N/A | N/A | 0.0000 | false | N/A | N/A | N/A | -0.2365 | false | 0.1005 | false | -0.3371 | -0.2537 | false | 0.0773 | false | -0.3311 |
| poker_player | -0.5379 | true | N/A | N/A | N/A | -0.5379 | true | N/A | N/A | N/A | 0.3549 | true | 0.2666 | false | +0.0883 | 0.3999 | true | 0.2411 | false | +0.1587 |
| real_estate_properties | -0.5774 | false | N/A | N/A | N/A | -0.5774 | false | N/A | N/A | N/A | 1.0000 | true | N/A | N/A | N/A | 1.0000 | true | N/A | N/A | N/A |
| singer | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 0.3508 | false | N/A | N/A | N/A | 0.3206 | false | N/A |
| student_club | -0.3815 | true | -0.0465 | false | -0.3351 | -0.3283 | true | -0.0567 | false | -0.2716 | -0.0548 | false | 0.0195 | false | -0.0744 | -0.0959 | false | -0.0035 | false | -0.0924 |
| student_transcripts_tracking | -0.4196 | true | N/A | N/A | N/A | -0.3307 | true | N/A | N/A | N/A | -0.2960 | true | N/A | N/A | N/A | -0.3010 | true | N/A | N/A | N/A |
| superhero | -0.4159 | true | N/A | N/A | N/A | -0.4157 | true | N/A | N/A | N/A | -0.0713 | false | 0.0926 | false | -0.1639 | -0.1200 | false | 0.1301 | false | -0.2501 |
| toxicology | -0.2583 | true | N/A | N/A | N/A | -0.2796 | true | N/A | N/A | N/A | -0.2478 | true | N/A | N/A | N/A | -0.2886 | true | N/A | N/A | N/A |
| tvshow | -0.3090 | true | N/A | N/A | N/A | -0.2577 | true | N/A | N/A | N/A | -0.1336 | false | 0.0116 | false | -0.1453 | -0.1334 | false | 0.0641 | false | -0.1975 |
| voter_1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | -0.2388 | false | 0.7447 | true | -0.9835 | -0.2381 | false | 0.6071 | true | -0.8453 |
| **MODEL VERDICT** | **-0.3156** | **17/24** | **-0.0446** | **0/7** | **-0.2710** | **-0.2805** | **15/24** | **-0.0474** | **0/7** | **-0.2331** | **-0.1173** | **9/26** | **0.0981** | **2/21** | **-0.2155** | **-0.1326** | **10/26** | **0.0902** | **1/21** | **-0.2228** |
