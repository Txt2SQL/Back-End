# Model Performance Summary: `gpt-5-mini`

**Base directory:** `C:\Users\pietr\Desktop\UniTn\Tesi\Progetto Text2SQL\Back-End\tests\output\generations`

Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.

## Status

| Database | Success db_conn | Success text | Success delta | Avg time db_conn | Avg time text | Avg time delta | Avg attempts db_conn | Avg attempts text | Avg attempts delta | Syntax db_conn | Syntax text | Syntax delta | Runtime db_conn | Runtime text | Incorrect db_conn | Incorrect text |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 81.25% | 31.25% | +50% | 19.87s | 9.43s | +10.44s | 1.5 | 1 | +0.5 | 0 | 0 | +0 | 0 | 11 | 3 | 0 |
| california_schools | 33.71% | 2.25% | +31.46% | 31.95s | 32.76s | -0.81s | 1.73 | 2.81 | -1.08 | 0 | 0 | +0 | 0 | 47 | 24 | 1 |
| car_1 | 60.87% | 4.35% | +56.52% | 32.31s | 12.02s | +20.29s | 1.97 | 1.01 | +0.96 | 0 | 0 | +0 | 0 | 87 | 36 | 1 |
| card_games | 39.79% | 4.19% | +35.6% | 25.55s | 10.43s | +15.12s | 2.02 | 1.03 | +0.99 | 0 | 0 | +0 | 0 | 167 | 109 | 14 |
| codebase_community | 48.39% | 5.38% | +43.01% | 23.78s | 8.69s | +15.08s | 2.1 | 1.02 | +1.09 | 0 | 0 | +0 | 0 | 167 | 87 | 7 |
| concert_singer | 84.44% | 20% | +64.44% | 23.66s | 10.68s | +12.98s | 1.76 | 1 | +0.76 | 0 | 0 | +0 | 0 | 36 | 7 | 0 |
| course_teach | 80% | 6.67% | +73.33% | 25.7s | 7.94s | +17.76s | 2.07 | 1 | +1.07 | 0 | 0 | +0 | 0 | 27 | 6 | 1 |
| cre_Doc_Template_Mgt | 84.52% | 2.38% | +82.14% | 23.3s | 7.85s | +15.45s | 1.83 | 1.02 | +0.81 | 0 | 0 | +0 | 0 | 82 | 13 | 0 |
| debit_card_specializing | 21.88% | 4.69% | +17.19% | 35.77s | 11.54s | +24.24s | 2.09 | 1 | +1.09 | 0 | 0 | +0 | 0 | 54 | 49 | 7 |
| dog_kennels | 73.17% | 7.32% | +65.85% | 19.52s | 8.21s | +11.31s | 1.78 | 1 | +0.78 | 0 | 0 | +0 | 0 | 74 | 22 | 2 |
| employee_hire_evaluation | 94.74% | 23.68% | +71.05% | 22.92s | 8.1s | +14.82s | 1.66 | 1 | +0.66 | 0 | 0 | +0 | 0 | 29 | 2 | 0 |
| european_football_2 | 53.49% | 13.95% | +39.53% | 32.57s | 12.65s | +19.92s | 1.88 | 1.04 | +0.84 | 0 | 0 | +0 | 0 | 89 | 60 | 22 |
| financial | 17.92% | 2.83% | +15.09% | 52.58s | 15.99s | +36.58s | 2.54 | 1.3 | +1.24 | 0 | 0 | +0 | 14 | 93 | 46 | 2 |
| flight_2 | 92.5% | 5% | +87.5% | 26.66s | 8.95s | +17.71s | 1.91 | 1 | +0.91 | 0 | 0 | +0 | 0 | 76 | 6 | 0 |
| formula_1 | 42.53% | 3.45% | +39.08% | 26.66s | 13.19s | +13.46s | 1.84 | 1.02 | +0.83 | 0 | 0 | +0 | 0 | 155 | 99 | 13 |
| museum_visit | 100% | 11.11% | +88.89% | 26.7s | 9.33s | +17.37s | 1.67 | 1 | +0.67 | 0 | 0 | +0 | 0 | 16 | 0 | 0 |
| network_1 | 67.86% | 0% | +67.86% | 18.84s | 8.08s | +10.76s | 1.7 | 1 | +0.7 | 0 | 0 | +0 | 0 | 54 | 18 | 2 |
| orchestra | 95% | 17.5% | +77.5% | 12.56s | 9.57s | +2.99s | 1.27 | 1.1 | +0.17 | 0 | 0 | +0 | 0 | 32 | 2 | 1 |
| pets_1 | 88.1% | 7.14% | +80.95% | 18.52s | 11.16s | +7.36s | 1.52 | 1 | +0.52 | 0 | 0 | +0 | 0 | 39 | 5 | 0 |
| poker_player | 97.5% | 55% | +42.5% | 9.04s | 7.87s | +1.16s | 1.02 | 1 | +0.02 | 0 | 0 | +0 | 0 | 16 | 1 | 2 |
| real_estate_properties | 50% | 0% | +50% | 25.89s | 7s | +18.89s | 2.75 | 1 | +1.75 | 0 | 0 | +0 | 1 | 4 | 1 | 0 |
| singer | 90% | 53.33% | +36.67% | 9.75s | 6.93s | +2.82s | 1.07 | 1 | +0.07 | 0 | 0 | +0 | 0 | 13 | 3 | 1 |
| student_transcripts_tracking | 60.26% | 0% | +60.26% | 27.43s | 8.31s | +19.13s | 2.15 | 1 | +1.15 | 0 | 0 | +0 | 0 | 78 | 31 | 0 |
| superhero | 42.64% | 6.2% | +36.43% | 40.54s | 11.14s | +29.4s | 2.68 | 1 | +1.68 | 0 | 0 | +0 | 15 | 111 | 56 | 10 |
| toxicology | 20% | 0% | +20% | 33.43s | 10.38s | +23.05s | 2.52 | 1.05 | +1.48 | 0 | 0 | +0 | 0 | 143 | 115 | 1 |
| tvshow | 85.48% | 12.9% | +72.58% | 18.44s | 7.25s | +11.19s | 1.89 | 1 | +0.89 | 0 | 0 | +0 | 0 | 54 | 9 | 0 |
| voter_1 | 73.33% | 0% | +73.33% | 19.2s | 7.57s | +11.63s | 2 | 1 | +1 | 0 | 0 | +0 | 0 | 15 | 4 | 0 |
| **MODEL VERDICT** | **55.11%** | **7.6%** | **+47.51%** | **27.97s** | **11.33s** | **+16.64s** | **1.99** | **1.11** | **+0.88** | **0** | **0** | **+0** | **30** | **1769** | **814** | **87** |

## Correlations

| Database | Attempts Pearson stats db_conn | Attempts Pearson p-value db_conn | Attempts Pearson stats text | Attempts Pearson p-value text | Attempts Pearson delta | Attempts Spearman stats db_conn | Attempts Spearman p-value db_conn | Attempts Spearman stats text | Attempts Spearman p-value text | Attempts Spearman delta | Complexity Pearson stats db_conn | Complexity Pearson p-value db_conn | Complexity Pearson stats text | Complexity Pearson p-value text | Complexity Pearson delta | Complexity Spearman stats db_conn | Complexity Spearman p-value db_conn | Complexity Spearman stats text | Complexity Spearman p-value text | Complexity Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.1601 | 0.5536 (false) | NR | NR | NR | -0.1601 | 0.5536 (false) | NR | NR | NR | -0.2634 | 0.3242 (false) | -0.4019 | 0.1228 (false) | +0.1384 | -0.3763 | 0.1509 (false) | -0.4224 | 0.1031 (false) | +0.0462 |
| california_schools | 0.1383 | 0.1963 (false) | -0.1408 | 0.1882 (false) | +0.2791 | 0.3375 | 0.0012 (true) | -0.1464 | 0.1710 (false) | +0.4839 | -0.0631 | 0.5571 (false) | -0.0805 | 0.4535 (false) | +0.0174 | -0.0341 | 0.7510 (false) | -0.0914 | 0.3940 (false) | +0.0573 |
| car_1 | -0.4295 | 1.93e-05 (true) | -0.0223 | 0.8325 (false) | -0.4072 | -0.3343 | 0.0011 (true) | -0.0223 | 0.8325 (false) | -0.3119 | -0.0399 | 0.7056 (false) | -0.0583 | 0.5808 (false) | +0.0184 | -0.0491 | 0.6421 (false) | -0.0433 | 0.6820 (false) | -0.0058 |
| card_games | -0.1852 | 0.0103 (true) | -0.0184 | 0.8004 (false) | -0.1668 | -0.1247 | 0.0858 (false) | -0.0215 | 0.7677 (false) | -0.1032 | -0.2279 | 0.0015 (true) | -0.0742 | 0.3076 (false) | -0.1537 | -0.2305 | 0.0013 (true) | -0.0628 | 0.3880 (false) | -0.1677 |
| codebase_community | -0.3518 | 8.50e-07 (true) | -0.0236 | 0.7495 (false) | -0.3282 | -0.2889 | 6.35e-05 (true) | -0.0249 | 0.7364 (false) | -0.2641 | -0.1916 | 0.0088 (true) | 0.0164 | 0.8247 (false) | -0.2079 | -0.1874 | 0.0104 (true) | 0.0713 | 0.3338 (false) | -0.2587 |
| concert_singer | -0.4348 | 0.0028 (true) | NR | NR | NR | -0.3209 | 0.0316 (true) | NR | NR | NR | -0.4872 | 0.0007 (true) | 0.0295 | 0.8473 (false) | -0.5168 | -0.4812 | 0.0008 (true) | 0.0283 | 0.8534 (false) | -0.5095 |
| course_teach | -0.3887 | 0.0337 (true) | NR | NR | NR | -0.3773 | 0.0398 (true) | NR | NR | NR | -0.3526 | 0.0560 (false) | 0.2234 | 0.2354 (false) | -0.5760 | -0.3807 | 0.0380 (true) | 0.2410 | 0.1996 (false) | -0.6216 |
| cre_Doc_Template_Mgt | 0.0567 | 0.6085 (false) | -0.0244 | 0.8257 (false) | +0.0811 | 0.0626 | 0.5719 (false) | -0.0244 | 0.8257 (false) | +0.0869 | -0.3148 | 0.0035 (true) | 0.2351 | 0.0313 (true) | -0.5499 | -0.3013 | 0.0054 (true) | 0.2184 | 0.0460 (true) | -0.5196 |
| debit_card_specializing | -0.0463 | 0.7163 (false) | NR | NR | NR | 0.0066 | 0.9586 (false) | NR | NR | NR | -0.2101 | 0.0956 (false) | -0.0207 | 0.8711 (false) | -0.1894 | -0.3100 | 0.0127 (true) | 0.0334 | 0.7930 (false) | -0.3434 |
| dog_kennels | -0.4448 | 2.83e-05 (true) | NR | NR | NR | -0.3854 | 0.0003 (true) | NR | NR | NR | -0.2548 | 0.0209 (true) | 0.0290 | 0.7960 (false) | -0.2838 | -0.2278 | 0.0396 (true) | 0.0565 | 0.6140 (false) | -0.2843 |
| employee_hire_evaluation | -0.1700 | 0.3076 (false) | NR | NR | NR | -0.1700 | 0.3076 (false) | NR | NR | NR | -0.3680 | 0.0230 (true) | -0.1631 | 0.3279 (false) | -0.2049 | -0.3283 | 0.0442 (true) | -0.1609 | 0.3345 (false) | -0.1673 |
| european_football_2 | -0.3961 | 3.37e-06 (true) | -0.0680 | 0.4442 (false) | -0.3282 | -0.3590 | 2.95e-05 (true) | -0.0720 | 0.4173 (false) | -0.2869 | -0.1316 | 0.1371 (false) | -0.0740 | 0.4043 (false) | -0.0576 | -0.1396 | 0.1146 (false) | -0.0973 | 0.2725 (false) | -0.0423 |
| financial | -0.2463 | 0.0109 (true) | -0.0488 | 0.6196 (false) | -0.1975 | -0.1656 | 0.0897 (false) | -0.0488 | 0.6196 (false) | -0.1169 | -0.0873 | 0.3736 (false) | 0.0512 | 0.6024 (false) | -0.1385 | -0.0686 | 0.4850 (false) | 0.0955 | 0.3300 (false) | -0.1641 |
| flight_2 | 0.0310 | 0.7851 (false) | NR | NR | NR | 0.0990 | 0.3825 (false) | NR | NR | NR | -0.2277 | 0.0422 (true) | 0.0658 | 0.5617 (false) | -0.2935 | -0.2324 | 0.0380 (true) | 0.0664 | 0.5584 (false) | -0.2988 |
| formula_1 | -0.2167 | 0.0041 (true) | -0.0144 | 0.8507 (false) | -0.2023 | -0.1806 | 0.0171 (true) | -0.0144 | 0.8507 (false) | -0.1662 | -0.1165 | 0.1258 (false) | -0.1075 | 0.1580 (false) | -0.0090 | -0.1203 | 0.1139 (false) | -0.1168 | 0.1249 (false) | -0.0035 |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | -0.2780 | 0.2641 (false) | NR | NR | NR | -0.2945 | 0.2355 (false) | NR |
| network_1 | -0.1757 | 0.1953 (false) | NR | NR | NR | -0.0904 | 0.5077 (false) | NR | NR | NR | -0.1805 | 0.1832 (false) | NR | NR | NR | -0.1777 | 0.1900 (false) | NR | NR | NR |
| orchestra | -0.6695 | 2.31e-06 (true) | -0.0940 | 0.5639 (false) | -0.5755 | -0.4723 | 0.0021 (true) | -0.1056 | 0.5165 (false) | -0.3667 | -0.3200 | 0.0441 (true) | 0.0216 | 0.8948 (false) | -0.3416 | -0.3062 | 0.0547 (false) | 0.0293 | 0.8577 (false) | -0.3355 |
| pets_1 | 0.0835 | 0.5990 (false) | NR | NR | NR | 0.0796 | 0.6162 (false) | NR | NR | NR | -0.2452 | 0.1176 (false) | -0.0050 | 0.9748 (false) | -0.2402 | -0.2891 | 0.0633 (false) | 0.0464 | 0.7704 (false) | -0.3355 |
| poker_player | 0.0256 | 0.8752 (false) | NR | NR | NR | 0.0256 | 0.8752 (false) | NR | NR | NR | 0.1996 | 0.2169 (false) | 0.3244 | 0.0411 (true) | -0.1248 | 0.2249 | 0.1630 (false) | 0.3387 | 0.0325 (true) | -0.1139 |
| real_estate_properties | -0.3906 | 0.6094 (false) | NR | NR | NR | 0.0000 | 1.0000 (false) | NR | NR | NR | -0.2294 | 0.7706 (false) | NR | NR | NR | 0.0000 | 1.0000 (false) | NR | NR | NR |
| singer | 0.0891 | 0.6397 (false) | NR | NR | NR | 0.0891 | 0.6397 (false) | NR | NR | NR | -0.2428 | 0.1961 (false) | -0.1760 | 0.3523 (false) | -0.0668 | -0.1849 | 0.3281 (false) | -0.1588 | 0.4019 (false) | -0.0261 |
| student_transcripts_tracking | -0.4202 | 0.0001 (true) | NR | NR | NR | -0.3350 | 0.0027 (true) | NR | NR | NR | -0.2432 | 0.0319 (true) | NR | NR | NR | -0.2226 | 0.0501 (false) | NR | NR | NR |
| superhero | -0.5408 | 3.67e-11 (true) | NR | NR | NR | -0.5066 | 9.05e-10 (true) | NR | NR | NR | 0.0315 | 0.7231 (false) | 0.0336 | 0.7053 (false) | -0.0021 | 0.0135 | 0.8792 (false) | 0.0545 | 0.5394 (false) | -0.0410 |
| toxicology | -0.1026 | 0.2193 (false) | NR | NR | NR | -0.0613 | 0.4641 (false) | NR | NR | NR | -0.2007 | 0.0155 (true) | NR | NR | NR | -0.2283 | 0.0058 (true) | NR | NR | NR |
| tvshow | -0.3393 | 0.0070 (true) | NR | NR | NR | -0.2223 | 0.0824 (false) | NR | NR | NR | -0.1165 | 0.3671 (false) | -0.0467 | 0.7186 (false) | -0.0698 | -0.1286 | 0.3191 (false) | -0.0901 | 0.4861 (false) | -0.0385 |
| voter_1 | -0.3121 | 0.2574 (false) | NR | NR | NR | -0.1394 | 0.6203 (false) | NR | NR | NR | -0.3737 | 0.1701 (false) | NR | NR | NR | -0.3770 | 0.1660 (false) | NR | NR | NR |
| **MODEL VERDICT** | **-0.3246** | **6.90e-52 (true)** | **-0.0496** | **0.0242 (true)** | **-0.2750** | **-0.2434** | **3.06e-29 (true)** | **-0.0533** | **0.0154 (true)** | **-0.1901** | **-0.1986** | **8.10e-20 (true)** | **-0.0566** | **0.0102 (true)** | **-0.1421** | **-0.2110** | **3.34e-22 (true)** | **-0.0526** | **0.0168 (true)** | **-0.1583** |

