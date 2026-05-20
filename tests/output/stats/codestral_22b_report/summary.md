# Model Performance Summary: `codestral:22b`

**Base directory:** `C:\Users\pietr\Desktop\UniTn\Tesi\Progetto Text2SQL\Back-End\tests\output\generations`

Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.

## Status

| Database | Success db_conn | Success text | Success delta | Avg time db_conn | Avg time text | Avg time delta | Avg attempts db_conn | Avg attempts text | Avg attempts delta | Syntax db_conn | Syntax text | Syntax delta | Runtime db_conn | Runtime text | Incorrect db_conn | Incorrect text | Incorrect delta | Incorrect perc db_conn | Incorrect perc text | Incorrect perc delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 93.75% | 68.75% | +25% | 7.84s | 3.54s | +4.3s | 1.25 | 1 | +0.25 | 0 | 0 | +0 | 0 | 2 | 1 | 3 | -2 | 6.25% | 21.43% | -15.18% |
| california_schools | 24.72% | 19.1% | +5.62% | 13.03s | 3.54s | +9.49s | 2.19 | 1.38 | +0.81 | 0 | 0 | +0 | 1 | 41 | 59 | 23 | +36 | 72.84% | 57.5% | +15.34% |
| car_1 | 52.17% | 50% | +2.17% | 11.15s | 5.77s | +5.38s | 1.7 | 1.04 | +0.65 | 0 | 0 | +0 | 2 | 6 | 41 | 39 | +2 | 46.07% | 45.88% | +0.19% |
| card_games | 29.32% | 27.23% | +2.09% | 6.05s | 6.42s | -0.37s | 1.05 | 1.05 | +0 | 0 | 0 | +0 | 12 | 8 | 120 | 121 | -1 | 68.18% | 69.94% | -1.76% |
| codebase_community | 44.09% | 37.1% | +6.99% | 10.28s | 5.16s | +5.12s | 1.77 | 1.01 | +0.76 | 0 | 0 | +0 | 3 | 31 | 94 | 81 | +13 | 53.41% | 54% | -0.59% |
| concert_singer | 82.22% | 86.67% | -4.44% | 7.15s | 4.27s | +2.89s | 1.2 | 1 | +0.2 | 0 | 0 | +0 | 1 | 1 | 7 | 5 | +2 | 15.91% | 11.36% | +4.55% |
| course_teach | 96.67% | 83.33% | +13.33% | 6.03s | 3.99s | +2.04s | 1.07 | 1 | +0.07 | 0 | 0 | +0 | 0 | 0 | 1 | 5 | -4 | 3.33% | 16.67% | -13.33% |
| cre_Doc_Template_Mgt | 89.29% | 83.33% | +5.95% | 7.02s | 4.29s | +2.73s | 1.29 | 1 | +0.29 | 0 | 0 | +0 | 0 | 4 | 9 | 10 | -1 | 10.71% | 12.5% | -1.79% |
| debit_card_specializing | 25% | 14.06% | +10.94% | 24.77s | 11.09s | +13.68s | 2.2 | 1 | +1.2 | 0 | 0 | +0 | 2 | 19 | 46 | 36 | +10 | 74.19% | 80% | -5.81% |
| dog_kennels | 63.41% | 64.63% | -1.22% | 10.03s | 5.11s | +4.93s | 1.54 | 1.01 | +0.52 | 0 | 0 | +0 | 2 | 9 | 28 | 20 | +8 | 35% | 27.4% | +7.6% |
| employee_hire_evaluation | 94.74% | 94.74% | +0% | 6.58s | 4.3s | +2.28s | 1.21 | 1 | +0.21 | 0 | 0 | +0 | 0 | 0 | 2 | 2 | +0 | 5.26% | 5.26% | +0% |
| european_football_2 | 17.83% | 37.21% | -19.38% | 20.42s | 9.74s | +10.68s | 1.4 | 1.1 | +0.29 | 0 | 0 | +0 | 1 | 16 | 23 | 55 | -32 | 50% | 53.4% | -3.4% |
| financial | 16.98% | 9.43% | +7.55% | 25.06s | 3.17s | +21.9s | 3.08 | 1.07 | +2.02 | 0 | 0 | +0 | 22 | 59 | 65 | 37 | +28 | 78.31% | 78.72% | -0.41% |
| flight_2 | 88.75% | 85% | +3.75% | 7.09s | 4.08s | +3.01s | 1.27 | 1 | +0.27 | 0 | 0 | +0 | 0 | 1 | 9 | 11 | -2 | 11.25% | 13.92% | -2.67% |
| formula_1 | 36.21% | 19.54% | +16.67% | 9.53s | 7.09s | +2.44s | 2.05 | 1 | +1.05 | 0 | 0 | +0 | 1 | 30 | 108 | 108 | +0 | 63.16% | 76.06% | -12.9% |
| museum_visit | 100% | 94.44% | +5.56% | 6.3s | 4.22s | +2.08s | 1.06 | 1 | +0.06 | 0 | 0 | +0 | 0 | 0 | 0 | 1 | -1 | 0% | 5.56% | -5.56% |
| network_1 | 80.36% | 78.57% | +1.79% | 8.02s | 4.54s | +3.48s | 1.59 | 1 | +0.59 | 0 | 0 | +0 | 0 | 0 | 11 | 12 | -1 | 19.64% | 21.43% | -1.79% |
| orchestra | 97.5% | 92.5% | +5% | 6.13s | 4.23s | +1.9s | 1.18 | 1 | +0.18 | 0 | 0 | +0 | 0 | 2 | 1 | 1 | +0 | 2.5% | 2.63% | -0.13% |
| pets_1 | 73.81% | 73.81% | +0% | 8.22s | 5s | +3.21s | 1.24 | 1 | +0.24 | 0 | 0 | +0 | 0 | 0 | 11 | 11 | +0 | 26.19% | 26.19% | +0% |
| poker_player | 87.5% | 82.5% | +5% | 5.67s | 4.03s | +1.64s | 1 | 1 | +0 | 0 | 0 | +0 | 0 | 3 | 5 | 4 | +1 | 12.5% | 10.81% | +1.69% |
| real_estate_properties | 50% | 75% | -25% | 13.01s | 5.62s | +7.39s | 2.75 | 1 | +1.75 | 0 | 0 | +0 | 0 | 0 | 2 | 1 | +1 | 50% | 25% | +25% |
| singer | 93.33% | 90% | +3.33% | 6.13s | 3.77s | +2.36s | 1.17 | 1 | +0.17 | 0 | 0 | +0 | 0 | 0 | 2 | 3 | -1 | 6.67% | 10% | -3.33% |
| student_transcripts_tracking | 52.56% | 52.56% | +0% | 11.03s | 5.9s | +5.13s | 1.63 | 1.01 | +0.62 | 0 | 0 | +0 | 1 | 5 | 36 | 32 | +4 | 46.75% | 43.84% | +2.92% |
| superhero | 30.23% | 21.71% | +8.53% | 14.27s | 2.41s | +11.85s | 3.2 | 1 | +2.2 | 0 | 0 | +0 | 32 | 44 | 55 | 55 | +0 | 58.51% | 66.27% | -7.75% |
| thrombosis_prediction | 12.88% | 3.07% | +9.82% | 14.24s | 4.18s | +10.06s | 2.46 | 1.17 | +1.29 | 0 | 0 | +0 | 8 | 92 | 131 | 62 | +69 | 86.18% | 92.54% | -6.35% |
| toxicology | 15.17% | 16.55% | -1.38% | 11.01s | 5.14s | +5.87s | 2.05 | 1 | +1.05 | 0 | 0 | +0 | 1 | 19 | 121 | 101 | +20 | 84.62% | 80.8% | +3.82% |
| tvshow | 82.26% | 62.9% | +19.35% | 7.84s | 5.17s | +2.66s | 1.48 | 1.03 | +0.45 | 0 | 0 | +0 | 0 | 2 | 11 | 21 | -10 | 17.74% | 35% | -17.26% |
| voter_1 | 86.67% | 86.67% | +0% | 8.56s | 4.91s | +3.65s | 1.53 | 1 | +0.53 | 0 | 0 | +0 | 0 | 0 | 2 | 2 | +0 | 13.33% | 13.33% | +0% |
| world_1 | 78.33% | 60% | +18.33% | 9.72s | 4.93s | +4.8s | 1.68 | 1 | +0.68 | 0 | 0 | +0 | 1 | 11 | 25 | 37 | -12 | 21.01% | 33.94% | -12.94% |
| wta_1 | 74.19% | 62.9% | +11.29% | 11.31s | 4.65s | +6.66s | 1.6 | 1 | +0.6 | 0 | 0 | +0 | 2 | 6 | 14 | 17 | -3 | 23.33% | 30.36% | -7.02% |
| **MODEL VERDICT** | **48.46%** | **43.15%** | **+5.31%** | **11.35s** | **5.26s** | **+6.09s** | **1.79** | **1.04** | **+0.75** | **0** | **0** | **+0** | **92** | **411** | **1040** | **916** | **+124** | **47.1%** | **46.83%** | **+0.27%** |

## Attempts Correlations

| Database | Pearson stats db_conn | Pearson p-value db_conn | Pearson stats text | Pearson p-value text | Pearson delta | Spearman stats db_conn | Spearman p-value db_conn | Spearman stats text | Spearman p-value text | Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 0.1155 | 0.6702 (false) | NR | NR | NR | 0.1234 | 0.6488 (false) | NR | NR | NR |
| california_schools | -0.3453 | 0.0009 (true) | -0.1553 | 0.1462 (false) | -0.1900 | -0.3924 | 0.0001 (true) | -0.1486 | 0.1647 (false) | -0.2438 |
| car_1 | -0.3993 | 8.05e-05 (true) | -0.1048 | 0.3200 (false) | -0.2945 | -0.4256 | 2.34e-05 (true) | -0.1048 | 0.3200 (false) | -0.3208 |
| card_games | 0.0745 | 0.3058 (false) | -0.0197 | 0.7866 (false) | +0.0942 | 0.0183 | 0.8017 (false) | 0.0163 | 0.8224 (false) | +0.0019 |
| codebase_community | -0.3540 | 7.15e-07 (true) | -0.0565 | 0.4440 (false) | -0.2976 | -0.3439 | 1.54e-06 (true) | -0.0565 | 0.4440 (false) | -0.2874 |
| concert_singer | -0.3726 | 0.0117 (true) | NR | NR | NR | -0.2298 | 0.1290 (false) | NR | NR | NR |
| course_teach | 0.0496 | 0.7945 (false) | NR | NR | NR | 0.0496 | 0.7945 (false) | NR | NR | NR |
| cre_Doc_Template_Mgt | -0.3981 | 0.0002 (true) | NR | NR | NR | -0.3569 | 0.0009 (true) | NR | NR | NR |
| debit_card_specializing | -0.2046 | 0.1049 (false) | NR | NR | NR | -0.1880 | 0.1368 (false) | NR | NR | NR |
| dog_kennels | -0.4463 | 2.63e-05 (true) | 0.0822 | 0.4629 (false) | -0.5285 | -0.4258 | 6.67e-05 (true) | 0.0822 | 0.4629 (false) | -0.5079 |
| employee_hire_evaluation | 0.1061 | 0.5262 (false) | NR | NR | NR | 0.1117 | 0.5043 (false) | NR | NR | NR |
| european_football_2 | -0.0891 | 0.3153 (false) | -0.1170 | 0.1867 (false) | +0.0279 | 0.0102 | 0.9091 (false) | -0.1147 | 0.1957 (false) | +0.1248 |
| financial | -0.3887 | 3.83e-05 (true) | -0.0540 | 0.5828 (false) | -0.3347 | -0.4136 | 1.05e-05 (true) | -0.0551 | 0.5750 (false) | -0.3585 |
| flight_2 | -0.3572 | 0.0011 (true) | NR | NR | NR | -0.3465 | 0.0016 (true) | NR | NR | NR |
| formula_1 | -0.3242 | 1.28e-05 (true) | NR | NR | NR | -0.3297 | 8.88e-06 (true) | NR | NR | NR |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| network_1 | -0.4176 | 0.0014 (true) | NR | NR | NR | -0.4012 | 0.0022 (true) | NR | NR | NR |
| orchestra | -0.6786 | 1.49e-06 (true) | NR | NR | NR | -0.5772 | 9.67e-05 (true) | NR | NR | NR |
| pets_1 | -0.1563 | 0.3230 (false) | NR | NR | NR | -0.1034 | 0.5146 (false) | NR | NR | NR |
| poker_player | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| real_estate_properties | -0.7035 | 0.2965 (false) | NR | NR | NR | -0.9428 | 0.0572 (false) | NR | NR | NR |
| singer | -0.4269 | 0.0186 (true) | NR | NR | NR | -0.3707 | 0.0437 (true) | NR | NR | NR |
| student_transcripts_tracking | -0.4086 | 0.0002 (true) | -0.1200 | 0.2955 (false) | -0.2886 | -0.3880 | 0.0004 (true) | -0.1200 | 0.2955 (false) | -0.2680 |
| superhero | -0.5256 | 1.59e-10 (true) | NR | NR | NR | -0.5333 | 7.66e-11 (true) | NR | NR | NR |
| thrombosis_prediction | -0.0530 | 0.5014 (false) | -0.0476 | 0.5463 (false) | -0.0054 | -0.0204 | 0.7958 (false) | -0.0566 | 0.4733 (false) | +0.0361 |
| toxicology | -0.2810 | 0.0006 (true) | NR | NR | NR | -0.3200 | 8.74e-05 (true) | NR | NR | NR |
| tvshow | -0.4088 | 0.0010 (true) | -0.1667 | 0.1953 (false) | -0.2421 | -0.3845 | 0.0020 (true) | -0.1667 | 0.1953 (false) | -0.2178 |
| voter_1 | -0.2549 | 0.3592 (false) | NR | NR | NR | -0.1815 | 0.5174 (false) | NR | NR | NR |
| world_1 | -0.1257 | 0.1714 (false) | NR | NR | NR | -0.0381 | 0.6793 (false) | NR | NR | NR |
| wta_1 | -0.3840 | 0.0021 (true) | NR | NR | NR | -0.1952 | 0.1284 (false) | NR | NR | NR |
| **MODEL VERDICT** | **-0.3601** | **1.06e-74 (true)** | **-0.0940** | **3.76e-06 (true)** | **-0.2661** | **-0.3388** | **8.16e-66 (true)** | **-0.1004** | **7.90e-07 (true)** | **-0.2385** |

## Complexity Correlations

| Database | Pearson stats db_conn | Pearson p-value db_conn | Pearson stats text | Pearson p-value text | Pearson delta | Spearman stats db_conn | Spearman p-value db_conn | Spearman stats text | Spearman p-value text | Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.3386 | 0.1996 (false) | -0.7298 | 0.0013 (true) | +0.3912 | -0.3756 | 0.1517 (false) | -0.7695 | 0.0005 (true) | +0.3939 |
| california_schools | -0.2073 | 0.0512 (false) | -0.3186 | 0.0023 (true) | +0.1112 | -0.1956 | 0.0663 (false) | -0.3347 | 0.0013 (true) | +0.1391 |
| car_1 | 0.0702 | 0.5058 (false) | -0.1847 | 0.0780 (false) | +0.2549 | 0.0665 | 0.5290 (false) | -0.1564 | 0.1366 (false) | +0.2228 |
| card_games | -0.2992 | 2.61e-05 (true) | -0.2560 | 0.0004 (true) | -0.0432 | -0.3337 | 2.40e-06 (true) | -0.2838 | 6.93e-05 (true) | -0.0499 |
| codebase_community | -0.2840 | 8.55e-05 (true) | -0.2333 | 0.0013 (true) | -0.0507 | -0.2705 | 0.0002 (true) | -0.2221 | 0.0023 (true) | -0.0483 |
| concert_singer | -0.3108 | 0.0377 (true) | -0.3418 | 0.0216 (true) | +0.0310 | -0.3033 | 0.0428 (true) | -0.3360 | 0.0240 (true) | +0.0327 |
| course_teach | -0.0824 | 0.6649 (false) | -0.1986 | 0.2929 (false) | +0.1161 | -0.0893 | 0.6389 (false) | -0.2150 | 0.2538 (false) | +0.1258 |
| cre_Doc_Template_Mgt | -0.1713 | 0.1192 (false) | -0.2083 | 0.0573 (false) | +0.0369 | -0.1631 | 0.1383 (false) | -0.1922 | 0.0798 (false) | +0.0291 |
| debit_card_specializing | -0.2192 | 0.0819 (false) | -0.1701 | 0.1790 (false) | -0.0491 | -0.3122 | 0.0120 (true) | -0.2669 | 0.0330 (true) | -0.0453 |
| dog_kennels | -0.3857 | 0.0003 (true) | -0.3719 | 0.0006 (true) | -0.0138 | -0.3765 | 0.0005 (true) | -0.3518 | 0.0012 (true) | -0.0247 |
| employee_hire_evaluation | 0.1783 | 0.2843 (false) | 0.2875 | 0.0800 (false) | -0.1093 | 0.1751 | 0.2931 (false) | 0.3283 | 0.0442 (true) | -0.1532 |
| european_football_2 | -0.1836 | 0.0372 (true) | -0.1064 | 0.2301 (false) | -0.0772 | -0.2464 | 0.0049 (true) | -0.1724 | 0.0507 (false) | -0.0740 |
| financial | -0.0168 | 0.8639 (false) | -0.0338 | 0.7310 (false) | +0.0169 | 0.0074 | 0.9400 (false) | -0.0553 | 0.5733 (false) | +0.0627 |
| flight_2 | -0.2360 | 0.0351 (true) | -0.3646 | 0.0009 (true) | +0.1286 | -0.2184 | 0.0516 (false) | -0.3336 | 0.0025 (true) | +0.1151 |
| formula_1 | -0.1637 | 0.0309 (true) | -0.0730 | 0.3385 (false) | -0.0907 | -0.1187 | 0.1188 (false) | -0.0626 | 0.4121 (false) | -0.0561 |
| museum_visit | NR | NR | -0.1706 | 0.4985 (false) | NR | NR | NR | -0.2139 | 0.3940 (false) | NR |
| network_1 | -0.1674 | 0.2175 (false) | 0.0421 | 0.7582 (false) | -0.2095 | -0.2287 | 0.0900 (false) | -0.0246 | 0.8572 (false) | -0.2041 |
| orchestra | 0.1708 | 0.2919 (false) | 0.1480 | 0.3621 (false) | +0.0228 | 0.2137 | 0.1854 (false) | 0.1689 | 0.2974 (false) | +0.0448 |
| pets_1 | -0.1747 | 0.2685 (false) | 0.0108 | 0.9459 (false) | -0.1855 | -0.2175 | 0.1665 (false) | -0.0544 | 0.7324 (false) | -0.1631 |
| poker_player | 0.2778 | 0.0826 (false) | 0.1535 | 0.3443 (false) | +0.1243 | 0.3185 | 0.0452 (true) | 0.1478 | 0.3627 (false) | +0.1706 |
| real_estate_properties | -0.2294 | 0.7706 (false) | 0.6623 | 0.3377 (false) | -0.8917 | 0.0000 | 1.0000 (false) | 0.8165 | 0.1835 (false) | -0.8165 |
| singer | 0.1984 | 0.2932 (false) | 0.2241 | 0.2338 (false) | -0.0257 | 0.2065 | 0.2737 (false) | 0.2113 | 0.2624 (false) | -0.0048 |
| student_transcripts_tracking | -0.2232 | 0.0495 (true) | -0.1425 | 0.2132 (false) | -0.0807 | -0.2040 | 0.0732 (false) | -0.1285 | 0.2621 (false) | -0.0755 |
| superhero | -0.1874 | 0.0334 (true) | -0.1633 | 0.0644 (false) | -0.0241 | -0.2293 | 0.0090 (true) | -0.1621 | 0.0664 (false) | -0.0672 |
| thrombosis_prediction | -0.1058 | 0.1788 (false) | -0.0499 | 0.5266 (false) | -0.0559 | -0.1030 | 0.1907 (false) | -0.0479 | 0.5436 (false) | -0.0551 |
| toxicology | -0.1614 | 0.0524 (false) | -0.1681 | 0.0432 (true) | +0.0067 | -0.1799 | 0.0304 (true) | -0.1985 | 0.0167 (true) | +0.0186 |
| tvshow | -0.3835 | 0.0021 (true) | -0.1806 | 0.1602 (false) | -0.2029 | -0.3731 | 0.0028 (true) | -0.1915 | 0.1359 (false) | -0.1816 |
| voter_1 | -0.3434 | 0.2102 (false) | -0.1427 | 0.6119 (false) | -0.2007 | -0.3036 | 0.2714 (false) | -0.1868 | 0.5050 (false) | -0.1168 |
| world_1 | -0.2760 | 0.0023 (true) | -0.2783 | 0.0021 (true) | +0.0023 | -0.3023 | 0.0008 (true) | -0.2842 | 0.0017 (true) | -0.0181 |
| wta_1 | -0.1245 | 0.3349 (false) | -0.3744 | 0.0027 (true) | +0.2498 | -0.1129 | 0.3825 (false) | -0.3665 | 0.0034 (true) | +0.2536 |
| **MODEL VERDICT** | **-0.2035** | **5.96e-24 (true)** | **-0.1959** | **2.80e-22 (true)** | **-0.0076** | **-0.2135** | **3.07e-26 (true)** | **-0.2080** | **5.75e-25 (true)** | **-0.0055** |

## Avg columns correlations

| Database | Pearson stats db_conn | Pearson p-value db_conn | Pearson stats text | Pearson p-value text | Pearson delta | Spearman stats db_conn | Spearman p-value db_conn | Spearman stats text | Spearman p-value text | Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| california_schools | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| car_1 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| card_games | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| codebase_community | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| concert_singer | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| course_teach | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| cre_Doc_Template_Mgt | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| debit_card_specializing | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| dog_kennels | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| employee_hire_evaluation | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| european_football_2 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| financial | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| flight_2 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| formula_1 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| network_1 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| orchestra | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| pets_1 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| poker_player | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| real_estate_properties | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| singer | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| student_transcripts_tracking | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| superhero | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| thrombosis_prediction | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| toxicology | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| tvshow | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| voter_1 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| world_1 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| wta_1 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| **MODEL VERDICT** | **-0.2776** | **6.72e-44 (true)** | **-0.2240** | **8.52e-29 (true)** | **-0.0536** | **-0.2124** | **5.66e-26 (true)** | **-0.2057** | **1.98e-24 (true)** | **-0.0067** |

