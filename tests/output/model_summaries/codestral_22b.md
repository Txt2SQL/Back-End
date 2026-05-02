# Model Performance Comparison: `codestral:22b`

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
| battle_death | 87.5% | 81.25% | +6.25% | 7.22s | 4.25s | +2.97s | 1.38 | 1 | +0.38 | 0 | 0 | +0 | 0 |
| california_schools | 32.58% | 19.1% | +13.48% | 15.43s | 6.94s | +8.49s | 2.07 | 1.37 | +0.70 | 0 | 0 | +0 | 1 |
| car_1 | 50% | 52.17% | -2.17% | 10.64s | 5.71s | +4.93s | 1.68 | 1.05 | +0.63 | 0 | 0 | +0 | 1 |
| card_games | 31.41% | 27.75% | +3.66% | 15.94s | 8.35s | +7.59s | 1.97 | 1.05 | +0.92 | 0 | 0 | +0 | 0 |
| codebase_community | 45.16% | 37.63% | +7.53% | 14.26s | 6.31s | +7.95s | 1.79 | 1 | +0.79 | 0 | 0 | +0 | 1 |
| concert_singer | 82.22% | 77.78% | +4.44% | 6.39s | 4.19s | +2.20s | 1.18 | 1 | +0.18 | 0 | 0 | +0 | 0 |
| course_teach | 90% | 86.67% | +3.33% | 6.28s | 4.3s | +1.98s | 1.07 | 1 | +0.07 | 0 | 0 | +0 | 0 |
| cre_Doc_Template_Mgt | 86.9% | 82.14% | +4.76% | 6.59s | 4.22s | +2.37s | 1.36 | 1 | +0.36 | 0 | 0 | +0 | 0 |
| debit_card_specializing | 18.75% | 14.06% | +4.69% | 15.5s | 6.36s | +9.14s | 2.03 | 1.02 | +1.01 | 0 | 0 | +0 | 1 |
| dog_kennels | 69.51% | 67.07% | +2.44% | 9.25s | 4.76s | +4.49s | 1.51 | 1 | +0.51 | 0 | 0 | +0 | 4 |
| employee_hire_evaluation | 94.74% | 89.47% | +5.27% | 5.45s | 4.48s | +0.97s | 1 | 1 | +0 | 0 | 0 | +0 | 0 |
| european_football_2 | 27.91% | 41.09% | -13.18% | 16.35s | 9.25s | +7.10s | 2.1 | 1.15 | +0.95 | 0 | 0 | +0 | 0 |
| financial | 20.75% | 10.38% | +10.37% | 22.18s | 6.61s | +15.57s | 3.04 | 1.03 | +2.01 | 0 | 0 | +0 | 15 |
| flight_2 | 88.75% | 83.75% | +5% | 6.7s | 4.09s | +2.61s | 1.34 | 1 | +0.34 | 0 | 0 | +0 | 0 |
| formula_1 | 36.21% | 23.56% | +12.65% | 14.08s | 6.6s | +7.48s | 2.05 | 1.01 | +1.04 | 0 | 0 | +0 | 5 |
| museum_visit | 94.44% | 100% | -5.56% | 6.98s | 13.1s | -6.12s | 1.28 | 1 | +0.28 | 0 | 0 | +0 | 0 |
| network_1 | 82.14% | 71.43% | +10.71% | 8.7s | 4.39s | +4.31s | 1.5 | 1 | +0.50 | 0 | 0 | +0 | 0 |
| orchestra | 92.5% | 97.5% | -5% | 5.81s | 3.83s | +1.98s | 1.12 | 1 | +0.12 | 0 | 0 | +0 | 0 |
| pets_1 | 80.95% | 76.19% | +4.76% | 6.9s | 5.03s | +1.87s | 1.19 | 1 | +0.19 | 0 | 0 | +0 | 0 |
| poker_player | 97.5% | 85% | +12.50% | 5.21s | 3.5s | +1.71s | 1.05 | 1 | +0.05 | 0 | 0 | +0 | 0 |
| real_estate_properties | 50% | 75% | -25% | 11.21s | 5s | +6.21s | 1.75 | 1 | +0.75 | 0 | 0 | +0 | 0 |
| singer | 93.33% | 90% | +3.33% | 6.17s | 3.8s | +2.37s | 1.17 | 1 | +0.17 | 0 | 0 | +0 | 0 |
| student_club | 52.53% | 39.24% | +13.29% | 11.82s | 5.03s | +6.79s | 2.19 | 1.1 | +1.09 | 0 | 0 | +0 | 11 |
| student_transcripts_tracking | 57.69% | 52.56% | +5.13% | 10.28s | 5.83s | +4.45s | 1.53 | 1 | +0.53 | 0 | 0 | +0 | 2 |
| superhero | 37.98% | 26.36% | +11.62% | 15.87s | 4.54s | +11.33s | 2.89 | 1.02 | +1.87 | 0 | 0 | +0 | 28 |
| toxicology | 17.93% | 15.86% | +2.07% | 15.53s | 5.96s | +9.57s | 2.22 | 1.01 | +1.21 | 0 | 0 | +0 | 3 |
| tvshow | 79.03% | 64.52% | +14.51% | 7.44s | 4.87s | +2.57s | 1.35 | 1.02 | +0.33 | 0 | 0 | +0 | 0 |
| voter_1 | 93.33% | 80% | +13.33% | 6.88s | 4.26s | +2.62s | 1.27 | 1 | +0.27 | 0 | 0 | +0 | 0 |
| **MODEL VERDICT** | **51.1%** | **45.25%** | **+5.85%** | **12.46s** | **5.93s** | **+6.54s** | **1.87** | **1.04** | **+0.83** | **0** | **0** | **+0** | **72** |

## Correlations

| Database | Attempts Pearson float db_conn | Attempts Pearson bool db_conn | Attempts Pearson float text | Attempts Pearson bool text | Attempts Pearson delta | Attempts Spearman float db_conn | Attempts Spearman bool db_conn | Attempts Spearman float text | Attempts Spearman bool text | Attempts Spearman delta | Complexity Pearson float db_conn | Complexity Pearson bool db_conn | Complexity Pearson float text | Complexity Pearson bool text | Complexity Pearson delta | Complexity Spearman float db_conn | Complexity Spearman bool db_conn | Complexity Spearman float text | Complexity Spearman bool text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.4880 | false | N/A | N/A | N/A | -0.4880 | false | N/A | N/A | N/A | -0.2794 | false | -0.2634 | false | -0.0159 | -0.4018 | false | -0.4479 | false | +0.0462 |
| california_schools | -0.3485 | true | -0.1747 | false | -0.1738 | -0.3617 | true | -0.1993 | false | -0.1625 | -0.1141 | false | -0.3537 | true | +0.2396 | -0.0951 | false | -0.3810 | true | +0.2859 |
| car_1 | -0.4368 | true | -0.1331 | false | -0.3037 | -0.4749 | true | -0.1557 | false | -0.3192 | -0.0704 | false | -0.2310 | true | +0.1605 | -0.0436 | false | -0.1725 | false | +0.1289 |
| card_games | -0.3176 | true | -0.0445 | false | -0.2731 | -0.3168 | true | 0.0127 | false | -0.3295 | -0.2435 | true | -0.2767 | true | +0.0333 | -0.2447 | true | -0.3080 | true | +0.0633 |
| codebase_community | -0.3488 | true | N/A | N/A | N/A | -0.3599 | true | N/A | N/A | N/A | -0.2960 | true | -0.2359 | true | -0.0601 | -0.2707 | true | -0.2020 | true | -0.0687 |
| concert_singer | -0.3090 | true | N/A | N/A | N/A | -0.1896 | false | N/A | N/A | N/A | -0.0955 | false | -0.2447 | false | +0.1492 | -0.0873 | false | -0.2391 | false | +0.1519 |
| course_teach | 0.0891 | false | N/A | N/A | N/A | 0.0891 | false | N/A | N/A | N/A | -0.2351 | false | 0.1332 | false | -0.3682 | -0.2538 | false | 0.1415 | false | -0.3952 |
| cre_Doc_Template_Mgt | -0.2619 | true | N/A | N/A | N/A | -0.2170 | true | N/A | N/A | N/A | -0.0868 | false | 0.0616 | false | -0.1484 | -0.0897 | false | 0.0790 | false | -0.1687 |
| debit_card_specializing | -0.2353 | false | -0.0510 | false | -0.1843 | -0.2323 | false | -0.0510 | false | -0.1814 | -0.1627 | false | -0.1922 | false | +0.0295 | -0.2106 | false | -0.3177 | true | +0.1072 |
| dog_kennels | -0.4894 | true | N/A | N/A | N/A | -0.4613 | true | N/A | N/A | N/A | -0.3316 | true | -0.4111 | true | +0.0795 | -0.3344 | true | -0.4273 | true | +0.0928 |
| employee_hire_evaluation | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 0.1783 | false | 0.1799 | false | -0.0017 | 0.1751 | false | 0.2388 | false | -0.0638 |
| european_football_2 | -0.4118 | true | -0.1132 | false | -0.2986 | -0.4218 | true | -0.1719 | false | -0.2499 | -0.1534 | false | -0.0813 | false | -0.0721 | -0.1997 | false | -0.1053 | false | -0.0945 |
| financial | -0.3573 | true | -0.0581 | false | -0.2992 | -0.3761 | true | -0.0581 | false | -0.3180 | -0.0487 | false | -0.1482 | false | +0.0995 | -0.0225 | false | -0.1580 | false | +0.1354 |
| flight_2 | -0.4461 | true | N/A | N/A | N/A | -0.3491 | true | N/A | N/A | N/A | -0.1967 | false | -0.4078 | true | +0.2110 | -0.1711 | false | -0.3772 | true | +0.2061 |
| formula_1 | -0.3374 | true | -0.0425 | false | -0.2949 | -0.3379 | true | -0.0425 | false | -0.2954 | -0.1526 | false | -0.1578 | true | +0.0051 | -0.0954 | false | -0.1538 | true | +0.0584 |
| museum_visit | 0.0922 | false | N/A | N/A | N/A | 0.1081 | false | N/A | N/A | N/A | -0.1706 | false | N/A | N/A | N/A | -0.2139 | false | N/A | N/A | N/A |
| network_1 | -0.3719 | true | N/A | N/A | N/A | -0.3226 | true | N/A | N/A | N/A | -0.0954 | false | -0.1798 | false | +0.0844 | -0.1640 | false | -0.2260 | false | +0.0619 |
| orchestra | -0.4479 | true | N/A | N/A | N/A | -0.3809 | true | N/A | N/A | N/A | -0.1636 | false | 0.1708 | false | -0.3344 | -0.1267 | false | 0.2137 | false | -0.3404 |
| pets_1 | -0.0735 | false | N/A | N/A | N/A | -0.0735 | false | N/A | N/A | N/A | -0.1989 | false | 0.1591 | false | -0.3580 | -0.1776 | false | 0.1169 | false | -0.2945 |
| poker_player | 0.0367 | false | N/A | N/A | N/A | 0.0367 | false | N/A | N/A | N/A | 0.1996 | false | 0.1656 | false | +0.0340 | 0.2249 | false | 0.1442 | false | +0.0807 |
| real_estate_properties | -0.9045 | false | N/A | N/A | N/A | -0.9428 | false | N/A | N/A | N/A | 1.0000 | true | 0.6623 | false | +0.3377 | 1.0000 | true | 0.8165 | false | +0.1835 |
| singer | -0.5596 | true | N/A | N/A | N/A | -0.4819 | true | N/A | N/A | N/A | 0.1984 | false | 0.2241 | false | -0.0257 | 0.2065 | false | 0.2113 | false | -0.0048 |
| student_club | -0.5326 | true | -0.1223 | false | -0.4102 | -0.5029 | true | -0.1126 | false | -0.3903 | 0.0109 | false | -0.0404 | false | +0.0513 | 0.0166 | false | -0.0654 | false | +0.0821 |
| student_transcripts_tracking | -0.4141 | true | N/A | N/A | N/A | -0.4108 | true | N/A | N/A | N/A | -0.1860 | false | -0.1604 | false | -0.0255 | -0.1860 | false | -0.1427 | false | -0.0433 |
| superhero | -0.5378 | true | 0.2095 | true | -0.7473 | -0.5461 | true | 0.2095 | true | -0.7556 | -0.2578 | true | -0.1709 | false | -0.0869 | -0.3025 | true | -0.1695 | false | -0.1330 |
| toxicology | -0.2132 | true | -0.0365 | false | -0.1768 | -0.2373 | true | -0.0365 | false | -0.2008 | -0.1807 | true | -0.2262 | true | +0.0455 | -0.2373 | true | -0.2689 | true | +0.0316 |
| tvshow | -0.3143 | true | -0.1726 | false | -0.1417 | -0.2088 | false | -0.1726 | false | -0.0362 | -0.1695 | false | -0.1802 | false | +0.0106 | -0.1600 | false | -0.2111 | false | +0.0511 |
| voter_1 | 0.1612 | false | N/A | N/A | N/A | 0.1612 | false | N/A | N/A | N/A | 0.0851 | false | -0.2956 | false | +0.3807 | 0.0318 | false | -0.3374 | false | +0.3692 |
| **MODEL VERDICT** | **-0.3251** | **19/27** | **-0.0672** | **1/11** | **-0.2579** | **-0.3074** | **17/27** | **-0.0707** | **1/11** | **-0.2367** | **-0.0792** | **6/28** | **-0.0926** | **8/27** | **+0.0135** | **-0.0869** | **6/28** | **-0.1018** | **8/27** | **+0.0149** |
