# Model Performance Summary: `Qwen3-coder-next`

**Base directory:** `C:\Users\pietr\Desktop\UniTn\Tesi\Progetto Text2SQL\Back-End\tests\output\generations`

Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.

## Status

| Database | Success db_conn | Success text | Success delta | Avg time db_conn | Avg time text | Avg time delta | Avg attempts db_conn | Avg attempts text | Avg attempts delta | Syntax db_conn | Syntax text | Syntax delta | Runtime db_conn | Runtime text | Incorrect db_conn | Incorrect text | Incorrect delta | Incorrect perc db_conn | Incorrect perc text | Incorrect perc delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 93.75% | 87.5% | +6.25% | 8.07s | 5.6s | +2.48s | 1.38 | 1 | +0.38 | 0 | 0 | +0 | 0 | 0 | 1 | 2 | -1 | 6.25% | 12.5% | -6.25% |
| california_schools | 33.71% | 24.72% | +8.99% | 7.84s | 7.16s | +0.68s | 1.78 | 2.11 | -0.34 | 0 | 0 | +0 | 0 | 11 | 50 | 26 | +24 | 62.5% | 54.17% | +8.33% |
| car_1 | 56.52% | 59.78% | -3.26% | 10.35s | 5.62s | +4.73s | 1.43 | 1 | +0.43 | 0 | 0 | +0 | 0 | 3 | 40 | 34 | +6 | 43.48% | 38.2% | +5.28% |
| card_games | 37.7% | 31.94% | +5.76% | 14.24s | 8.54s | +5.71s | 1.71 | 1.03 | +0.68 | 0 | 0 | +0 | 0 | 9 | 117 | 119 | -2 | 61.9% | 66.11% | -4.21% |
| codebase_community | 52.15% | 47.31% | +4.84% | 9.8s | 6.53s | +3.27s | 1.6 | 1 | +0.6 | 0 | 0 | +0 | 0 | 22 | 81 | 69 | +12 | 45.51% | 43.95% | +1.56% |
| concert_singer | 80% | 86.67% | -6.67% | 7.19s | 4.88s | +2.31s | 1.16 | 1 | +0.16 | 0 | 0 | +0 | 1 | 0 | 8 | 6 | +2 | 18.18% | 13.33% | +4.85% |
| course_teach | 93.33% | 86.67% | +6.67% | 6.67s | 3.88s | +2.79s | 1.03 | 1 | +0.03 | 0 | 0 | +0 | 0 | 0 | 2 | 4 | -2 | 6.67% | 13.33% | -6.67% |
| cre_Doc_Template_Mgt | 91.67% | 77.38% | +14.29% | 6.62s | 3.77s | +2.85s | 1.23 | 1 | +0.23 | 0 | 0 | +0 | 0 | 8 | 7 | 11 | -4 | 8.33% | 14.47% | -6.14% |
| debit_card_specializing | 31.25% | 34.38% | -3.12% | 20.25s | 11.93s | +8.32s | 1.59 | 1 | +0.59 | 0 | 0 | +0 | 0 | 4 | 44 | 38 | +6 | 68.75% | 63.33% | +5.42% |
| dog_kennels | 75.61% | 64.63% | +10.98% | 9.84s | 4.71s | +5.13s | 1.4 | 1 | +0.4 | 0 | 0 | +0 | 2 | 11 | 16 | 18 | -2 | 20.51% | 25.35% | -4.84% |
| employee_hire_evaluation | 97.37% | 97.37% | +0% | 5.65s | 3.66s | +1.99s | 1 | 1 | +0 | 0 | 0 | +0 | 0 | 0 | 1 | 1 | +0 | 2.63% | 2.63% | +0% |
| european_football_2 | 55.81% | 48.06% | +7.75% | 22.01s | 8.29s | +13.72s | 1.53 | 1 | +0.53 | 0 | 0 | +0 | 0 | 16 | 57 | 51 | +6 | 44.19% | 45.13% | -0.95% |
| financial | 19.81% | 18.87% | +0.94% | 25.1s | 5.71s | +19.39s | 2.87 | 1.11 | +1.75 | 0 | 0 | +0 | 13 | 51 | 68 | 32 | +36 | 76.4% | 61.54% | +14.87% |
| flight_2 | 87.5% | 83.75% | +3.75% | 6.27s | 3.88s | +2.39s | 1.21 | 1 | +0.21 | 0 | 0 | +0 | 0 | 3 | 10 | 10 | +0 | 12.5% | 12.99% | -0.49% |
| formula_1 | 43.68% | 29.31% | +14.37% | 12.89s | 5.35s | +7.54s | 2.03 | 1 | +1.03 | 0 | 0 | +0 | 4 | 48 | 93 | 75 | +18 | 55.03% | 59.52% | -4.49% |
| museum_visit | 100% | 100% | +0% | 6.24s | 3.75s | +2.49s | 1.06 | 1 | +0.06 | 0 | 0 | +0 | 0 | 0 | 0 | 0 | +0 | 0% | 0% | +0% |
| network_1 | 83.93% | 82.14% | +1.79% | 7.66s | 3.94s | +3.72s | 1.5 | 1 | +0.5 | 0 | 0 | +0 | 0 | 3 | 9 | 7 | +2 | 16.07% | 13.21% | +2.86% |
| orchestra | 95% | 87.5% | +7.5% | 5.49s | 4.18s | +1.3s | 1.02 | 1 | +0.02 | 0 | 0 | +0 | 0 | 3 | 2 | 2 | +0 | 5% | 5.41% | -0.41% |
| pets_1 | 92.86% | 90.48% | +2.38% | 6.76s | 4.54s | +2.22s | 1.1 | 1 | +0.1 | 0 | 0 | +0 | 0 | 2 | 3 | 2 | +1 | 7.14% | 5% | +2.14% |
| poker_player | 100% | 90% | +10% | 5.17s | 3.69s | +1.47s | 1.05 | 1 | +0.05 | 0 | 0 | +0 | 0 | 1 | 0 | 3 | -3 | 0% | 7.69% | -7.69% |
| real_estate_properties | 50% | 75% | -25% | 11.13s | 4.17s | +6.96s | 2.5 | 1 | +1.5 | 0 | 0 | +0 | 0 | 1 | 2 | 0 | +2 | 50% | 0% | +50% |
| singer | 100% | 93.33% | +6.67% | 5.42s | 3.58s | +1.85s | 1.03 | 1 | +0.03 | 0 | 0 | +0 | 0 | 0 | 0 | 2 | -2 | 0% | 6.67% | -6.67% |
| student_transcripts_tracking | 66.67% | 61.54% | +5.13% | 11.52s | 5.3s | +6.22s | 1.63 | 1 | +0.63 | 0 | 0 | +0 | 2 | 7 | 23 | 23 | +0 | 30.67% | 32.39% | -1.73% |
| superhero | 33.33% | 31.78% | +1.55% | 10.91s | 4.14s | +6.77s | 2.78 | 1 | +1.78 | 0 | 0 | +0 | 28 | 51 | 53 | 35 | +18 | 55.21% | 46.05% | +9.16% |
| thrombosis_prediction | 14.72% | 6.75% | +7.98% | 8.52s | 3.18s | +5.34s | 1.9 | 1.84 | +0.06 | 0 | 0 | +0 | 0 | 53 | 137 | 69 | +68 | 85.09% | 86.25% | -1.16% |
| toxicology | 19.31% | 20% | -0.69% | 11.83s | 3.57s | +8.26s | 1.66 | 1 | +0.66 | 0 | 0 | +0 | 2 | 6 | 114 | 109 | +5 | 80.28% | 78.99% | +1.3% |
| tvshow | 85.48% | 77.42% | +8.06% | 7.8s | 4.53s | +3.28s | 1.74 | 1 | +0.74 | 0 | 0 | +0 | 0 | 5 | 9 | 9 | +0 | 14.52% | 15.79% | -1.27% |
| voter_1 | 93.33% | 66.67% | +26.67% | 6.3s | 4.08s | +2.22s | 1.27 | 1 | +0.27 | 0 | 0 | +0 | 0 | 4 | 1 | 1 | +0 | 6.67% | 9.09% | -2.42% |
| world_1 | 85% | 75.83% | +9.17% | 7.85s | 3.75s | +4.1s | 1.57 | 1 | +0.57 | 0 | 0 | +0 | 0 | 16 | 18 | 13 | +5 | 15% | 12.5% | +2.5% |
| wta_1 | 79.03% | 72.58% | +6.45% | 8.28s | 4.13s | +4.15s | 1.55 | 1 | +0.55 | 0 | 0 | +0 | 3 | 8 | 10 | 9 | +1 | 16.95% | 16.67% | +0.28% |
| **MODEL VERDICT** | **55.77%** | **50.17%** | **+5.6%** | **11.15s** | **5.35s** | **+5.8s** | **1.68** | **1.1** | **+0.58** | **0** | **0** | **+0** | **55** | **346** | **976** | **780** | **+196** | **42.07%** | **39.22%** | **+2.85%** |

## Attempts Correlations

| Database | Pearson stats db_conn | Pearson p-value db_conn | Pearson stats text | Pearson p-value text | Pearson delta | Spearman stats db_conn | Spearman p-value db_conn | Spearman stats text | Spearman p-value text | Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 0.1615 | 0.5501 (false) | NR | NR | NR | 0.1721 | 0.5238 (false) | NR | NR | NR |
| california_schools | -0.2070 | 0.0516 (false) | -0.3640 | 0.0005 (true) | +0.1570 | -0.1788 | 0.0937 (false) | -0.3750 | 0.0003 (true) | +0.1962 |
| car_1 | -0.4013 | 7.35e-05 (true) | NR | NR | NR | -0.3646 | 0.0004 (true) | NR | NR | NR |
| card_games | -0.1751 | 0.0154 (true) | -0.0420 | 0.5642 (false) | -0.1331 | -0.1388 | 0.0556 (false) | -0.0420 | 0.5642 (false) | -0.0968 |
| codebase_community | -0.3602 | 4.41e-07 (true) | NR | NR | NR | -0.3246 | 6.19e-06 (true) | NR | NR | NR |
| concert_singer | -0.3950 | 0.0072 (true) | NR | NR | NR | -0.4312 | 0.0031 (true) | NR | NR | NR |
| course_teach | 0.0496 | 0.7945 (false) | NR | NR | NR | 0.0496 | 0.7945 (false) | NR | NR | NR |
| cre_Doc_Template_Mgt | -0.1459 | 0.1856 (false) | NR | NR | NR | -0.1459 | 0.1856 (false) | NR | NR | NR |
| debit_card_specializing | -0.3243 | 0.0089 (true) | NR | NR | NR | -0.3322 | 0.0073 (true) | NR | NR | NR |
| dog_kennels | -0.3157 | 0.0039 (true) | NR | NR | NR | -0.2490 | 0.0241 (true) | NR | NR | NR |
| employee_hire_evaluation | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| european_football_2 | -0.5033 | 1.21e-09 (true) | NR | NR | NR | -0.5392 | 4.32e-11 (true) | NR | NR | NR |
| financial | -0.3248 | 0.0007 (true) | -0.0929 | 0.3438 (false) | -0.2320 | -0.3489 | 0.0002 (true) | -0.1073 | 0.2738 (false) | -0.2416 |
| flight_2 | -0.1440 | 0.2027 (false) | NR | NR | NR | -0.0521 | 0.6465 (false) | NR | NR | NR |
| formula_1 | -0.3828 | 1.86e-07 (true) | NR | NR | NR | -0.3481 | 2.51e-06 (true) | NR | NR | NR |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| network_1 | -0.2144 | 0.1126 (false) | NR | NR | NR | -0.1991 | 0.1412 (false) | NR | NR | NR |
| orchestra | 0.0367 | 0.8219 (false) | NR | NR | NR | 0.0367 | 0.8219 (false) | NR | NR | NR |
| pets_1 | -0.1805 | 0.2526 (false) | NR | NR | NR | -0.2733 | 0.0799 (false) | NR | NR | NR |
| poker_player | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| real_estate_properties | -0.4851 | 0.5149 (false) | NR | NR | NR | -0.2357 | 0.7643 (false) | NR | NR | NR |
| singer | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| student_transcripts_tracking | -0.4089 | 0.0002 (true) | NR | NR | NR | -0.3891 | 0.0004 (true) | NR | NR | NR |
| superhero | -0.4207 | 6.89e-07 (true) | NR | NR | NR | -0.3944 | 3.75e-06 (true) | NR | NR | NR |
| thrombosis_prediction | -0.0967 | 0.2194 (false) | -0.0819 | 0.2986 (false) | -0.0148 | -0.0676 | 0.3909 (false) | -0.0592 | 0.4531 (false) | -0.0085 |
| toxicology | -0.2581 | 0.0017 (true) | NR | NR | NR | -0.2879 | 0.0004 (true) | NR | NR | NR |
| tvshow | -0.0819 | 0.5267 (false) | NR | NR | NR | -0.0540 | 0.6770 (false) | NR | NR | NR |
| voter_1 | -0.4432 | 0.0980 (false) | NR | NR | NR | -0.4432 | 0.0980 (false) | NR | NR | NR |
| world_1 | -0.3201 | 0.0004 (true) | NR | NR | NR | -0.2737 | 0.0025 (true) | NR | NR | NR |
| wta_1 | -0.5829 | 6.67e-07 (true) | NR | NR | NR | -0.4296 | 0.0005 (true) | NR | NR | NR |
| **MODEL'S TOTAL** | **-0.3872** | **5.11e-87 (true)** | **-0.1643** | **4.87e-16 (true)** | **-0.2229** | **-0.3646** | **1.20e-76 (true)** | **-0.1684** | **8.56e-17 (true)** | **-0.1961** |

## Complexity Correlations

| Database | Pearson stats db_conn | Pearson p-value db_conn | Pearson stats text | Pearson p-value text | Pearson delta | Spearman stats db_conn | Spearman p-value db_conn | Spearman stats text | Spearman p-value text | Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.3386 | 0.1996 (false) | -0.2794 | 0.2947 (false) | -0.0592 | -0.3756 | 0.1517 (false) | -0.4018 | 0.1229 (false) | +0.0262 |
| california_schools | -0.1766 | 0.0978 (false) | -0.2488 | 0.0187 (true) | +0.0722 | -0.1404 | 0.1894 (false) | -0.2638 | 0.0125 (true) | +0.1234 |
| car_1 | 0.0192 | 0.8559 (false) | -0.0790 | 0.4542 (false) | +0.0982 | 0.0415 | 0.6942 (false) | -0.0866 | 0.4119 (false) | +0.1281 |
| card_games | -0.1944 | 0.0070 (true) | -0.2564 | 0.0003 (true) | +0.0620 | -0.1871 | 0.0095 (true) | -0.2652 | 0.0002 (true) | +0.0781 |
| codebase_community | -0.1349 | 0.0665 (false) | -0.1474 | 0.0446 (true) | +0.0126 | -0.1036 | 0.1595 (false) | -0.1361 | 0.0639 (false) | +0.0326 |
| concert_singer | -0.3003 | 0.0450 (true) | -0.0811 | 0.5964 (false) | -0.2192 | -0.2921 | 0.0515 (false) | -0.0744 | 0.6272 (false) | -0.2177 |
| course_teach | -0.2234 | 0.2354 (false) | -0.1357 | 0.4745 (false) | -0.0876 | -0.2410 | 0.1996 (false) | -0.1768 | 0.3499 (false) | -0.0641 |
| cre_Doc_Template_Mgt | -0.1796 | 0.1021 (false) | 0.0145 | 0.8960 (false) | -0.1941 | -0.1570 | 0.1539 (false) | 0.0241 | 0.8276 (false) | -0.1811 |
| debit_card_specializing | -0.2559 | 0.0412 (true) | -0.0568 | 0.6560 (false) | -0.1992 | -0.3432 | 0.0055 (true) | -0.1163 | 0.3602 (false) | -0.2269 |
| dog_kennels | -0.3197 | 0.0034 (true) | -0.2217 | 0.0453 (true) | -0.0980 | -0.3366 | 0.0020 (true) | -0.2342 | 0.0342 (true) | -0.1024 |
| employee_hire_evaluation | -0.2567 | 0.1198 (false) | -0.2567 | 0.1198 (false) | +0.0000 | -0.2290 | 0.1668 (false) | -0.2290 | 0.1668 (false) | +0.0000 |
| european_football_2 | -0.1451 | 0.1009 (false) | -0.1185 | 0.1810 (false) | -0.0266 | -0.2055 | 0.0195 (true) | -0.1703 | 0.0537 (false) | -0.0352 |
| financial | -0.0869 | 0.3757 (false) | -0.0923 | 0.3468 (false) | +0.0054 | -0.0709 | 0.4702 (false) | -0.0927 | 0.3447 (false) | +0.0218 |
| flight_2 | -0.2867 | 0.0099 (true) | -0.3383 | 0.0021 (true) | +0.0516 | -0.2827 | 0.0111 (true) | -0.3108 | 0.0050 (true) | +0.0281 |
| formula_1 | -0.1868 | 0.0136 (true) | -0.0517 | 0.4983 (false) | -0.1351 | -0.1569 | 0.0387 (true) | -0.0615 | 0.4199 (false) | -0.0953 |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| network_1 | 0.0014 | 0.9919 (false) | -0.0954 | 0.4841 (false) | +0.0968 | -0.0397 | 0.7714 (false) | -0.0967 | 0.4786 (false) | +0.0569 |
| orchestra | -0.3200 | 0.0441 (true) | -0.0310 | 0.8493 (false) | -0.2890 | -0.3062 | 0.0547 (false) | 0.0000 | 1.0000 (false) | -0.3062 |
| pets_1 | -0.2765 | 0.0763 (false) | 0.1602 | 0.3107 (false) | -0.4367 | -0.2088 | 0.1844 (false) | 0.1493 | 0.3453 (false) | -0.3581 |
| poker_player | NR | NR | -0.3303 | 0.0374 (true) | NR | NR | NR | -0.2965 | 0.0632 (false) | NR |
| real_estate_properties | -0.2294 | 0.7706 (false) | 0.6623 | 0.3377 (false) | -0.8917 | 0.0000 | 1.0000 (false) | 0.8165 | 0.1835 (false) | -0.8165 |
| singer | NR | NR | 0.1984 | 0.2932 (false) | NR | NR | NR | 0.2065 | 0.2737 (false) | NR |
| student_transcripts_tracking | -0.3545 | 0.0014 (true) | -0.2258 | 0.0469 (true) | -0.1287 | -0.3572 | 0.0013 (true) | -0.1985 | 0.0815 (false) | -0.1587 |
| superhero | -0.0797 | 0.3690 (false) | -0.0154 | 0.8628 (false) | -0.0644 | -0.1139 | 0.1988 (false) | -0.0069 | 0.9377 (false) | -0.1069 |
| thrombosis_prediction | -0.1902 | 0.0150 (true) | -0.1159 | 0.1406 (false) | -0.0743 | -0.1871 | 0.0168 (true) | -0.1102 | 0.1615 (false) | -0.0770 |
| toxicology | -0.2657 | 0.0012 (true) | -0.2263 | 0.0062 (true) | -0.0393 | -0.3123 | 0.0001 (true) | -0.2803 | 0.0006 (true) | -0.0320 |
| tvshow | -0.2068 | 0.1067 (false) | -0.3768 | 0.0025 (true) | +0.1699 | -0.2010 | 0.1173 (false) | -0.3025 | 0.0168 (true) | +0.1016 |
| voter_1 | -0.2796 | 0.3129 (false) | 0.6110 | 0.0155 (true) | -0.8906 | -0.2864 | 0.3007 (false) | 0.6904 | 0.0044 (true) | -0.9768 |
| world_1 | -0.2025 | 0.0265 (true) | -0.1281 | 0.1633 (false) | -0.0745 | -0.2275 | 0.0125 (true) | -0.1457 | 0.1122 (false) | -0.0817 |
| wta_1 | 0.0278 | 0.8301 (false) | -0.1469 | 0.2544 (false) | +0.1747 | 0.0458 | 0.7239 (false) | -0.1274 | 0.3238 (false) | +0.1732 |
| **MODEL'S TOTAL** | -0.1977 | 1.17e-22 (true) | -0.1503 | 1.18e-13 (true) | -0.0473 | -0.2071 | 9.47e-25 (true) | -0.1681 | 9.78e-17 (true) | -0.0390 |
| **AVG COLUMNS** | **-0.1907** | **3.51e-21 (true)** | **-0.2186** | **1.83e-27 (true)** | **+0.0279** | **-0.1437** | **1.36e-12 (true)** | **-0.1861** | **3.17e-20 (true)** | **+0.0424** |

