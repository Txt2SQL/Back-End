# Model Performance Summary: `Qwen3-coder-next`

**Base directory:** `C:\Users\pietr\Desktop\UniTn\Tesi\Progetto Text2SQL\Back-End\tests\output\generations`

Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.

## Status

| Database | Success db_conn | Success text | Success delta | Avg time db_conn | Avg time text | Avg time delta | Avg attempts db_conn | Avg attempts text | Avg attempts delta | Syntax db_conn | Syntax text | Syntax delta | Runtime db_conn | Runtime text | Incorrect db_conn | Incorrect text | Incorrect delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 93.75% | 87.5% | +6.25% | 8.07s | 5.6s | +2.48s | 1.38 | 1 | +0.38 | 0 | 0 | +0 | 0 | 0 | 1 | 2 | -1 |
| california_schools | 34.83% | 24.72% | +10.11% | 12.6s | 7.16s | +5.45s | 1.6 | 2.11 | -0.52 | 0 | 0 | +0 | 0 | 11 | 47 | 26 | +21 |
| car_1 | 56.52% | 59.78% | -3.26% | 10.35s | 5.62s | +4.73s | 1.43 | 1 | +0.43 | 0 | 0 | +0 | 0 | 3 | 40 | 34 | +6 |
| card_games | 37.7% | 31.94% | +5.76% | 14.24s | 8.54s | +5.71s | 1.71 | 1.03 | +0.68 | 0 | 0 | +0 | 0 | 9 | 117 | 119 | -2 |
| codebase_community | 52.15% | 47.31% | +4.84% | 9.8s | 6.53s | +3.27s | 1.6 | 1 | +0.6 | 0 | 0 | +0 | 0 | 22 | 81 | 69 | +12 |
| concert_singer | 80% | 86.67% | -6.67% | 7.19s | 4.88s | +2.31s | 1.16 | 1 | +0.16 | 0 | 0 | +0 | 1 | 0 | 8 | 6 | +2 |
| course_teach | 93.33% | 86.67% | +6.67% | 6.67s | 3.88s | +2.79s | 1.03 | 1 | +0.03 | 0 | 0 | +0 | 0 | 0 | 2 | 4 | -2 |
| cre_Doc_Template_Mgt | 91.67% | 77.38% | +14.29% | 6.62s | 3.77s | +2.85s | 1.23 | 1 | +0.23 | 0 | 0 | +0 | 0 | 8 | 7 | 11 | -4 |
| debit_card_specializing | 31.25% | 34.38% | -3.12% | 20.25s | 11.93s | +8.32s | 1.59 | 1 | +0.59 | 0 | 0 | +0 | 0 | 4 | 44 | 38 | +6 |
| dog_kennels | 75.61% | 64.63% | +10.98% | 9.84s | 4.71s | +5.13s | 1.4 | 1 | +0.4 | 0 | 0 | +0 | 2 | 11 | 16 | 18 | -2 |
| employee_hire_evaluation | 97.37% | 97.37% | +0% | 5.65s | 3.66s | +1.99s | 1 | 1 | +0 | 0 | 0 | +0 | 0 | 0 | 1 | 1 | +0 |
| european_football_2 | 55.81% | 48.06% | +7.75% | 22.01s | 8.29s | +13.72s | 1.53 | 1 | +0.53 | 0 | 0 | +0 | 0 | 16 | 57 | 51 | +6 |
| financial | 19.81% | 18.87% | +0.94% | 25.1s | 5.71s | +19.39s | 2.87 | 1.11 | +1.75 | 0 | 0 | +0 | 13 | 51 | 68 | 32 | +36 |
| flight_2 | 87.5% | 83.75% | +3.75% | 6.27s | 3.88s | +2.39s | 1.21 | 1 | +0.21 | 0 | 0 | +0 | 0 | 3 | 10 | 10 | +0 |
| formula_1 | 43.68% | 29.31% | +14.37% | 12.89s | 5.35s | +7.54s | 2.03 | 1 | +1.03 | 0 | 0 | +0 | 4 | 48 | 93 | 75 | +18 |
| museum_visit | 100% | 100% | +0% | 6.24s | 3.75s | +2.49s | 1.06 | 1 | +0.06 | 0 | 0 | +0 | 0 | 0 | 0 | 0 | +0 |
| network_1 | 83.93% | 82.14% | +1.79% | 7.66s | 3.94s | +3.72s | 1.5 | 1 | +0.5 | 0 | 0 | +0 | 0 | 3 | 9 | 7 | +2 |
| orchestra | 95% | 87.5% | +7.5% | 5.49s | 4.18s | +1.3s | 1.02 | 1 | +0.02 | 0 | 0 | +0 | 0 | 3 | 2 | 2 | +0 |
| pets_1 | 92.86% | 90.48% | +2.38% | 6.76s | 4.54s | +2.22s | 1.1 | 1 | +0.1 | 0 | 0 | +0 | 0 | 2 | 3 | 2 | +1 |
| poker_player | 100% | 90% | +10% | 5.17s | 3.69s | +1.47s | 1.05 | 1 | +0.05 | 0 | 0 | +0 | 0 | 1 | 0 | 3 | -3 |
| real_estate_properties | 50% | 75% | -25% | 11.13s | 4.17s | +6.96s | 2.5 | 1 | +1.5 | 0 | 0 | +0 | 0 | 1 | 2 | 0 | +2 |
| singer | 100% | 93.33% | +6.67% | 5.42s | 3.58s | +1.85s | 1.03 | 1 | +0.03 | 0 | 0 | +0 | 0 | 0 | 0 | 2 | -2 |
| student_transcripts_tracking | 66.67% | 61.54% | +5.13% | 11.52s | 5.3s | +6.22s | 1.63 | 1 | +0.63 | 0 | 0 | +0 | 2 | 7 | 23 | 23 | +0 |
| superhero | 34.88% | 31.78% | +3.1% | 18.59s | 4.14s | +14.45s | 2.78 | 1 | +1.78 | 0 | 0 | +0 | 29 | 51 | 51 | 35 | +16 |
| toxicology | 19.31% | 20% | -0.69% | 11.83s | 3.57s | +8.26s | 1.66 | 1 | +0.66 | 0 | 0 | +0 | 2 | 6 | 114 | 109 | +5 |
| tvshow | 85.48% | 77.42% | +8.06% | 7.8s | 4.53s | +3.28s | 1.74 | 1 | +0.74 | 0 | 0 | +0 | 0 | 5 | 9 | 9 | +0 |
| voter_1 | 93.33% | 66.67% | +26.67% | 6.3s | 4.08s | +2.22s | 1.27 | 1 | +0.27 | 0 | 0 | +0 | 0 | 4 | 1 | 1 | +0 |
| **MODEL VERDICT** | **56.76%** | **51.43%** | **+5.33%** | **12.32s** | **5.65s** | **+6.67s** | **1.67** | **1.06** | **+0.61** | **0** | **0** | **+0** | **53** | **269** | **806** | **689** | **+117** |

## Correlations

| Database | Attempts Pearson stats db_conn | Attempts Pearson p-value db_conn | Attempts Pearson stats text | Attempts Pearson p-value text | Attempts Pearson delta | Attempts Spearman stats db_conn | Attempts Spearman p-value db_conn | Attempts Spearman stats text | Attempts Spearman p-value text | Attempts Spearman delta | Complexity Pearson stats db_conn | Complexity Pearson p-value db_conn | Complexity Pearson stats text | Complexity Pearson p-value text | Complexity Pearson delta | Complexity Spearman stats db_conn | Complexity Spearman p-value db_conn | Complexity Spearman stats text | Complexity Spearman p-value text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 0.1615 | 0.5501 (false) | NR | NR | NR | 0.1721 | 0.5238 (false) | NR | NR | NR | -0.3386 | 0.1996 (false) | -0.2794 | 0.2947 (false) | -0.0592 | -0.3756 | 0.1517 (false) | -0.4018 | 0.1229 (false) | +0.0262 |
| california_schools | -0.2610 | 0.0135 (true) | -0.3640 | 0.0005 (true) | +0.1030 | -0.2512 | 0.0176 (true) | -0.3750 | 0.0003 (true) | +0.1238 | -0.2128 | 0.0453 (true) | -0.2488 | 0.0187 (true) | +0.0360 | -0.1942 | 0.0682 (false) | -0.2638 | 0.0125 (true) | +0.0696 |
| car_1 | -0.4013 | 7.35e-05 (true) | NR | NR | NR | -0.3646 | 0.0004 (true) | NR | NR | NR | 0.0192 | 0.8559 (false) | -0.0790 | 0.4542 (false) | +0.0982 | 0.0415 | 0.6942 (false) | -0.0866 | 0.4119 (false) | +0.1281 |
| card_games | -0.1751 | 0.0154 (true) | -0.0420 | 0.5642 (false) | -0.1331 | -0.1388 | 0.0556 (false) | -0.0420 | 0.5642 (false) | -0.0968 | -0.1944 | 0.0070 (true) | -0.2564 | 0.0003 (true) | +0.0620 | -0.1871 | 0.0095 (true) | -0.2652 | 0.0002 (true) | +0.0781 |
| codebase_community | -0.3602 | 4.41e-07 (true) | NR | NR | NR | -0.3246 | 6.19e-06 (true) | NR | NR | NR | -0.1349 | 0.0665 (false) | -0.1474 | 0.0446 (true) | +0.0126 | -0.1036 | 0.1595 (false) | -0.1361 | 0.0639 (false) | +0.0326 |
| concert_singer | -0.3950 | 0.0072 (true) | NR | NR | NR | -0.4312 | 0.0031 (true) | NR | NR | NR | -0.3003 | 0.0450 (true) | -0.0811 | 0.5964 (false) | -0.2192 | -0.2921 | 0.0515 (false) | -0.0744 | 0.6272 (false) | -0.2177 |
| course_teach | 0.0496 | 0.7945 (false) | NR | NR | NR | 0.0496 | 0.7945 (false) | NR | NR | NR | -0.2234 | 0.2354 (false) | -0.1357 | 0.4745 (false) | -0.0876 | -0.2410 | 0.1996 (false) | -0.1768 | 0.3499 (false) | -0.0641 |
| cre_Doc_Template_Mgt | -0.1459 | 0.1856 (false) | NR | NR | NR | -0.1459 | 0.1856 (false) | NR | NR | NR | -0.1796 | 0.1021 (false) | 0.0145 | 0.8960 (false) | -0.1941 | -0.1570 | 0.1539 (false) | 0.0241 | 0.8276 (false) | -0.1811 |
| debit_card_specializing | -0.3243 | 0.0089 (true) | NR | NR | NR | -0.3322 | 0.0073 (true) | NR | NR | NR | -0.2559 | 0.0412 (true) | -0.0568 | 0.6560 (false) | -0.1992 | -0.3432 | 0.0055 (true) | -0.1163 | 0.3602 (false) | -0.2269 |
| dog_kennels | -0.3157 | 0.0039 (true) | NR | NR | NR | -0.2490 | 0.0241 (true) | NR | NR | NR | -0.3197 | 0.0034 (true) | -0.2217 | 0.0453 (true) | -0.0980 | -0.3366 | 0.0020 (true) | -0.2342 | 0.0342 (true) | -0.1024 |
| employee_hire_evaluation | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | -0.2567 | 0.1198 (false) | -0.2567 | 0.1198 (false) | +0.0000 | -0.2290 | 0.1668 (false) | -0.2290 | 0.1668 (false) | +0.0000 |
| european_football_2 | -0.5033 | 1.21e-09 (true) | NR | NR | NR | -0.5392 | 4.32e-11 (true) | NR | NR | NR | -0.1451 | 0.1009 (false) | -0.1185 | 0.1810 (false) | -0.0266 | -0.2055 | 0.0195 (true) | -0.1703 | 0.0537 (false) | -0.0352 |
| financial | -0.3248 | 0.0007 (true) | -0.0929 | 0.3438 (false) | -0.2320 | -0.3489 | 0.0002 (true) | -0.1073 | 0.2738 (false) | -0.2416 | -0.0869 | 0.3757 (false) | -0.0923 | 0.3468 (false) | +0.0054 | -0.0709 | 0.4702 (false) | -0.0927 | 0.3447 (false) | +0.0218 |
| flight_2 | -0.1440 | 0.2027 (false) | NR | NR | NR | -0.0521 | 0.6465 (false) | NR | NR | NR | -0.2867 | 0.0099 (true) | -0.3383 | 0.0021 (true) | +0.0516 | -0.2827 | 0.0111 (true) | -0.3108 | 0.0050 (true) | +0.0281 |
| formula_1 | -0.3828 | 1.86e-07 (true) | NR | NR | NR | -0.3481 | 2.51e-06 (true) | NR | NR | NR | -0.1868 | 0.0136 (true) | -0.0517 | 0.4983 (false) | -0.1351 | -0.1569 | 0.0387 (true) | -0.0615 | 0.4199 (false) | -0.0953 |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| network_1 | -0.2144 | 0.1126 (false) | NR | NR | NR | -0.1991 | 0.1412 (false) | NR | NR | NR | 0.0014 | 0.9919 (false) | -0.0954 | 0.4841 (false) | +0.0968 | -0.0397 | 0.7714 (false) | -0.0967 | 0.4786 (false) | +0.0569 |
| orchestra | 0.0367 | 0.8219 (false) | NR | NR | NR | 0.0367 | 0.8219 (false) | NR | NR | NR | -0.3200 | 0.0441 (true) | -0.0310 | 0.8493 (false) | -0.2890 | -0.3062 | 0.0547 (false) | 0.0000 | 1.0000 (false) | -0.3062 |
| pets_1 | -0.1805 | 0.2526 (false) | NR | NR | NR | -0.2733 | 0.0799 (false) | NR | NR | NR | -0.2765 | 0.0763 (false) | 0.1602 | 0.3107 (false) | -0.4367 | -0.2088 | 0.1844 (false) | 0.1493 | 0.3453 (false) | -0.3581 |
| poker_player | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | -0.3303 | 0.0374 (true) | NR | NR | NR | -0.2965 | 0.0632 (false) | NR |
| real_estate_properties | -0.4851 | 0.5149 (false) | NR | NR | NR | -0.2357 | 0.7643 (false) | NR | NR | NR | -0.2294 | 0.7706 (false) | 0.6623 | 0.3377 (false) | -0.8917 | 0.0000 | 1.0000 (false) | 0.8165 | 0.1835 (false) | -0.8165 |
| singer | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | 0.1984 | 0.2932 (false) | NR | NR | NR | 0.2065 | 0.2737 (false) | NR |
| student_transcripts_tracking | -0.4089 | 0.0002 (true) | NR | NR | NR | -0.3891 | 0.0004 (true) | NR | NR | NR | -0.3545 | 0.0014 (true) | -0.2258 | 0.0469 (true) | -0.1287 | -0.3572 | 0.0013 (true) | -0.1985 | 0.0815 (false) | -0.1587 |
| superhero | -0.4945 | 2.58e-09 (true) | NR | NR | NR | -0.4738 | 1.42e-08 (true) | NR | NR | NR | -0.0639 | 0.4721 (false) | -0.0154 | 0.8628 (false) | -0.0485 | -0.0925 | 0.2971 (false) | -0.0069 | 0.9377 (false) | -0.0856 |
| toxicology | -0.2581 | 0.0017 (true) | NR | NR | NR | -0.2879 | 0.0004 (true) | NR | NR | NR | -0.2657 | 0.0012 (true) | -0.2263 | 0.0062 (true) | -0.0393 | -0.3123 | 0.0001 (true) | -0.2803 | 0.0006 (true) | -0.0320 |
| tvshow | -0.0819 | 0.5267 (false) | NR | NR | NR | -0.0540 | 0.6770 (false) | NR | NR | NR | -0.2068 | 0.1067 (false) | -0.3768 | 0.0025 (true) | +0.1699 | -0.2010 | 0.1173 (false) | -0.3025 | 0.0168 (true) | +0.1016 |
| voter_1 | -0.4432 | 0.0980 (false) | NR | NR | NR | -0.4432 | 0.0980 (false) | NR | NR | NR | -0.2796 | 0.3129 (false) | 0.6110 | 0.0155 (true) | -0.8906 | -0.2864 | 0.3007 (false) | 0.6904 | 0.0044 (true) | -0.9768 |
| **MODEL VERDICT** | **-0.4042** | **5.27e-82 (true)** | **-0.1261** | **8.94e-09 (true)** | **-0.2781** | **-0.3843** | **1.18e-73 (true)** | **-0.1318** | **1.84e-09 (true)** | **-0.2525** | **-0.2050** | **5.03e-21 (true)** | **-0.1536** | **2.24e-12 (true)** | **-0.0513** | **-0.2122** | **1.90e-22 (true)** | **-0.1676** | **1.75e-14 (true)** | **-0.0445** |

