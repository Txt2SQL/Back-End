# Model Performance Comparison: `Qwen3-coder-next`

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
| battle_death | 93.75% | 81.25% | +12.50% | 6.35s | 4.27s | +2.08s | 1.19 | 1 | +0.19 | 0 | 0 | +0 | 0 |
| california_schools | 34.83% | 28.09% | +6.74% | 14.15s | 9.11s | +5.04s | 1.81 | 2.28 | -0.47 | 0 | 0 | +0 | 0 |
| car_1 | 59.78% | 58.7% | +1.08% | 9.5s | 5.37s | +4.13s | 1.46 | 1 | +0.46 | 0 | 0 | +0 | 0 |
| card_games | 37.17% | 25.65% | +11.52% | 13.62s | 7.42s | +6.20s | 1.74 | 1.03 | +0.71 | 0 | 0 | +0 | 0 |
| codebase_community | 49.46% | 43.55% | +5.91% | 10.99s | 5.87s | +5.12s | 1.56 | 1 | +0.56 | 0 | 0 | +0 | 0 |
| concert_singer | 82.22% | 84.44% | -2.22% | 7.53s | 4.26s | +3.27s | 1.16 | 1 | +0.16 | 0 | 0 | +0 | 0 |
| course_teach | 96.67% | 86.67% | +10% | 5.8s | 3.99s | +1.81s | 1.07 | 1 | +0.07 | 0 | 0 | +0 | 0 |
| cre_Doc_Template_Mgt | 91.67% | 80.95% | +10.72% | 6.15s | 3.95s | +2.20s | 1.27 | 1 | +0.27 | 0 | 0 | +0 | 0 |
| debit_card_specializing | 28.12% | 32.81% | -4.69% | 12.52s | 6.41s | +6.11s | 1.61 | 1 | +0.61 | 0 | 0 | +0 | 0 |
| dog_kennels | 71.95% | 65.85% | +6.10% | 9.81s | 4.73s | +5.08s | 1.54 | 1 | +0.54 | 0 | 0 | +0 | 4 |
| employee_hire_evaluation | 97.37% | 97.37% | +0% | 5.39s | 4.18s | +1.21s | 1 | 1 | +0 | 0 | 0 | +0 | 0 |
| european_football_2 | 52.71% | 51.16% | +1.55% | 15.22s | 7.83s | +7.39s | 1.74 | 1 | +0.74 | 0 | 0 | +0 | 1 |
| financial | 26.42% | 17.92% | +8.50% | 22.21s | 5.12s | +17.09s | 2.67 | 1.05 | +1.62 | 0 | 0 | +0 | 11 |
| flight_2 | 78.75% | 78.75% | +0% | 6.33s | 3.89s | +2.44s | 1.26 | 1 | +0.26 | 0 | 0 | +0 | 0 |
| formula_1 | 42.53% | 30.46% | +12.07% | 14.33s | 5.89s | +8.44s | 1.99 | 1 | +0.99 | 0 | 0 | +0 | 2 |
| museum_visit | 100% | 94.44% | +5.56% | 6.02s | 8.11s | -2.09s | 1.22 | 1 | +0.22 | 0 | 0 | +0 | 0 |
| network_1 | 83.93% | 83.93% | +0% | 7.79s | 3.77s | +4.02s | 1.75 | 1 | +0.75 | 0 | 0 | +0 | 0 |
| orchestra | 95% | 80% | +15% | 5.31s | 3.74s | +1.57s | 1.07 | 1 | +0.07 | 0 | 0 | +0 | 0 |
| pets_1 | 95.24% | 88.1% | +7.14% | 6.44s | 4.45s | +1.99s | 1.12 | 1 | +0.12 | 0 | 0 | +0 | 0 |
| poker_player | 100% | 95% | +5% | 4.9s | 3.33s | +1.57s | 1.02 | 1 | +0.02 | 0 | 0 | +0 | 0 |
| real_estate_properties | 50% | 25% | +25% | 9.66s | 4.22s | +5.44s | 1.75 | 1 | +0.75 | 0 | 0 | +0 | 0 |
| singer | 96.67% | 96.67% | +0% | 5.2s | 3.37s | +1.83s | 1 | 1 | +0 | 0 | 0 | +0 | 0 |
| student_club | 50.63% | 44.94% | +5.69% | 11.17s | 4.74s | +6.43s | 1.81 | 1 | +0.81 | 0 | 0 | +0 | 7 |
| student_transcripts_tracking | 65.38% | 62.82% | +2.56% | 10.55s | 5.55s | +5.00s | 1.58 | 1 | +0.58 | 0 | 0 | +0 | 0 |
| superhero | 38.76% | 28.68% | +10.08% | 18.22s | 4.12s | +14.10s | 2.7 | 1.01 | +1.69 | 0 | 0 | +0 | 31 |
| toxicology | 22.07% | 19.31% | +2.76% | 12.39s | 5.78s | +6.61s | 1.74 | 1 | +0.74 | 0 | 0 | +0 | 1 |
| tvshow | 85.48% | 75.81% | +9.67% | 6.89s | 4.32s | +2.57s | 1.45 | 1 | +0.45 | 0 | 0 | +0 | 0 |
| voter_1 | 100% | 80% | +20% | 6.89s | 3.71s | +3.18s | 1.6 | 1 | +0.60 | 0 | 0 | +0 | 0 |
| **MODEL VERDICT** | **56.18%** | **50.02%** | **+6.16%** | **11.57s** | **5.48s** | **+6.09s** | **1.69** | **1.06** | **+0.64** | **0** | **0** | **+0** | **57** |

## Correlations

| Database | Attempts Pearson float db_conn | Attempts Pearson bool db_conn | Attempts Pearson float text | Attempts Pearson bool text | Attempts Pearson delta | Attempts Spearman float db_conn | Attempts Spearman bool db_conn | Attempts Spearman float text | Attempts Spearman bool text | Attempts Spearman delta | Complexity Pearson float db_conn | Complexity Pearson bool db_conn | Complexity Pearson float text | Complexity Pearson bool text | Complexity Pearson delta | Complexity Spearman float db_conn | Complexity Spearman bool db_conn | Complexity Spearman float text | Complexity Spearman bool text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.5375 | true | N/A | N/A | N/A | -0.5375 | true | N/A | N/A | N/A | -0.3386 | false | -0.3856 | false | +0.0470 | -0.3756 | false | -0.5375 | true | +0.1619 |
| california_schools | -0.3193 | true | -0.4131 | true | +0.0938 | -0.3570 | true | -0.4272 | true | +0.0701 | -0.2139 | false | -0.2005 | false | -0.0134 | -0.1791 | false | -0.2012 | false | +0.0220 |
| car_1 | -0.4098 | true | N/A | N/A | N/A | -0.3335 | true | N/A | N/A | N/A | 0.0027 | false | -0.1942 | false | +0.1968 | 0.0217 | false | -0.1383 | false | +0.1600 |
| card_games | -0.2822 | true | -0.0173 | false | -0.2649 | -0.2740 | true | 0.0197 | false | -0.2937 | -0.2426 | true | -0.2037 | true | -0.0388 | -0.2461 | true | -0.2140 | true | -0.0321 |
| codebase_community | -0.3853 | true | N/A | N/A | N/A | -0.3779 | true | N/A | N/A | N/A | -0.2134 | true | -0.1946 | true | -0.0187 | -0.1974 | true | -0.1564 | true | -0.0411 |
| concert_singer | -0.5029 | true | N/A | N/A | N/A | -0.5744 | true | N/A | N/A | N/A | -0.1791 | false | -0.1612 | false | -0.0179 | -0.1670 | false | -0.1540 | false | -0.0130 |
| course_teach | 0.0345 | false | N/A | N/A | N/A | 0.0345 | false | N/A | N/A | N/A | -0.2279 | false | -0.3278 | false | +0.0999 | -0.2456 | false | -0.3536 | false | +0.1081 |
| cre_Doc_Template_Mgt | -0.0066 | false | N/A | N/A | N/A | -0.0329 | false | N/A | N/A | N/A | -0.1012 | false | -0.1510 | false | +0.0498 | -0.0712 | false | -0.1426 | false | +0.0714 |
| debit_card_specializing | -0.3485 | true | N/A | N/A | N/A | -0.3717 | true | N/A | N/A | N/A | -0.2744 | true | -0.2122 | false | -0.0622 | -0.3951 | true | -0.2503 | true | -0.1448 |
| dog_kennels | -0.3520 | true | N/A | N/A | N/A | -0.2841 | true | N/A | N/A | N/A | -0.2493 | true | -0.1121 | false | -0.1371 | -0.2660 | true | -0.1086 | false | -0.1574 |
| employee_hire_evaluation | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | -0.2567 | false | -0.2567 | false | +0.0000 | -0.2290 | false | -0.2290 | false | +0.0000 |
| european_football_2 | -0.4798 | true | N/A | N/A | N/A | -0.4911 | true | N/A | N/A | N/A | -0.1581 | false | -0.1440 | false | -0.0141 | -0.2183 | true | -0.1996 | true | -0.0187 |
| financial | -0.4198 | true | -0.0635 | false | -0.3563 | -0.4570 | true | -0.0648 | false | -0.3922 | -0.1263 | false | 0.0833 | false | -0.2095 | -0.1266 | false | 0.0903 | false | -0.2168 |
| flight_2 | -0.3290 | true | N/A | N/A | N/A | -0.3292 | true | N/A | N/A | N/A | -0.3982 | true | -0.3276 | true | -0.0705 | -0.3740 | true | -0.2939 | true | -0.0801 |
| formula_1 | -0.3942 | true | N/A | N/A | N/A | -0.4268 | true | N/A | N/A | N/A | -0.1565 | true | -0.0495 | false | -0.1070 | -0.1438 | false | -0.0417 | false | -0.1021 |
| museum_visit | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | -0.0803 | false | N/A | N/A | N/A | -0.1426 | false | N/A |
| network_1 | -0.3711 | true | N/A | N/A | N/A | -0.3230 | true | N/A | N/A | N/A | -0.0373 | false | -0.0180 | false | -0.0194 | -0.0947 | false | -0.0367 | false | -0.0580 |
| orchestra | -0.3702 | true | N/A | N/A | N/A | -0.3702 | true | N/A | N/A | N/A | -0.3200 | true | 0.0718 | false | -0.3918 | -0.3062 | false | 0.1112 | false | -0.4174 |
| pets_1 | -0.2630 | false | N/A | N/A | N/A | -0.2630 | false | N/A | N/A | N/A | -0.1236 | false | 0.3425 | true | -0.4661 | -0.0748 | false | 0.3260 | true | -0.4008 |
| poker_player | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | -0.0073 | false | N/A | N/A | N/A | -0.0430 | false | N/A |
| real_estate_properties | -0.3015 | false | N/A | N/A | N/A | -0.2357 | false | N/A | N/A | N/A | 1.0000 | true | -0.1325 | false | +1.1325 | 1.0000 | true | 0.0000 | false | +1.0000 |
| singer | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 0.1769 | false | 0.1769 | false | +0.0000 | 0.2207 | false | 0.2207 | false | +0.0000 |
| student_club | -0.4415 | true | N/A | N/A | N/A | -0.4536 | true | N/A | N/A | N/A | -0.1201 | false | -0.0116 | false | -0.1085 | -0.1258 | false | -0.0593 | false | -0.0665 |
| student_transcripts_tracking | -0.4574 | true | N/A | N/A | N/A | -0.4558 | true | N/A | N/A | N/A | -0.3599 | true | -0.2546 | true | -0.1053 | -0.3568 | true | -0.2303 | true | -0.1265 |
| superhero | -0.5350 | true | -0.0571 | false | -0.4779 | -0.5190 | true | -0.0571 | false | -0.4619 | -0.2089 | true | -0.0513 | false | -0.1576 | -0.1860 | false | -0.0962 | false | -0.0898 |
| toxicology | -0.2622 | true | N/A | N/A | N/A | -0.2769 | true | N/A | N/A | N/A | -0.2477 | true | -0.2549 | true | +0.0072 | -0.2981 | true | -0.2965 | true | -0.0016 |
| tvshow | -0.3682 | true | N/A | N/A | N/A | -0.3042 | true | N/A | N/A | N/A | -0.3197 | true | -0.2588 | true | -0.0609 | -0.3162 | true | -0.2381 | false | -0.0782 |
| voter_1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | -0.0114 | false | N/A | N/A | N/A | 0.1191 | false | N/A |
| **MODEL VERDICT** | **-0.3523** | **19/23** | **-0.1378** | **1/4** | **-0.2145** | **-0.3484** | **19/23** | **-0.1324** | **1/4** | **-0.2161** | **-0.1478** | **12/25** | **-0.1188** | **7/28** | **-0.0289** | **-0.1500** | **10/25** | **-0.1177** | **9/28** | **-0.0323** |
