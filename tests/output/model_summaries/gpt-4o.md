# Model Performance Summary: `gpt-4o`

**Base directory:** `C:\Users\pietr\Desktop\UniTn\Tesi\Progetto Text2SQL\Back-End\tests\output\generations`

Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.

## Status

| Database | Success db_conn | Success text | Success delta | Avg time db_conn | Avg time text | Avg time delta | Avg attempts db_conn | Avg attempts text | Avg attempts delta | Syntax db_conn | Syntax text | Syntax delta | Runtime db_conn | Runtime text | Incorrect db_conn | Incorrect text | Incorrect delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 81.25% | 12.5% | +68.75% | 10.75s | 2.54s | +8.21s | 2.31 | 1 | +1.31 | 0 | 0 | +0 | 0 | 14 | 3 | 0 | +3 |
| california_schools | 30.34% | 3.37% | +26.97% | 15.21s | 5.51s | +9.7s | 2.19 | 1.89 | +0.3 | 0 | 0 | +0 | 1 | 66 | 44 | 3 | +41 |
| car_1 | 55.43% | 4.35% | +51.09% | 12.27s | 5.04s | +7.23s | 2.23 | 1 | +1.23 | 0 | 0 | +0 | 0 | 77 | 41 | 11 | +30 |
| card_games | 37.17% | 2.09% | +35.08% | 13.61s | 4.07s | +9.53s | 2.49 | 1.03 | +1.47 | 0 | 0 | +0 | 1 | 178 | 117 | 7 | +110 |
| codebase_community | 51.61% | 2.69% | +48.92% | 11.8s | 2.98s | +8.82s | 2.39 | 1 | +1.39 | 0 | 0 | +0 | 2 | 178 | 82 | 3 | +79 |
| concert_singer | 84.44% | 11.11% | +73.33% | 9.04s | 4.67s | +4.37s | 1.93 | 1 | +0.93 | 0 | 0 | +0 | 0 | 40 | 7 | 0 | +7 |
| course_teach | 86.67% | 3.33% | +83.33% | 8.56s | 3.92s | +4.64s | 1.97 | 1 | +0.97 | 0 | 0 | +0 | 0 | 29 | 4 | 0 | +4 |
| cre_Doc_Template_Mgt | 89.29% | 0% | +89.29% | 9.26s | 3.87s | +5.39s | 2.06 | 1 | +1.06 | 0 | 0 | +0 | 0 | 84 | 9 | 0 | +9 |
| debit_card_specializing | 20.31% | 1.56% | +18.75% | 19.99s | 5.26s | +14.73s | 2.17 | 1 | +1.17 | 0 | 0 | +0 | 0 | 53 | 51 | 10 | +41 |
| dog_kennels | 71.95% | 1.22% | +70.73% | 10.55s | 4.36s | +6.19s | 2.24 | 1 | +1.24 | 0 | 0 | +0 | 5 | 79 | 18 | 2 | +16 |
| employee_hire_evaluation | 94.74% | 7.89% | +86.84% | 8.91s | 3.91s | +5s | 1.87 | 1 | +0.87 | 0 | 0 | +0 | 0 | 35 | 2 | 0 | +2 |
| european_football_2 | 55.81% | 6.2% | +49.61% | 21.29s | 3.77s | +17.52s | 2.22 | 1.02 | +1.2 | 0 | 0 | +0 | 0 | 113 | 57 | 8 | +49 |
| financial | 23.58% | 0% | +23.58% | 23.3s | 3.48s | +19.82s | 3.58 | 1.01 | +2.58 | 0 | 0 | +0 | 25 | 106 | 55 | 0 | +55 |
| flight_2 | 87.5% | 6.25% | +81.25% | 10.21s | 5.46s | +4.75s | 2.21 | 1 | +1.21 | 0 | 0 | +0 | 0 | 75 | 10 | 0 | +10 |
| formula_1 | 34.48% | 2.3% | +32.18% | 15.13s | 3.67s | +11.46s | 2.66 | 1.03 | +1.63 | 0 | 0 | +0 | 10 | 156 | 101 | 14 | +87 |
| museum_visit | 100% | 0% | +100% | 8.96s | 3.94s | +5.03s | 2 | 1 | +1 | 0 | 0 | +0 | 0 | 18 | 0 | 0 | +0 |
| network_1 | 75% | 0% | +75% | 9.21s | 4.35s | +4.85s | 2.12 | 1 | +1.12 | 0 | 0 | +0 | 0 | 56 | 14 | 0 | +14 |
| orchestra | 97.5% | 0% | +97.5% | 6.84s | 4.63s | +2.21s | 1.68 | 1 | +0.68 | 0 | 0 | +0 | 0 | 40 | 1 | 0 | +1 |
| pets_1 | 80.95% | 4.76% | +76.19% | 10.61s | 3.87s | +6.75s | 2 | 1 | +1 | 0 | 0 | +0 | 1 | 40 | 7 | 0 | +7 |
| poker_player | 100% | 70% | +30% | 5.82s | 4.32s | +1.5s | 1.2 | 1 | +0.2 | 0 | 0 | +0 | 0 | 11 | 0 | 1 | -1 |
| real_estate_properties | 50% | 0% | +50% | 14.08s | 4.64s | +9.44s | 3.25 | 1 | +2.25 | 0 | 0 | +0 | 1 | 4 | 1 | 0 | +1 |
| singer | 100% | 36.67% | +63.33% | 6.07s | 3.94s | +2.12s | 1.47 | 1 | +0.47 | 0 | 0 | +0 | 0 | 19 | 0 | 0 | +0 |
| student_transcripts_tracking | 65.38% | 0% | +65.38% | 11.81s | 4.19s | +7.62s | 2.47 | 1.01 | +1.46 | 0 | 0 | +0 | 3 | 78 | 23 | 0 | +23 |
| superhero | 28.68% | 2.33% | +26.36% | 19.9s | 2.88s | +17.02s | 4.05 | 1 | +3.05 | 0 | 0 | +0 | 47 | 123 | 42 | 3 | +39 |
| toxicology | 20% | 0% | +20% | 16.97s | 1.89s | +15.08s | 3.15 | 1 | +2.15 | 0 | 0 | +0 | 13 | 144 | 102 | 1 | +101 |
| tvshow | 80.65% | 0% | +80.65% | 9.63s | 4.09s | +5.54s | 2.18 | 1 | +1.18 | 0 | 0 | +0 | 0 | 62 | 12 | 0 | +12 |
| voter_1 | 86.67% | 13.33% | +73.33% | 7.95s | 5.15s | +2.8s | 1.87 | 1 | +0.87 | 0 | 0 | +0 | 0 | 13 | 2 | 0 | +2 |
| **MODEL VERDICT** | **54.09%** | **4.46%** | **+49.64%** | **13.84s** | **3.89s** | **+9.95s** | **2.48** | **1.05** | **+1.44** | **0** | **0** | **+0** | **109** | **1891** | **805** | **63** | **+742** |

## Correlations

| Database | Attempts Pearson stats db_conn | Attempts Pearson p-value db_conn | Attempts Pearson stats text | Attempts Pearson p-value text | Attempts Pearson delta | Attempts Spearman stats db_conn | Attempts Spearman p-value db_conn | Attempts Spearman stats text | Attempts Spearman p-value text | Attempts Spearman delta | Complexity Pearson stats db_conn | Complexity Pearson p-value db_conn | Complexity Pearson stats text | Complexity Pearson p-value text | Complexity Pearson delta | Complexity Spearman stats db_conn | Complexity Spearman p-value db_conn | Complexity Spearman stats text | Complexity Spearman p-value text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.5375 | 0.0318 (true) | NR | NR | NR | -0.5375 | 0.0318 (true) | NR | NR | NR | -0.2634 | 0.3242 (false) | -0.0811 | 0.7652 (false) | -0.1823 | -0.4479 | 0.0819 (false) | -0.0423 | 0.8764 (false) | -0.4056 |
| california_schools | -0.0033 | 0.9752 (false) | -0.1067 | 0.3196 (false) | +0.1034 | 0.0868 | 0.4184 (false) | -0.1214 | 0.2572 (false) | +0.2082 | -0.1557 | 0.1452 (false) | -0.0330 | 0.7586 (false) | -0.1226 | -0.1367 | 0.2013 (false) | -0.0259 | 0.8096 (false) | -0.1108 |
| car_1 | -0.3522 | 0.0006 (true) | NR | NR | NR | -0.3267 | 0.0015 (true) | NR | NR | NR | 0.0010 | 0.9921 (false) | 0.0255 | 0.8092 (false) | -0.0245 | 0.0397 | 0.7068 (false) | 0.0556 | 0.5983 (false) | -0.0159 |
| card_games | -0.2484 | 0.0005 (true) | -0.0129 | 0.8596 (false) | -0.2355 | -0.2171 | 0.0026 (true) | -0.0150 | 0.8363 (false) | -0.2021 | -0.2551 | 0.0004 (true) | -0.0001 | 0.9990 (false) | -0.2550 | -0.2581 | 0.0003 (true) | 0.0174 | 0.8108 (false) | -0.2755 |
| codebase_community | -0.3943 | 2.56e-08 (true) | NR | NR | NR | -0.3761 | 1.22e-07 (true) | NR | NR | NR | -0.1881 | 0.0101 (true) | 0.0114 | 0.8773 (false) | -0.1995 | -0.1642 | 0.0251 (true) | 0.0122 | 0.8690 (false) | -0.1764 |
| concert_singer | -0.3423 | 0.0213 (true) | NR | NR | NR | -0.1103 | 0.4707 (false) | NR | NR | NR | -0.3242 | 0.0298 (true) | 0.3342 | 0.0248 (true) | -0.6584 | -0.3176 | 0.0335 (true) | 0.3330 | 0.0254 (true) | -0.6505 |
| course_teach | -0.0728 | 0.7021 (false) | NR | NR | NR | -0.0728 | 0.7021 (false) | NR | NR | NR | -0.3278 | 0.0770 (false) | 0.0824 | 0.6649 (false) | -0.4103 | -0.3536 | 0.0552 (false) | 0.0893 | 0.6389 (false) | -0.4429 |
| cre_Doc_Template_Mgt | -0.0555 | 0.6159 (false) | NR | NR | NR | -0.1358 | 0.2181 (false) | NR | NR | NR | -0.0663 | 0.5491 (false) | NR | NR | NR | -0.0734 | 0.5070 (false) | NR | NR | NR |
| debit_card_specializing | -0.1828 | 0.1481 (false) | NR | NR | NR | -0.1481 | 0.2430 (false) | NR | NR | NR | -0.2059 | 0.1026 (false) | -0.0942 | 0.4591 (false) | -0.1117 | -0.3097 | 0.0128 (true) | -0.1710 | 0.1767 (false) | -0.1387 |
| dog_kennels | -0.3984 | 0.0002 (true) | NR | NR | NR | -0.2839 | 0.0097 (true) | NR | NR | NR | -0.3790 | 0.0004 (true) | 0.1954 | 0.0786 (false) | -0.5743 | -0.3861 | 0.0003 (true) | 0.1676 | 0.1323 (false) | -0.5537 |
| employee_hire_evaluation | -0.0662 | 0.6930 (false) | NR | NR | NR | -0.0725 | 0.6654 (false) | NR | NR | NR | -0.1495 | 0.3703 (false) | 0.0500 | 0.7656 (false) | -0.1995 | -0.1532 | 0.3585 (false) | 0.0544 | 0.7458 (false) | -0.2076 |
| european_football_2 | -0.2101 | 0.0169 (true) | -0.0323 | 0.7166 (false) | -0.1778 | -0.1320 | 0.1359 (false) | -0.0323 | 0.7166 (false) | -0.0997 | -0.2066 | 0.0188 (true) | -0.0426 | 0.6318 (false) | -0.1641 | -0.2579 | 0.0032 (true) | -0.0537 | 0.5457 (false) | -0.2042 |
| financial | -0.4161 | 9.15e-06 (true) | NR | NR | NR | -0.4193 | 7.68e-06 (true) | NR | NR | NR | -0.0774 | 0.4303 (false) | NR | NR | NR | -0.0727 | 0.4588 (false) | NR | NR | NR |
| flight_2 | -0.4819 | 6.00e-06 (true) | NR | NR | NR | -0.3997 | 0.0002 (true) | NR | NR | NR | -0.0697 | 0.5387 (false) | -0.0265 | 0.8157 (false) | -0.0433 | -0.0640 | 0.5730 (false) | -0.0092 | 0.9355 (false) | -0.0548 |
| formula_1 | -0.3074 | 3.69e-05 (true) | -0.0222 | 0.7712 (false) | -0.2852 | -0.2884 | 0.0001 (true) | -0.0235 | 0.7580 (false) | -0.2649 | -0.0946 | 0.2142 (false) | 0.1826 | 0.0159 (true) | -0.2772 | -0.1111 | 0.1444 (false) | 0.1337 | 0.0786 (false) | -0.2448 |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| network_1 | -0.2670 | 0.0466 (true) | NR | NR | NR | -0.2665 | 0.0471 (true) | NR | NR | NR | 0.0328 | 0.8102 (false) | NR | NR | NR | 0.0130 | 0.9245 (false) | NR | NR | NR |
| orchestra | -0.0921 | 0.5720 (false) | NR | NR | NR | -0.1036 | 0.5247 (false) | NR | NR | NR | -0.0920 | 0.5724 (false) | NR | NR | NR | -0.1425 | 0.3805 (false) | NR | NR | NR |
| pets_1 | -0.1348 | 0.3948 (false) | NR | NR | NR | 0.0065 | 0.9674 (false) | NR | NR | NR | -0.1066 | 0.5016 (false) | 0.1236 | 0.4354 (false) | -0.2302 | -0.1167 | 0.4618 (false) | 0.0935 | 0.5557 (false) | -0.2102 |
| poker_player | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | 0.2580 | 0.1079 (false) | NR | NR | NR | 0.2247 | 0.1633 (false) | NR |
| real_estate_properties | -0.5774 | 0.4226 (false) | NR | NR | NR | -0.5774 | 0.4226 (false) | NR | NR | NR | -0.2294 | 0.7706 (false) | NR | NR | NR | 0.0000 | 1.0000 (false) | NR | NR | NR |
| singer | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | 0.3798 | 0.0384 (true) | NR | NR | NR | 0.3782 | 0.0394 (true) | NR |
| student_transcripts_tracking | -0.4679 | 1.57e-05 (true) | NR | NR | NR | -0.4534 | 3.07e-05 (true) | NR | NR | NR | -0.3518 | 0.0016 (true) | NR | NR | NR | -0.3552 | 0.0014 (true) | NR | NR | NR |
| superhero | -0.4321 | 3.16e-07 (true) | NR | NR | NR | -0.4312 | 3.36e-07 (true) | NR | NR | NR | -0.1003 | 0.2579 (false) | 0.0485 | 0.5851 (false) | -0.1489 | -0.1003 | 0.2579 (false) | 0.0715 | 0.4206 (false) | -0.1718 |
| toxicology | -0.2885 | 0.0004 (true) | NR | NR | NR | -0.2913 | 0.0004 (true) | NR | NR | NR | -0.2327 | 0.0049 (true) | NR | NR | NR | -0.2617 | 0.0015 (true) | NR | NR | NR |
| tvshow | -0.3771 | 0.0025 (true) | NR | NR | NR | -0.3936 | 0.0015 (true) | NR | NR | NR | -0.0916 | 0.4791 (false) | NR | NR | NR | -0.0860 | 0.5062 (false) | NR | NR | NR |
| voter_1 | -0.1538 | 0.5841 (false) | NR | NR | NR | -0.1538 | 0.5841 (false) | NR | NR | NR | -0.3434 | 0.2102 (false) | 0.7447 | 0.0014 (true) | -1.0881 | -0.3036 | 0.2714 (false) | 0.6071 | 0.0164 (true) | -0.9107 |
| **MODEL VERDICT** | **-0.3999** | **3.71e-80 (true)** | **-0.0251** | **0.2533 (false)** | **-0.3748** | **-0.3517** | **3.54e-61 (true)** | **-0.0292** | **0.1852 (false)** | **-0.3225** | **-0.2001** | **4.33e-20 (true)** | **0.0115** | **0.6021 (false)** | **-0.2116** | **-0.2132** | **1.20e-22 (true)** | **0.0087** | **0.6938 (false)** | **-0.2218** |

