# Model Performance Comparison: `sqlcoder:34b`

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
| battle_death | 56.25% | 25% | +31.25% | 13.35s | 4.4s | +8.95s | 3.75 | 1.31 | +2.44 | 2 | 0 | +2 | 2 |
| california_schools | 0% | 2.25% | -2.25% | 23.88s | 5.16s | +18.72s | 5.19 | 1.44 | +3.75 | 17 | 0 | +17 | 58 |
| car_1 | 26.09% | 29.35% | -3.26% | 15.07s | 4.48s | +10.59s | 4.07 | 1.36 | +2.71 | 7 | 0 | +7 | 40 |
| card_games | 7.33% | 5.76% | +1.57% | 20.62s | 4.62s | +16s | 4.8 | 1.3 | +3.50 | 26 | 0 | +26 | 99 |
| codebase_community | 24.73% | 11.29% | +13.44% | 20.25s | 6.77s | +13.48s | 4.01 | 1.3 | +2.71 | 18 | 0 | +18 | 53 |
| concert_singer | 57.78% | 60% | -2.22% | 11.66s | 4.4s | +7.26s | 3.11 | 1.18 | +1.93 | 2 | 0 | +2 | 10 |
| course_teach | 50% | 46.67% | +3.33% | 13.59s | 4.4s | +9.19s | 4 | 1.33 | +2.67 | 0 | 0 | +0 | 12 |
| cre_Doc_Template_Mgt | 32.14% | 22.62% | +9.52% | 18.63s | 4.11s | +14.52s | 4.39 | 1.25 | +3.14 | 10 | 0 | +10 | 42 |
| debit_card_specializing | 3.12% | 1.56% | +1.56% | 21.59s | 5.41s | +16.18s | 4.86 | 1.19 | +3.67 | 9 | 0 | +9 | 26 |
| dog_kennels | 26.83% | 12.2% | +14.63% | 22.91s | 4.62s | +18.29s | 4.39 | 1.24 | +3.15 | 9 | 0 | +9 | 42 |
| employee_hire_evaluation | 84.21% | 76.32% | +7.89% | 9.14s | 4.26s | +4.88s | 2.5 | 1.18 | +1.32 | 2 | 0 | +2 | 3 |
| european_football_2 | 19.38% | 5.43% | +13.95% | 22.63s | 8.48s | +14.15s | 4.67 | 1.31 | +3.36 | 22 | 0 | +22 | 52 |
| financial | 3.77% | 0% | +3.77% | 27.07s | 6.67s | +20.40s | 4.79 | 1.16 | +3.63 | 13 | 0 | +13 | 55 |
| flight_2 | 21.25% | 17.5% | +3.75% | 17.33s | 6.94s | +10.39s | 4.55 | 1.12 | +3.43 | 11 | 0 | +11 | 42 |
| formula_1 | 13.22% | 9.77% | +3.45% | 22.4s | 4.58s | +17.82s | 4.65 | 1.26 | +3.39 | 21 | 0 | +21 | 75 |
| museum_visit | 44.44% | 61.11% | -16.67% | 15.42s | 13.97s | +1.45s | 3.5 | 1 | +2.50 | 4 | 0 | +4 | 4 |
| network_1 | 46.43% | 39.29% | +7.14% | 14.25s | 4.35s | +9.90s | 3.91 | 1.27 | +2.64 | 3 | 0 | +3 | 4 |
| orchestra | 52.5% | 30% | +22.50% | 19.69s | 3.99s | +15.70s | 3.85 | 1.25 | +2.60 | 2 | 0 | +2 | 17 |
| pets_1 | 45.24% | 21.43% | +23.81% | 14.39s | 3.95s | +10.44s | 3.86 | 1.12 | +2.74 | 3 | 0 | +3 | 18 |
| poker_player | 87.5% | 77.5% | +10% | 6.54s | 4.01s | +2.53s | 1.82 | 1.2 | +0.62 | 0 | 0 | +0 | 1 |
| real_estate_properties | 50% | 0% | +50% | 16.34s | 4.77s | +11.57s | 3.75 | 1.25 | +2.50 | 1 | 0 | +1 | 1 |
| singer | 76.67% | 63.33% | +13.34% | 9.91s | 3.57s | +6.34s | 3 | 1.17 | +1.83 | 1 | 0 | +1 | 4 |
| student_club | 30.38% | 13.92% | +16.46% | 16.51s | 4.41s | +12.10s | 3.93 | 1.28 | +2.65 | 9 | 0 | +9 | 45 |
| student_transcripts_tracking | 26.92% | 19.23% | +7.69% | 18.13s | 4.81s | +13.32s | 4.24 | 1.36 | +2.88 | 10 | 0 | +10 | 35 |
| superhero | 11.63% | 1.55% | +10.08% | 21.55s | 3.4s | +18.15s | 4.82 | 1.37 | +3.45 | 19 | 0 | +19 | 56 |
| toxicology | 5.52% | 2.76% | +2.76% | 26.37s | 3.64s | +22.73s | 4.69 | 1.28 | +3.41 | 13 | 0 | +13 | 94 |
| tvshow | 40.32% | 19.35% | +20.97% | 18.15s | 4.5s | +13.65s | 4.13 | 1.19 | +2.94 | 1 | 0 | +1 | 28 |
| voter_1 | 40% | 26.67% | +13.33% | 15.11s | 4.49s | +10.62s | 3.67 | 1.07 | +2.60 | 0 | 0 | +0 | 4 |
| **MODEL VERDICT** | **24.43%** | **16.46%** | **+7.96%** | **19.65s** | **5.08s** | **+14.57s** | **4.31** | **1.27** | **+3.04** | **235** | **0** | **+235** | **922** |

## Correlations

| Database | Attempts Pearson float db_conn | Attempts Pearson bool db_conn | Attempts Pearson float text | Attempts Pearson bool text | Attempts Pearson delta | Attempts Spearman float db_conn | Attempts Spearman bool db_conn | Attempts Spearman float text | Attempts Spearman bool text | Attempts Spearman delta | Complexity Pearson float db_conn | Complexity Pearson bool db_conn | Complexity Pearson float text | Complexity Pearson bool text | Complexity Pearson delta | Complexity Spearman float db_conn | Complexity Spearman bool db_conn | Complexity Spearman float text | Complexity Spearman bool text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.7019 | true | -0.3095 | false | -0.3924 | -0.6967 | true | -0.3308 | false | -0.3660 | -0.0991 | false | -0.4543 | false | +0.3551 | -0.2256 | false | -0.5491 | true | +0.3236 |
| california_schools | N/A | N/A | -0.0838 | false | N/A | N/A | N/A | -0.0987 | false | N/A | N/A | N/A | -0.1609 | false | N/A | N/A | N/A | -0.1719 | false | N/A |
| car_1 | -0.6752 | true | -0.0233 | false | -0.6519 | -0.6695 | true | -0.0632 | false | -0.6063 | -0.4437 | true | -0.4429 | true | -0.0007 | -0.5193 | true | -0.5169 | true | -0.0024 |
| card_games | -0.3328 | true | -0.0111 | false | -0.3216 | -0.3303 | true | 0.0245 | false | -0.3548 | -0.1720 | true | -0.0824 | false | -0.0895 | -0.1978 | true | -0.0904 | false | -0.1073 |
| codebase_community | -0.5547 | true | 0.0621 | false | -0.6168 | -0.5561 | true | 0.0753 | false | -0.6314 | -0.2342 | true | -0.0821 | false | -0.1521 | -0.2410 | true | -0.0638 | false | -0.1772 |
| concert_singer | -0.6645 | true | 0.0237 | false | -0.6883 | -0.6459 | true | 0.0237 | false | -0.6696 | -0.2005 | false | 0.0724 | false | -0.2729 | -0.2059 | false | 0.0783 | false | -0.2842 |
| course_teach | -0.3710 | true | 0.0374 | false | -0.4083 | -0.4425 | true | 0.0399 | false | -0.4824 | -0.3395 | false | -0.4223 | true | +0.0828 | -0.3446 | false | -0.4337 | true | +0.0891 |
| cre_Doc_Template_Mgt | -0.7554 | true | -0.0937 | false | -0.6617 | -0.8156 | true | -0.1225 | false | -0.6931 | 0.2245 | true | 0.3738 | true | -0.1494 | 0.2290 | true | 0.3617 | true | -0.1327 |
| debit_card_specializing | -0.2505 | true | 0.2063 | false | -0.4569 | -0.2634 | true | 0.2870 | true | -0.5504 | -0.0977 | false | -0.0324 | false | -0.0653 | -0.1601 | false | -0.0285 | false | -0.1316 |
| dog_kennels | -0.7713 | true | 0.1146 | false | -0.8859 | -0.7425 | true | 0.0938 | false | -0.8363 | -0.1477 | false | -0.0438 | false | -0.1039 | -0.1275 | false | -0.0305 | false | -0.0969 |
| employee_hire_evaluation | -0.7471 | true | 0.1708 | false | -0.9179 | -0.6272 | true | 0.1907 | false | -0.8179 | 0.0599 | false | 0.1918 | false | -0.1319 | 0.1072 | false | 0.1897 | false | -0.0824 |
| european_football_2 | -0.5768 | true | -0.1198 | false | -0.4570 | -0.5365 | true | -0.1309 | false | -0.4057 | -0.1751 | false | -0.1296 | false | -0.0454 | -0.1965 | true | -0.1599 | false | -0.0366 |
| financial | -0.2744 | true | N/A | N/A | N/A | -0.3026 | true | N/A | N/A | N/A | -0.1061 | false | N/A | N/A | N/A | -0.1214 | false | N/A | N/A | N/A |
| flight_2 | -0.8000 | true | 0.2238 | true | -1.0238 | -0.8245 | true | 0.2238 | true | -1.0483 | -0.0512 | false | -0.1713 | false | +0.1201 | -0.0486 | false | -0.1728 | false | +0.1243 |
| formula_1 | -0.4591 | true | 0.0210 | false | -0.4801 | -0.3981 | true | -0.0626 | false | -0.3354 | -0.0291 | false | -0.1033 | false | +0.0741 | -0.0141 | false | -0.0994 | false | +0.0853 |
| museum_visit | -0.7678 | true | N/A | N/A | N/A | -0.7641 | true | N/A | N/A | N/A | -0.2036 | false | -0.2216 | false | +0.0181 | -0.1205 | false | -0.2345 | false | +0.1140 |
| network_1 | -0.4275 | true | -0.1036 | false | -0.3239 | -0.4821 | true | -0.0136 | false | -0.4685 | -0.4764 | true | -0.1060 | false | -0.3704 | -0.4723 | true | -0.0919 | false | -0.3805 |
| orchestra | -0.7826 | true | 0.1017 | false | -0.8844 | -0.7858 | true | 0.0882 | false | -0.8740 | -0.2588 | false | -0.0940 | false | -0.1648 | -0.2183 | false | 0.0097 | false | -0.2280 |
| pets_1 | -0.8102 | true | -0.0083 | false | -0.8019 | -0.7990 | true | 0.0751 | false | -0.8740 | -0.3078 | true | -0.0095 | false | -0.2983 | -0.2882 | false | -0.0194 | false | -0.2687 |
| poker_player | -0.3121 | true | -0.0299 | false | -0.2821 | -0.2134 | false | -0.0299 | false | -0.1835 | 0.2778 | false | 0.3655 | true | -0.0876 | 0.2901 | false | 0.3755 | true | -0.0854 |
| real_estate_properties | -0.9113 | false | N/A | N/A | N/A | -0.8944 | false | N/A | N/A | N/A | 1.0000 | true | N/A | N/A | N/A | 1.0000 | true | N/A | N/A | N/A |
| singer | -0.8014 | true | -0.0254 | false | -0.7760 | -0.7263 | true | 0.0745 | false | -0.8008 | 0.1281 | false | 0.2306 | false | -0.1026 | 0.0000 | false | 0.2384 | false | -0.2384 |
| student_club | -0.4101 | true | -0.0088 | false | -0.4013 | -0.4045 | true | -0.0073 | false | -0.3971 | -0.1008 | false | 0.0501 | false | -0.1509 | -0.1364 | false | 0.0156 | false | -0.1520 |
| student_transcripts_tracking | -0.7647 | true | -0.1176 | false | -0.6471 | -0.7350 | true | -0.1405 | false | -0.5944 | -0.2555 | true | -0.1730 | false | -0.0825 | -0.2550 | true | -0.1434 | false | -0.1116 |
| superhero | -0.3404 | true | -0.0592 | false | -0.2812 | -0.3851 | true | -0.0729 | false | -0.3122 | -0.2013 | true | 0.0026 | false | -0.2038 | -0.2083 | true | 0.0052 | false | -0.2136 |
| toxicology | -0.1592 | false | -0.0834 | false | -0.0757 | -0.1003 | false | -0.0910 | false | -0.0093 | -0.1320 | false | -0.1495 | false | +0.0175 | -0.1490 | false | -0.1772 | true | +0.0282 |
| tvshow | -0.5174 | true | 0.0550 | false | -0.5724 | -0.5718 | true | 0.0354 | false | -0.6072 | -0.0774 | false | 0.3935 | true | -0.4709 | -0.1020 | false | 0.3441 | true | -0.4461 |
| voter_1 | -0.2660 | false | 0.4432 | false | -0.7092 | -0.3154 | false | 0.4432 | false | -0.7586 | 0.1578 | false | 0.0651 | false | +0.0927 | 0.2755 | false | 0.1616 | false | +0.1139 |
| **MODEL VERDICT** | **-0.5632** | **24/27** | **0.0153** | **1/25** | **-0.5785** | **-0.5566** | **23/27** | **0.0204** | **2/25** | **-0.5771** | **-0.0838** | **9/27** | **-0.0436** | **5/26** | **-0.0402** | **-0.0908** | **9/27** | **-0.0463** | **7/26** | **-0.0445** |
