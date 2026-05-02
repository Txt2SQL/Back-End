# Model Performance Comparison: `gpt-5-mini`

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
| battle_death | 93.75% | 43.75% | +50% | 16.38s | 26.23s | -9.85s | 1.31 | 1 | +0.31 | 0 | 0 | +0 | 0 |
| california_schools | 38.2% | 4.49% | +33.71% | 37.63s | 70.68s | -33.05s | 2.06 | 2.78 | -0.72 | 0 | 0 | +0 | 0 |
| car_1 | 58.7% | 4.35% | +54.35% | 31.92s | 24.23s | +7.69s | 2.07 | 1 | +1.07 | 0 | 0 | +0 | 0 |
| card_games | 39.79% | 3.14% | +36.65% | 33.56s | 17.02s | +16.54s | 2.09 | 1.02 | +1.07 | 0 | 0 | +0 | 0 |
| codebase_community | 50.54% | 4.84% | +45.70% | 31.85s | 15.91s | +15.94s | 1.96 | 1.05 | +0.91 | 0 | 0 | +0 | 1 |
| concert_singer | 84.44% | 31.11% | +53.33% | 19.99s | 17.88s | +2.11s | 1.62 | 1 | +0.62 | 0 | 0 | +0 | 0 |
| course_teach | 90% | 3.33% | +86.67% | 22.71s | 14.1s | +8.61s | 2 | 1 | +1 | 0 | 0 | +0 | 0 |
| cre_Doc_Template_Mgt | 84.52% | 0% | +84.52% | 22.61s | 16.27s | +6.34s | 1.77 | 1.01 | +0.76 | 0 | 0 | +0 | 0 |
| debit_card_specializing | 23.44% | 3.12% | +20.32% | 48.38s | 22.14s | +26.24s | 1.88 | 1.05 | +0.83 | 0 | 0 | +0 | 0 |
| dog_kennels | 73.17% | 6.1% | +67.07% | 28.29s | 18.21s | +10.08s | 1.84 | 1 | +0.84 | 0 | 0 | +0 | 1 |
| employee_hire_evaluation | 94.74% | 26.32% | +68.42% | 16.78s | 15.93s | +0.85s | 1.58 | 1 | +0.58 | 0 | 0 | +0 | 0 |
| european_football_2 | 60.47% | 13.18% | +47.29% | 44.87s | 32.03s | +12.84s | 1.73 | 1.06 | +0.67 | 0 | 0 | +0 | 0 |
| financial | 28.3% | 0% | +28.30% | 60.67s | 35.6s | +25.07s | 3.01 | 1.31 | +1.70 | 0 | 0 | +0 | 15 |
| flight_2 | 82.5% | 7.5% | +75% | 25.48s | 16.22s | +9.26s | 2.05 | 1 | +1.05 | 0 | 0 | +0 | 0 |
| formula_1 | 45.4% | 4.02% | +41.38% | 55.68s | 27.72s | +27.96s | 2.02 | 1.01 | +1.01 | 0 | 0 | +0 | 0 |
| museum_visit | 100% | 0% | +100% | 31.67s | 19.51s | +12.16s | 1.83 | 1 | +0.83 | 0 | 0 | +0 | 0 |
| network_1 | 66.07% | 0% | +66.07% | 33.28s | 14.38s | +18.90s | 1.91 | 1 | +0.91 | 0 | 0 | +0 | 0 |
| orchestra | 95% | 22.5% | +72.50% | 24.6s | 19.61s | +4.99s | 1.48 | 1.1 | +0.38 | 0 | 0 | +0 | 0 |
| pets_1 | 90.48% | 11.9% | +78.58% | 19.69s | 17.22s | +2.47s | 1.67 | 1 | +0.67 | 0 | 0 | +0 | 0 |
| poker_player | 95% | 52.5% | +42.50% | 11.22s | 16.63s | -5.41s | 1 | 1 | +0 | 0 | 0 | +0 | 0 |
| real_estate_properties | 50% | 0% | +50% | 38.21s | 14.85s | +23.36s | 3.25 | 1.25 | +2 | 0 | 0 | +0 | 1 |
| singer | 96.67% | 50% | +46.67% | 13.69s | 13.91s | -0.22s | 1.1 | 1 | +0.10 | 0 | 0 | +0 | 0 |
| student_club | 53.16% | 0.63% | +52.53% | 57.87s | 19.13s | +38.74s | 2.67 | 1.03 | +1.64 | 0 | 0 | +0 | 4 |
| student_transcripts_tracking | 61.54% | 0% | +61.54% | 31.49s | 20.44s | +11.05s | 2.06 | 1 | +1.06 | 0 | 0 | +0 | 2 |
| superhero | 23.26% | 6.98% | +16.28% | 77.98s | 23.98s | +54s | 2.59 | 1.01 | +1.58 | 0 | 0 | +0 | 8 |
| toxicology | 20.69% | 0% | +20.69% | 41.65s | 20.48s | +21.17s | 2.63 | 1.03 | +1.60 | 0 | 0 | +0 | 1 |
| tvshow | 90.32% | 9.68% | +80.64% | 20.15s | 14.43s | +5.72s | 1.73 | 1 | +0.73 | 0 | 0 | +0 | 0 |
| voter_1 | 80% | 6.67% | +73.33% | 24.38s | 15.69s | +8.69s | 1.73 | 1 | +0.73 | 0 | 0 | +0 | 0 |
| **MODEL VERDICT** | **55.47%** | **7.15%** | **+48.31%** | **39.11s** | **22.9s** | **+16.21s** | **2.08** | **1.1** | **+0.97** | **0** | **0** | **+0** | **33** |

## Correlations

| Database | Attempts Pearson float db_conn | Attempts Pearson bool db_conn | Attempts Pearson float text | Attempts Pearson bool text | Attempts Pearson delta | Attempts Spearman float db_conn | Attempts Spearman bool db_conn | Attempts Spearman float text | Attempts Spearman bool text | Attempts Spearman delta | Complexity Pearson float db_conn | Complexity Pearson bool db_conn | Complexity Pearson float text | Complexity Pearson bool text | Complexity Pearson delta | Complexity Spearman float db_conn | Complexity Spearman bool db_conn | Complexity Spearman float text | Complexity Spearman bool text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 0.1741 | false | N/A | N/A | N/A | 0.1741 | false | N/A | N/A | N/A | -0.3386 | false | -0.1412 | false | -0.1974 | -0.3756 | false | -0.3383 | false | -0.0372 |
| california_schools | -0.2144 | false | -0.1967 | false | -0.0178 | -0.1828 | false | -0.1983 | false | +0.0155 | -0.2640 | true | -0.0624 | false | -0.2016 | -0.2478 | true | -0.0610 | false | -0.1868 |
| car_1 | -0.1694 | false | N/A | N/A | N/A | -0.0954 | false | N/A | N/A | N/A | -0.1302 | false | -0.0583 | false | -0.0719 | -0.0920 | false | -0.0433 | false | -0.0487 |
| card_games | -0.2184 | true | -0.0215 | false | -0.1969 | -0.1680 | true | -0.0229 | false | -0.1451 | -0.2004 | true | -0.0793 | false | -0.1210 | -0.1913 | true | -0.0863 | false | -0.1050 |
| codebase_community | -0.3103 | true | -0.0278 | false | -0.2826 | -0.2796 | true | -0.0289 | false | -0.2508 | -0.2640 | true | -0.0276 | false | -0.2364 | -0.2758 | true | -0.0265 | false | -0.2492 |
| concert_singer | -0.3478 | true | N/A | N/A | N/A | -0.2407 | false | N/A | N/A | N/A | -0.2145 | false | -0.2368 | false | +0.0223 | -0.2099 | false | -0.2336 | false | +0.0237 |
| course_teach | 0.0000 | false | N/A | N/A | N/A | -0.0497 | false | N/A | N/A | N/A | -0.3221 | false | 0.3734 | true | -0.6956 | -0.3473 | false | 0.3125 | false | -0.6598 |
| cre_Doc_Template_Mgt | -0.0595 | false | N/A | N/A | N/A | -0.0829 | false | N/A | N/A | N/A | -0.3747 | true | N/A | N/A | N/A | -0.3668 | true | N/A | N/A | N/A |
| debit_card_specializing | -0.1267 | false | -0.0306 | false | -0.0961 | -0.1437 | false | -0.0323 | false | -0.1115 | -0.1554 | false | -0.0021 | false | -0.1533 | -0.1992 | false | 0.0609 | false | -0.2601 |
| dog_kennels | -0.3264 | true | N/A | N/A | N/A | -0.1291 | false | N/A | N/A | N/A | -0.2229 | true | -0.0581 | false | -0.1648 | -0.2104 | false | -0.0659 | false | -0.1445 |
| employee_hire_evaluation | 0.0377 | false | N/A | N/A | N/A | 0.0377 | false | N/A | N/A | N/A | -0.3680 | true | -0.0919 | false | -0.2762 | -0.3283 | true | -0.1221 | false | -0.2062 |
| european_football_2 | -0.2963 | true | -0.0038 | false | -0.2925 | -0.2633 | true | 0.0219 | false | -0.2852 | -0.1422 | false | -0.1624 | false | +0.0202 | -0.1609 | false | -0.1952 | true | +0.0344 |
| financial | -0.4300 | true | N/A | N/A | N/A | -0.4086 | true | N/A | N/A | N/A | 0.1238 | false | N/A | N/A | N/A | 0.1100 | false | N/A | N/A | N/A |
| flight_2 | -0.2923 | true | N/A | N/A | N/A | -0.2461 | true | N/A | N/A | N/A | -0.2253 | true | -0.0058 | false | -0.2195 | -0.2423 | true | -0.0042 | false | -0.2381 |
| formula_1 | -0.3244 | true | -0.0156 | false | -0.3088 | -0.3150 | true | -0.0156 | false | -0.2994 | -0.1933 | true | -0.0726 | false | -0.1207 | -0.1905 | true | -0.0547 | false | -0.1359 |
| museum_visit | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| network_1 | -0.1474 | false | N/A | N/A | N/A | -0.2191 | false | N/A | N/A | N/A | -0.2113 | false | N/A | N/A | N/A | -0.2298 | false | N/A | N/A | N/A |
| orchestra | -0.2201 | false | -0.0863 | false | -0.1338 | -0.2398 | false | -0.0863 | false | -0.1535 | -0.3200 | true | 0.0639 | false | -0.3839 | -0.3062 | false | 0.0959 | false | -0.4021 |
| pets_1 | -0.0574 | false | N/A | N/A | N/A | -0.0574 | false | N/A | N/A | N/A | -0.3028 | false | -0.2865 | false | -0.0163 | -0.3393 | true | -0.2891 | false | -0.0502 |
| poker_player | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 0.2860 | false | 0.2896 | false | -0.0036 | 0.3222 | true | 0.2812 | false | +0.0410 |
| real_estate_properties | -0.5774 | false | N/A | N/A | N/A | -0.5774 | false | N/A | N/A | N/A | 1.0000 | true | N/A | N/A | N/A | 1.0000 | true | N/A | N/A | N/A |
| singer | 0.0469 | false | N/A | N/A | N/A | 0.0496 | false | N/A | N/A | N/A | -0.2913 | false | -0.2802 | false | -0.0112 | -0.2648 | false | -0.3169 | false | +0.0521 |
| student_club | -0.4951 | true | -0.0081 | false | -0.4871 | -0.5040 | true | -0.0090 | false | -0.4950 | -0.0608 | false | 0.0261 | false | -0.0869 | -0.0922 | false | 0.0559 | false | -0.1480 |
| student_transcripts_tracking | -0.4279 | true | N/A | N/A | N/A | -0.3427 | true | N/A | N/A | N/A | -0.2937 | true | N/A | N/A | N/A | -0.2762 | true | N/A | N/A | N/A |
| superhero | -0.5436 | true | -0.0242 | false | -0.5194 | -0.5098 | true | -0.0242 | false | -0.4856 | -0.3714 | true | -0.0078 | false | -0.3636 | -0.3416 | true | 0.0178 | false | -0.3593 |
| toxicology | -0.2984 | true | N/A | N/A | N/A | -0.3363 | true | N/A | N/A | N/A | -0.2478 | true | N/A | N/A | N/A | -0.2886 | true | N/A | N/A | N/A |
| tvshow | -0.3656 | true | N/A | N/A | N/A | -0.2832 | true | N/A | N/A | N/A | -0.1822 | false | 0.0746 | false | -0.2569 | -0.1756 | false | 0.0255 | false | -0.2012 |
| voter_1 | 0.3487 | false | N/A | N/A | N/A | 0.3563 | false | N/A | N/A | N/A | 0.2729 | false | -0.2674 | false | +0.5403 | 0.2381 | false | -0.3182 | false | +0.5564 |
| **MODEL VERDICT** | **-0.2170** | **13/26** | **-0.0461** | **0/9** | **-0.1709** | **-0.1945** | **11/26** | **-0.0439** | **0/9** | **-0.1506** | **-0.1487** | **13/27** | **-0.0482** | **1/21** | **-0.1005** | **-0.1512** | **13/27** | **-0.0622** | **1/21** | **-0.0890** |
