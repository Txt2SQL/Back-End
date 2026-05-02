# Model Performance Comparison: `codellama:34b`

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
| battle_death | 43.75% | 50% | -6.25% | 15.02s | 4.97s | +10.05s | 3.06 | 1.19 | +1.87 | 0 | 0 | +0 | 2 |
| california_schools | 12.36% | 3.37% | +8.99% | 26.28s | 9.15s | +17.13s | 4.19 | 1.44 | +2.75 | 0 | 0 | +0 | 23 |
| car_1 | 39.13% | 28.26% | +10.87% | 16.01s | 5.44s | +10.57s | 2.99 | 1.01 | +1.98 | 0 | 0 | +0 | 12 |
| card_games | 23.04% | 7.33% | +15.71% | 20.91s | 9.5s | +11.41s | 3.5 | 1.14 | +2.36 | 0 | 0 | +0 | 25 |
| codebase_community | 38.71% | 22.04% | +16.67% | 20.09s | 7.9s | +12.19s | 3.16 | 1.08 | +2.08 | 0 | 0 | +0 | 22 |
| concert_singer | 68.89% | 37.78% | +31.11% | 11.35s | 4.82s | +6.53s | 2.18 | 1 | +1.18 | 0 | 0 | +0 | 3 |
| course_teach | 60% | 40% | +20% | 9.87s | 5.05s | +4.82s | 2 | 1.07 | +0.93 | 0 | 0 | +0 | 0 |
| cre_Doc_Template_Mgt | 66.67% | 46.43% | +20.24% | 15.05s | 5.01s | +10.04s | 3.17 | 1.05 | +2.12 | 0 | 0 | +0 | 10 |
| debit_card_specializing | 4.69% | 6.25% | -1.56% | 23.78s | 6.35s | +17.43s | 3.94 | 1.08 | +2.86 | 0 | 0 | +0 | 12 |
| dog_kennels | 50% | 31.71% | +18.29% | 16.41s | 5.28s | +11.13s | 2.77 | 1.02 | +1.75 | 0 | 0 | +0 | 12 |
| employee_hire_evaluation | 71.05% | 47.37% | +23.68% | 12.81s | 4.76s | +8.05s | 2.82 | 1 | +1.82 | 0 | 0 | +0 | 4 |
| european_football_2 | 15.5% | 10.08% | +5.42% | 24.69s | 13.88s | +10.81s | 3.57 | 1.1 | +2.47 | 0 | 0 | +0 | 11 |
| financial | 5.66% | 2.83% | +2.83% | 26.05s | 5.33s | +20.72s | 4.53 | 1.04 | +3.49 | 0 | 0 | +0 | 46 |
| flight_2 | 61.25% | 60% | +1.25% | 15.87s | 4.46s | +11.41s | 3.44 | 1.06 | +2.38 | 0 | 0 | +0 | 11 |
| formula_1 | 17.82% | 9.2% | +8.62% | 23.12s | 5.89s | +17.23s | 3.94 | 1.05 | +2.89 | 0 | 0 | +0 | 37 |
| museum_visit | 72.22% | 38.89% | +33.33% | 13.88s | 14.68s | -0.80s | 3 | 1.06 | +1.94 | 0 | 0 | +0 | 3 |
| network_1 | 57.14% | 53.57% | +3.57% | 16.54s | 4.9s | +11.64s | 3.36 | 1.04 | +2.32 | 0 | 0 | +0 | 6 |
| orchestra | 87.5% | 75% | +12.50% | 9.96s | 4.53s | +5.43s | 1.95 | 1.07 | +0.88 | 0 | 0 | +0 | 0 |
| pets_1 | 71.43% | 40.48% | +30.95% | 11.82s | 5.07s | +6.75s | 2.29 | 1 | +1.29 | 0 | 0 | +0 | 1 |
| poker_player | 80% | 72.5% | +7.50% | 9.27s | 4.15s | +5.12s | 1.88 | 1.05 | +0.83 | 0 | 0 | +0 | 1 |
| real_estate_properties | 50% | 25% | +25% | 15.05s | 5.86s | +9.19s | 3 | 1 | +2 | 0 | 0 | +0 | 0 |
| singer | 83.33% | 66.67% | +16.66% | 7.28s | 4.24s | +3.04s | 1.4 | 1.03 | +0.37 | 0 | 0 | +0 | 0 |
| student_club | 30.38% | 13.29% | +17.09% | 18.44s | 5.32s | +13.12s | 3.39 | 1.09 | +2.30 | 0 | 0 | +0 | 24 |
| student_transcripts_tracking | 44.87% | 24.36% | +20.51% | 19.33s | 5.56s | +13.77s | 3.1 | 1.01 | +2.09 | 1 | 0 | +1 | 10 |
| superhero | 21.71% | 5.43% | +16.28% | 21.9s | 4.68s | +17.22s | 4.04 | 1.03 | +3.01 | 0 | 0 | +0 | 42 |
| toxicology | 10.34% | 4.83% | +5.51% | 26.24s | 6.42s | +19.82s | 4.3 | 1.03 | +3.27 | 0 | 0 | +0 | 46 |
| tvshow | 53.23% | 25.81% | +27.42% | 15.27s | 5.05s | +10.22s | 3.08 | 1.02 | +2.06 | 0 | 0 | +0 | 10 |
| voter_1 | 53.33% | 40% | +13.33% | 17.3s | 4.8s | +12.50s | 3.21 | 1 | +2.21 | 0 | 0 | +0 | 4 |
| **MODEL VERDICT** | **35.45%** | **22.4%** | **+13.04%** | **19.53s** | **6.6s** | **+12.94s** | **3.41** | **1.07** | **+2.33** | **1** | **0** | **+1** | **377** |

## Correlations

| Database | Attempts Pearson float db_conn | Attempts Pearson bool db_conn | Attempts Pearson float text | Attempts Pearson bool text | Attempts Pearson delta | Attempts Spearman float db_conn | Attempts Spearman bool db_conn | Attempts Spearman float text | Attempts Spearman bool text | Attempts Spearman delta | Complexity Pearson float db_conn | Complexity Pearson bool db_conn | Complexity Pearson float text | Complexity Pearson bool text | Complexity Pearson delta | Complexity Spearman float db_conn | Complexity Spearman bool db_conn | Complexity Spearman float text | Complexity Spearman bool text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.4478 | false | -0.1601 | false | -0.2877 | -0.4975 | true | -0.1601 | false | -0.3374 | -0.0931 | false | -0.5007 | true | +0.4076 | -0.2960 | false | -0.5315 | true | +0.2354 |
| california_schools | -0.2777 | true | -0.1068 | false | -0.1709 | -0.2528 | true | -0.1199 | false | -0.1329 | -0.2133 | false | -0.1673 | false | -0.0461 | -0.2043 | false | -0.1809 | false | -0.0234 |
| car_1 | -0.2977 | true | -0.0658 | false | -0.2319 | -0.3377 | true | -0.0658 | false | -0.2719 | -0.3352 | true | -0.3160 | true | -0.0192 | -0.3249 | true | -0.3445 | true | +0.0195 |
| card_games | -0.1978 | true | 0.0018 | false | -0.1996 | -0.2040 | true | 0.0407 | false | -0.2447 | -0.2271 | true | -0.1403 | false | -0.0868 | -0.2342 | true | -0.1829 | true | -0.0513 |
| codebase_community | -0.3805 | true | -0.1118 | false | -0.2687 | -0.3843 | true | -0.1118 | false | -0.2725 | -0.1831 | true | -0.1765 | true | -0.0066 | -0.1990 | true | -0.1454 | true | -0.0536 |
| concert_singer | -0.5569 | true | N/A | N/A | N/A | -0.5565 | true | N/A | N/A | N/A | -0.1710 | false | -0.1842 | false | +0.0133 | -0.1719 | false | -0.1852 | false | +0.0134 |
| course_teach | -0.1667 | false | -0.2182 | false | +0.0516 | -0.2011 | false | -0.2182 | false | +0.0171 | 0.2239 | false | 0.1493 | false | +0.0746 | 0.2208 | false | 0.1718 | false | +0.0491 |
| cre_Doc_Template_Mgt | -0.4171 | true | 0.0160 | false | -0.4331 | -0.4120 | true | 0.0160 | false | -0.4280 | 0.0153 | false | -0.0752 | false | +0.0905 | 0.0225 | false | -0.0698 | false | +0.0923 |
| debit_card_specializing | -0.1127 | false | -0.0752 | false | -0.0375 | -0.1156 | false | -0.0752 | false | -0.0405 | -0.1391 | false | -0.1930 | false | +0.0539 | -0.2407 | false | -0.3505 | true | +0.1098 |
| dog_kennels | -0.4272 | true | -0.1077 | false | -0.3195 | -0.4051 | true | -0.1077 | false | -0.2973 | -0.4280 | true | -0.4310 | true | +0.0029 | -0.3940 | true | -0.4439 | true | +0.0499 |
| employee_hire_evaluation | -0.4311 | true | N/A | N/A | N/A | -0.4198 | true | N/A | N/A | N/A | 0.1600 | false | 0.1864 | false | -0.0265 | 0.1616 | false | 0.2202 | false | -0.0586 |
| european_football_2 | -0.3505 | true | -0.0253 | false | -0.3251 | -0.3582 | true | -0.0201 | false | -0.3381 | -0.0789 | false | -0.1416 | false | +0.0627 | -0.1530 | false | -0.1418 | false | -0.0112 |
| financial | -0.3050 | true | -0.0277 | false | -0.2773 | -0.3038 | true | -0.0294 | false | -0.2744 | -0.2264 | true | -0.0973 | false | -0.1291 | -0.2358 | true | -0.1107 | false | -0.1251 |
| flight_2 | -0.4390 | true | -0.0000 | false | -0.4390 | -0.4636 | true | 0.0000 | false | -0.4636 | -0.3416 | true | -0.0774 | false | -0.2641 | -0.3255 | true | -0.0545 | false | -0.2710 |
| formula_1 | -0.2679 | true | 0.0146 | false | -0.2825 | -0.2722 | true | 0.0146 | false | -0.2868 | -0.0980 | false | -0.0857 | false | -0.0122 | -0.1018 | false | -0.0940 | false | -0.0078 |
| museum_visit | -0.5684 | true | 0.3040 | false | -0.8724 | -0.5857 | true | 0.3040 | false | -0.8897 | -0.3439 | false | 0.0519 | false | -0.3958 | -0.2917 | false | 0.1117 | false | -0.4034 |
| network_1 | -0.2762 | true | 0.1792 | false | -0.4553 | -0.2854 | true | 0.1792 | false | -0.4645 | -0.2750 | true | -0.1507 | false | -0.1243 | -0.2969 | true | -0.1799 | false | -0.1170 |
| orchestra | 0.0554 | false | -0.0548 | false | +0.1102 | 0.0590 | false | -0.0548 | false | +0.1138 | -0.3722 | true | -0.2606 | false | -0.1116 | -0.2892 | false | -0.1952 | false | -0.0940 |
| pets_1 | -0.4615 | true | N/A | N/A | N/A | -0.4250 | true | N/A | N/A | N/A | -0.2493 | false | 0.0774 | false | -0.3267 | -0.2558 | false | 0.0203 | false | -0.2760 |
| poker_player | -0.3899 | true | 0.1413 | false | -0.5311 | -0.3582 | true | 0.1413 | false | -0.4995 | -0.1758 | false | 0.0519 | false | -0.2277 | -0.1229 | false | 0.0419 | false | -0.1648 |
| real_estate_properties | -0.5774 | false | N/A | N/A | N/A | -0.5774 | false | N/A | N/A | N/A | 1.0000 | true | 0.9272 | false | +0.0728 | 1.0000 | true | 0.8165 | false | +0.1835 |
| singer | -0.2928 | false | 0.1313 | false | -0.4241 | -0.1623 | false | 0.1313 | false | -0.2936 | 0.0877 | false | -0.0099 | false | +0.0976 | 0.0744 | false | -0.0756 | false | +0.1500 |
| student_club | -0.4409 | true | -0.0533 | false | -0.3876 | -0.4493 | true | -0.0506 | false | -0.3987 | -0.1402 | false | -0.0456 | false | -0.0947 | -0.1137 | false | -0.0657 | false | -0.0480 |
| student_transcripts_tracking | -0.3126 | true | -0.0647 | false | -0.2480 | -0.3156 | true | -0.0647 | false | -0.2509 | -0.1925 | false | -0.2610 | true | +0.0684 | -0.1977 | false | -0.2359 | true | +0.0383 |
| superhero | -0.5125 | true | -0.0432 | false | -0.4693 | -0.5075 | true | -0.0432 | false | -0.4643 | -0.1907 | false | -0.1783 | true | -0.0124 | -0.2424 | true | -0.2094 | true | -0.0330 |
| toxicology | -0.3663 | true | 0.1335 | false | -0.4998 | -0.3537 | true | 0.1335 | false | -0.4872 | -0.0995 | false | -0.0934 | false | -0.0061 | -0.1167 | false | -0.0846 | false | -0.0321 |
| tvshow | -0.4571 | true | -0.0755 | false | -0.3816 | -0.4485 | true | -0.0755 | false | -0.3729 | -0.0915 | false | -0.1261 | false | +0.0345 | -0.0643 | false | -0.1143 | false | +0.0500 |
| voter_1 | -0.6383 | true | N/A | N/A | N/A | -0.6035 | true | N/A | N/A | N/A | -0.1345 | false | -0.5848 | true | +0.4504 | -0.0741 | false | -0.5995 | true | +0.5254 |
| **MODEL VERDICT** | **-0.3684** | **22/28** | **-0.0117** | **0/23** | **-0.3567** | **-0.3642** | **23/28** | **-0.0103** | **0/23** | **-0.3539** | **-0.1183** | **9/28** | **-0.1019** | **7/28** | **-0.0164** | **-0.1238** | **9/28** | **-0.1148** | **9/28** | **-0.0091** |
