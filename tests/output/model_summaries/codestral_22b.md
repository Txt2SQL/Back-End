# Model Performance Summary: `codestral:22b`

**Base directory:** `C:\Users\pietr\Desktop\UniTn\Tesi\Progetto Text2SQL\Back-End\tests\output\generations`

Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.

## Status

| Database | Success db_conn | Success text | Success delta | Avg time db_conn | Avg time text | Avg time delta | Avg attempts db_conn | Avg attempts text | Avg attempts delta | Syntax db_conn | Syntax text | Syntax delta | Runtime db_conn | Runtime text | Incorrect db_conn | Incorrect text | Incorrect delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 93.75% | 68.75% | +25% | 7.84s | 3.54s | +4.3s | 1.25 | 1 | +0.25 | 0 | 0 | +0 | 0 | 2 | 1 | 3 | -2 |
| california_schools | 24.72% | 0% | +24.72% | 12.61s | 9.1s | +3.51s | 1.93 | 1 | +0.93 | 0 | 0 | +0 | 0 | 0 | 37 | 0 | +37 |
| car_1 | 52.17% | 50% | +2.17% | 11.15s | 5.77s | +5.38s | 1.7 | 1.04 | +0.65 | 0 | 0 | +0 | 2 | 6 | 41 | 39 | +2 |
| card_games | 0% | 0% | +0% | 9.4s | 9.04s | +0.36s | 1 | 1 | +0 | 0 | 0 | +0 | 0 | 0 | 0 | 0 | +0 |
| codebase_community | 0% | 0% | +0% | 9.27s | 9.18s | +0.09s | 1 | 1 | +0 | 0 | 0 | +0 | 0 | 0 | 0 | 0 | +0 |
| concert_singer | 82.22% | 86.67% | -4.44% | 7.15s | 4.27s | +2.89s | 1.2 | 1 | +0.2 | 0 | 0 | +0 | 1 | 1 | 7 | 5 | +2 |
| course_teach | 96.67% | 83.33% | +13.33% | 6.03s | 3.99s | +2.04s | 1.07 | 1 | +0.07 | 0 | 0 | +0 | 0 | 0 | 1 | 5 | -4 |
| cre_Doc_Template_Mgt | 89.29% | 83.33% | +5.95% | 7.02s | 4.29s | +2.73s | 1.29 | 1 | +0.29 | 0 | 0 | +0 | 0 | 4 | 9 | 10 | -1 |
| debit_card_specializing | 25% | 14.06% | +10.94% | 24.77s | 11.09s | +13.68s | 2.2 | 1 | +1.2 | 0 | 0 | +0 | 2 | 19 | 46 | 36 | +10 |
| dog_kennels | 63.41% | 64.63% | -1.22% | 10.03s | 5.11s | +4.93s | 1.54 | 1.01 | +0.52 | 0 | 0 | +0 | 2 | 9 | 28 | 20 | +8 |
| employee_hire_evaluation | 94.74% | 94.74% | +0% | 6.58s | 4.3s | +2.28s | 1.21 | 1 | +0.21 | 0 | 0 | +0 | 0 | 0 | 2 | 2 | +0 |
| european_football_2 | 17.83% | 37.21% | -19.38% | 20.42s | 9.74s | +10.68s | 1.4 | 1.1 | +0.29 | 0 | 0 | +0 | 1 | 16 | 23 | 55 | -32 |
| financial | 16.98% | 0% | +16.98% | 25.06s | 9.06s | +16.01s | 3.08 | 1 | +2.08 | 0 | 0 | +0 | 22 | 0 | 65 | 0 | +65 |
| flight_2 | 88.75% | 85% | +3.75% | 7.09s | 4.08s | +3.01s | 1.27 | 1 | +0.27 | 0 | 0 | +0 | 0 | 1 | 9 | 11 | -2 |
| formula_1 | 0% | 19.54% | -19.54% | 9.4s | 7.09s | +2.31s | 1 | 1 | +0 | 0 | 0 | +0 | 0 | 30 | 0 | 108 | -108 |
| museum_visit | 100% | 94.44% | +5.56% | 6.3s | 4.22s | +2.08s | 1.06 | 1 | +0.06 | 0 | 0 | +0 | 0 | 0 | 0 | 1 | -1 |
| network_1 | 80.36% | 78.57% | +1.79% | 8.02s | 4.54s | +3.48s | 1.59 | 1 | +0.59 | 0 | 0 | +0 | 0 | 0 | 11 | 12 | -1 |
| orchestra | 97.5% | 92.5% | +5% | 6.13s | 4.23s | +1.9s | 1.18 | 1 | +0.18 | 0 | 0 | +0 | 0 | 2 | 1 | 1 | +0 |
| pets_1 | 73.81% | 73.81% | +0% | 8.22s | 5s | +3.21s | 1.24 | 1 | +0.24 | 0 | 0 | +0 | 0 | 0 | 11 | 11 | +0 |
| poker_player | 87.5% | 82.5% | +5% | 5.67s | 4.03s | +1.64s | 1 | 1 | +0 | 0 | 0 | +0 | 0 | 3 | 5 | 4 | +1 |
| real_estate_properties | 50% | 75% | -25% | 13.01s | 5.62s | +7.39s | 2.75 | 1 | +1.75 | 0 | 0 | +0 | 0 | 0 | 2 | 1 | +1 |
| singer | 93.33% | 90% | +3.33% | 6.13s | 3.77s | +2.36s | 1.17 | 1 | +0.17 | 0 | 0 | +0 | 0 | 0 | 2 | 3 | -1 |
| student_transcripts_tracking | 52.56% | 52.56% | +0% | 11.03s | 5.9s | +5.13s | 1.63 | 1.01 | +0.62 | 0 | 0 | +0 | 1 | 5 | 36 | 32 | +4 |
| superhero | 0% | 1.55% | -1.55% | 9.71s | 8.32s | +1.39s | 1 | 1.02 | -0.02 | 0 | 0 | +0 | 0 | 10 | 0 | 5 | -5 |
| toxicology | 0% | 0% | +0% | 9.32s | 9.01s | +0.3s | 1 | 1 | +0 | 0 | 0 | +0 | 0 | 0 | 0 | 0 | +0 |
| tvshow | 82.26% | 62.9% | +19.35% | 7.84s | 5.17s | +2.66s | 1.48 | 1.03 | +0.45 | 0 | 0 | +0 | 0 | 2 | 11 | 21 | -10 |
| voter_1 | 86.67% | 86.67% | +0% | 8.56s | 4.91s | +3.65s | 1.53 | 1 | +0.53 | 0 | 0 | +0 | 0 | 0 | 2 | 2 | +0 |
| **MODEL VERDICT** | **36.08%** | **35.16%** | **+0.92%** | **11.01s** | **7.17s** | **+3.84s** | **1.37** | **1.01** | **+0.36** | **0** | **0** | **+0** | **31** | **110** | **350** | **387** | **-37** |

## Correlations

| Database | Attempts Pearson stats db_conn | Attempts Pearson p-value db_conn | Attempts Pearson stats text | Attempts Pearson p-value text | Attempts Pearson delta | Attempts Spearman stats db_conn | Attempts Spearman p-value db_conn | Attempts Spearman stats text | Attempts Spearman p-value text | Attempts Spearman delta | Complexity Pearson stats db_conn | Complexity Pearson p-value db_conn | Complexity Pearson stats text | Complexity Pearson p-value text | Complexity Pearson delta | Complexity Spearman stats db_conn | Complexity Spearman p-value db_conn | Complexity Spearman stats text | Complexity Spearman p-value text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 0.1155 | 0.6702 (false) | NR | NR | NR | 0.1234 | 0.6488 (false) | NR | NR | NR | -0.3386 | 0.1996 (false) | -0.7298 | 0.0013 (true) | +0.3912 | -0.3756 | 0.1517 (false) | -0.7695 | 0.0005 (true) | +0.3939 |
| california_schools | -0.0879 | 0.4130 (false) | NR | NR | NR | -0.0284 | 0.7919 (false) | NR | NR | NR | -0.0968 | 0.3670 (false) | NR | NR | NR | -0.0758 | 0.4799 (false) | NR | NR | NR |
| car_1 | -0.3993 | 8.05e-05 (true) | -0.1048 | 0.3200 (false) | -0.2945 | -0.4256 | 2.34e-05 (true) | -0.1048 | 0.3200 (false) | -0.3208 | 0.0702 | 0.5058 (false) | -0.1847 | 0.0780 (false) | +0.2549 | 0.0665 | 0.5290 (false) | -0.1564 | 0.1366 (false) | +0.2228 |
| card_games | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| codebase_community | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| concert_singer | -0.3726 | 0.0117 (true) | NR | NR | NR | -0.2298 | 0.1290 (false) | NR | NR | NR | -0.3108 | 0.0377 (true) | -0.3418 | 0.0216 (true) | +0.0310 | -0.3033 | 0.0428 (true) | -0.3360 | 0.0240 (true) | +0.0327 |
| course_teach | 0.0496 | 0.7945 (false) | NR | NR | NR | 0.0496 | 0.7945 (false) | NR | NR | NR | -0.0824 | 0.6649 (false) | -0.1986 | 0.2929 (false) | +0.1161 | -0.0893 | 0.6389 (false) | -0.2150 | 0.2538 (false) | +0.1258 |
| cre_Doc_Template_Mgt | -0.3981 | 0.0002 (true) | NR | NR | NR | -0.3569 | 0.0009 (true) | NR | NR | NR | -0.1713 | 0.1192 (false) | -0.2083 | 0.0573 (false) | +0.0369 | -0.1631 | 0.1383 (false) | -0.1922 | 0.0798 (false) | +0.0291 |
| debit_card_specializing | -0.2046 | 0.1049 (false) | NR | NR | NR | -0.1880 | 0.1368 (false) | NR | NR | NR | -0.2192 | 0.0819 (false) | -0.1701 | 0.1790 (false) | -0.0491 | -0.3122 | 0.0120 (true) | -0.2669 | 0.0330 (true) | -0.0453 |
| dog_kennels | -0.4463 | 2.63e-05 (true) | 0.0822 | 0.4629 (false) | -0.5285 | -0.4258 | 6.67e-05 (true) | 0.0822 | 0.4629 (false) | -0.5079 | -0.3857 | 0.0003 (true) | -0.3719 | 0.0006 (true) | -0.0138 | -0.3765 | 0.0005 (true) | -0.3518 | 0.0012 (true) | -0.0247 |
| employee_hire_evaluation | 0.1061 | 0.5262 (false) | NR | NR | NR | 0.1117 | 0.5043 (false) | NR | NR | NR | 0.1783 | 0.2843 (false) | 0.2875 | 0.0800 (false) | -0.1093 | 0.1751 | 0.2931 (false) | 0.3283 | 0.0442 (true) | -0.1532 |
| european_football_2 | -0.0891 | 0.3153 (false) | -0.1170 | 0.1867 (false) | +0.0279 | 0.0102 | 0.9091 (false) | -0.1147 | 0.1957 (false) | +0.1248 | -0.1836 | 0.0372 (true) | -0.1064 | 0.2301 (false) | -0.0772 | -0.2464 | 0.0049 (true) | -0.1724 | 0.0507 (false) | -0.0740 |
| financial | -0.3887 | 3.83e-05 (true) | NR | NR | NR | -0.4136 | 1.05e-05 (true) | NR | NR | NR | -0.0168 | 0.8639 (false) | NR | NR | NR | 0.0074 | 0.9400 (false) | NR | NR | NR |
| flight_2 | -0.3572 | 0.0011 (true) | NR | NR | NR | -0.3465 | 0.0016 (true) | NR | NR | NR | -0.2360 | 0.0351 (true) | -0.3646 | 0.0009 (true) | +0.1286 | -0.2184 | 0.0516 (false) | -0.3336 | 0.0025 (true) | +0.1151 |
| formula_1 | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | -0.0730 | 0.3385 (false) | NR | NR | NR | -0.0626 | 0.4121 (false) | NR |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | -0.1706 | 0.4985 (false) | NR | NR | NR | -0.2139 | 0.3940 (false) | NR |
| network_1 | -0.4176 | 0.0014 (true) | NR | NR | NR | -0.4012 | 0.0022 (true) | NR | NR | NR | -0.1674 | 0.2175 (false) | 0.0421 | 0.7582 (false) | -0.2095 | -0.2287 | 0.0900 (false) | -0.0246 | 0.8572 (false) | -0.2041 |
| orchestra | -0.6786 | 1.49e-06 (true) | NR | NR | NR | -0.5772 | 9.67e-05 (true) | NR | NR | NR | 0.1708 | 0.2919 (false) | 0.1480 | 0.3621 (false) | +0.0228 | 0.2137 | 0.1854 (false) | 0.1689 | 0.2974 (false) | +0.0448 |
| pets_1 | -0.1563 | 0.3230 (false) | NR | NR | NR | -0.1034 | 0.5146 (false) | NR | NR | NR | -0.1747 | 0.2685 (false) | 0.0108 | 0.9459 (false) | -0.1855 | -0.2175 | 0.1665 (false) | -0.0544 | 0.7324 (false) | -0.1631 |
| poker_player | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | 0.2778 | 0.0826 (false) | 0.1535 | 0.3443 (false) | +0.1243 | 0.3185 | 0.0452 (true) | 0.1478 | 0.3627 (false) | +0.1706 |
| real_estate_properties | -0.7035 | 0.2965 (false) | NR | NR | NR | -0.9428 | 0.0572 (false) | NR | NR | NR | -0.2294 | 0.7706 (false) | 0.6623 | 0.3377 (false) | -0.8917 | 0.0000 | 1.0000 (false) | 0.8165 | 0.1835 (false) | -0.8165 |
| singer | -0.4269 | 0.0186 (true) | NR | NR | NR | -0.3707 | 0.0437 (true) | NR | NR | NR | 0.1984 | 0.2932 (false) | 0.2241 | 0.2338 (false) | -0.0257 | 0.2065 | 0.2737 (false) | 0.2113 | 0.2624 (false) | -0.0048 |
| student_transcripts_tracking | -0.4086 | 0.0002 (true) | -0.1200 | 0.2955 (false) | -0.2886 | -0.3880 | 0.0004 (true) | -0.1200 | 0.2955 (false) | -0.2680 | -0.2232 | 0.0495 (true) | -0.1425 | 0.2132 (false) | -0.0807 | -0.2040 | 0.0732 (false) | -0.1285 | 0.2621 (false) | -0.0755 |
| superhero | NR | NR | -0.0111 | 0.9007 (false) | NR | NR | NR | -0.0111 | 0.9007 (false) | NR | NR | NR | -0.1081 | 0.2228 (false) | NR | NR | NR | -0.1291 | 0.1447 (false) | NR |
| toxicology | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| tvshow | -0.4088 | 0.0010 (true) | -0.1667 | 0.1953 (false) | -0.2421 | -0.3845 | 0.0020 (true) | -0.1667 | 0.1953 (false) | -0.2178 | -0.3835 | 0.0021 (true) | -0.1806 | 0.1602 (false) | -0.2029 | -0.3731 | 0.0028 (true) | -0.1915 | 0.1359 (false) | -0.1816 |
| voter_1 | -0.2549 | 0.3592 (false) | NR | NR | NR | -0.1815 | 0.5174 (false) | NR | NR | NR | -0.3434 | 0.2102 (false) | -0.1427 | 0.6119 (false) | -0.2007 | -0.3036 | 0.2714 (false) | -0.1868 | 0.5050 (false) | -0.1168 |
| **MODEL VERDICT** | **-0.1110** | **4.27e-07 (true)** | **-0.0354** | **0.1077 (false)** | **-0.0756** | **-0.0183** | **0.4054 (false)** | **-0.0297** | **0.1777 (false)** | **+0.0114** | **-0.1229** | **2.09e-08 (true)** | **-0.1291** | **3.87e-09 (true)** | **+0.0062** | **-0.1287** | **4.33e-09 (true)** | **-0.1370** | **4.05e-10 (true)** | **+0.0083** |

