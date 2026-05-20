# Model Performance Summary: `gpt-5-mini`

**Base directory:** `C:\Users\pietr\Desktop\UniTn\Tesi\Progetto Text2SQL\Back-End\tests\output\generations`

Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.

## Status

| Database | Success db_conn | Success text | Success delta | Avg time db_conn | Avg time text | Avg time delta | Avg attempts db_conn | Avg attempts text | Avg attempts delta | Syntax db_conn | Syntax text | Syntax delta | Runtime db_conn | Runtime text | Incorrect db_conn | Incorrect text | Incorrect delta | Incorrect perc db_conn | Incorrect perc text | Incorrect perc delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | 81.25% | 31.25% | +50% | 19.87s | 9.43s | +10.44s | 1.5 | 1 | +0.5 | 0 | 0 | +0 | 0 | 11 | 3 | 0 | +3 | 18.75% | 0% | +18.75% |
| california_schools | 39.33% | 2.25% | +37.08% | 21.16s | 32.76s | -11.6s | 2 | 2.81 | -0.81 | 0 | 0 | +0 | 0 | 47 | 47 | 1 | +46 | 57.32% | 33.33% | +23.98% |
| car_1 | 60.87% | 4.35% | +56.52% | 32.31s | 12.02s | +20.29s | 1.97 | 1.01 | +0.96 | 0 | 0 | +0 | 0 | 87 | 36 | 1 | +35 | 39.13% | 20% | +19.13% |
| card_games | 39.79% | 4.19% | +35.6% | 25.55s | 10.43s | +15.12s | 2.02 | 1.03 | +0.99 | 0 | 0 | +0 | 0 | 167 | 109 | 14 | +95 | 58.92% | 63.64% | -4.72% |
| codebase_community | 48.39% | 5.38% | +43.01% | 23.78s | 8.69s | +15.08s | 2.1 | 1.02 | +1.09 | 0 | 0 | +0 | 0 | 167 | 87 | 7 | +80 | 49.15% | 41.18% | +7.98% |
| concert_singer | 84.44% | 20% | +64.44% | 23.66s | 10.68s | +12.98s | 1.76 | 1 | +0.76 | 0 | 0 | +0 | 0 | 36 | 7 | 0 | +7 | 15.56% | 0% | +15.56% |
| course_teach | 80% | 6.67% | +73.33% | 25.7s | 7.94s | +17.76s | 2.07 | 1 | +1.07 | 0 | 0 | +0 | 0 | 27 | 6 | 1 | +5 | 20% | 33.33% | -13.33% |
| cre_Doc_Template_Mgt | 84.52% | 2.38% | +82.14% | 23.3s | 7.85s | +15.45s | 1.83 | 1.02 | +0.81 | 0 | 0 | +0 | 0 | 82 | 13 | 0 | +13 | 15.48% | 0% | +15.48% |
| debit_card_specializing | 21.88% | 4.69% | +17.19% | 35.77s | 11.54s | +24.24s | 2.09 | 1 | +1.09 | 0 | 0 | +0 | 0 | 54 | 49 | 7 | +42 | 77.78% | 70% | +7.78% |
| dog_kennels | 73.17% | 7.32% | +65.85% | 19.52s | 8.21s | +11.31s | 1.78 | 1 | +0.78 | 0 | 0 | +0 | 0 | 74 | 22 | 2 | +20 | 26.83% | 25% | +1.83% |
| employee_hire_evaluation | 94.74% | 23.68% | +71.05% | 22.92s | 8.1s | +14.82s | 1.66 | 1 | +0.66 | 0 | 0 | +0 | 0 | 29 | 2 | 0 | +2 | 5.26% | 0% | +5.26% |
| european_football_2 | 53.49% | 13.95% | +39.53% | 32.57s | 12.65s | +19.92s | 1.88 | 1.04 | +0.84 | 0 | 0 | +0 | 0 | 89 | 60 | 22 | +38 | 46.51% | 55% | -8.49% |
| financial | 20.75% | 2.83% | +17.92% | 35.41s | 15.99s | +19.41s | 3.1 | 1.3 | +1.8 | 0 | 0 | +0 | 16 | 93 | 68 | 2 | +66 | 75.56% | 40% | +35.56% |
| flight_2 | 92.5% | 5% | +87.5% | 26.66s | 8.95s | +17.71s | 1.91 | 1 | +0.91 | 0 | 0 | +0 | 0 | 76 | 6 | 0 | +6 | 7.5% | 0% | +7.5% |
| formula_1 | 42.53% | 3.45% | +39.08% | 26.66s | 13.19s | +13.46s | 1.84 | 1.02 | +0.83 | 0 | 0 | +0 | 0 | 155 | 99 | 13 | +86 | 57.23% | 68.42% | -11.2% |
| museum_visit | 100% | 11.11% | +88.89% | 26.7s | 9.33s | +17.37s | 1.67 | 1 | +0.67 | 0 | 0 | +0 | 0 | 16 | 0 | 0 | +0 | 0% | 0% | +0% |
| network_1 | 67.86% | 0% | +67.86% | 18.84s | 8.08s | +10.76s | 1.7 | 1 | +0.7 | 0 | 0 | +0 | 0 | 54 | 18 | 2 | +16 | 32.14% | 100% | -67.86% |
| orchestra | 95% | 17.5% | +77.5% | 12.56s | 9.57s | +2.99s | 1.27 | 1.1 | +0.17 | 0 | 0 | +0 | 0 | 32 | 2 | 1 | +1 | 5% | 12.5% | -7.5% |
| pets_1 | 88.1% | 7.14% | +80.95% | 18.52s | 11.16s | +7.36s | 1.52 | 1 | +0.52 | 0 | 0 | +0 | 0 | 39 | 5 | 0 | +5 | 11.9% | 0% | +11.9% |
| poker_player | 97.5% | 55% | +42.5% | 9.04s | 7.87s | +1.16s | 1.02 | 1 | +0.02 | 0 | 0 | +0 | 0 | 16 | 1 | 2 | -1 | 2.5% | 8.33% | -5.83% |
| real_estate_properties | 50% | 0% | +50% | 25.89s | 7s | +18.89s | 2.75 | 1 | +1.75 | 0 | 0 | +0 | 1 | 4 | 1 | 0 | +1 | 33.33% | N/A | N/A |
| singer | 90% | 53.33% | +36.67% | 9.75s | 6.93s | +2.82s | 1.07 | 1 | +0.07 | 0 | 0 | +0 | 0 | 13 | 3 | 1 | +2 | 10% | 5.88% | +4.12% |
| student_transcripts_tracking | 60.26% | 0% | +60.26% | 27.43s | 8.31s | +19.13s | 2.15 | 1 | +1.15 | 0 | 0 | +0 | 0 | 78 | 31 | 0 | +31 | 39.74% | N/A | N/A |
| superhero | 37.98% | 6.2% | +31.78% | 32.17s | 11.14s | +21.03s | 2.82 | 1 | +1.82 | 0 | 0 | +0 | 17 | 111 | 60 | 10 | +50 | 55.05% | 55.56% | -0.51% |
| thrombosis_prediction | 12.88% | 0% | +12.88% | 22.39s | 21.86s | +0.53s | 1.93 | 2.44 | -0.5 | 0 | 0 | +0 | 0 | 105 | 142 | 5 | +137 | 87.12% | 100% | -12.88% |
| toxicology | 20% | 0% | +20% | 33.43s | 8.75s | +24.68s | 2.52 | 1.03 | +1.49 | 0 | 0 | +0 | 0 | 144 | 115 | 1 | +114 | 79.86% | 100% | -20.14% |
| tvshow | 85.48% | 12.9% | +72.58% | 18.44s | 7.25s | +11.19s | 1.89 | 1 | +0.89 | 0 | 0 | +0 | 0 | 54 | 9 | 0 | +9 | 14.52% | 0% | +14.52% |
| voter_1 | 73.33% | 0% | +73.33% | 19.2s | 7.57s | +11.63s | 2 | 1 | +1 | 0 | 0 | +0 | 0 | 15 | 4 | 0 | +4 | 26.67% | N/A | N/A |
| world_1 | 80.83% | 23.33% | +57.5% | 15.35s | 6.79s | +8.57s | 1.93 | 1 | +0.93 | 0 | 0 | +0 | 0 | 86 | 23 | 6 | +17 | 19.17% | 17.65% | +1.52% |
| wta_1 | 74.19% | 1.61% | +72.58% | 15.95s | 6.06s | +9.9s | 1.81 | 1 | +0.81 | 0 | 0 | +0 | 4 | 60 | 12 | 1 | +11 | 20.69% | 50% | -29.31% |
| **MODEL VERDICT** | **54.11%** | **7.72%** | **+46.39%** | **25.05s** | **11.58s** | **+13.47s** | **2.02** | **1.19** | **+0.83** | **0** | **0** | **+0** | **38** | **2021** | **1040** | **99** | **+941** | **44.37%** | **34.74%** | **+9.63%** |

## Attempts Correlations

| Database | Pearson stats db_conn | Pearson p-value db_conn | Pearson stats text | Pearson p-value text | Pearson delta | Spearman stats db_conn | Spearman p-value db_conn | Spearman stats text | Spearman p-value text | Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.1601 | 0.5536 (false) | NR | NR | NR | -0.1601 | 0.5536 (false) | NR | NR | NR |
| california_schools | -0.2665 | 0.0116 (true) | -0.1408 | 0.1882 (false) | -0.1257 | -0.2074 | 0.0512 (false) | -0.1464 | 0.1710 (false) | -0.0610 |
| car_1 | -0.4295 | 1.93e-05 (true) | -0.0223 | 0.8325 (false) | -0.4072 | -0.3343 | 0.0011 (true) | -0.0223 | 0.8325 (false) | -0.3119 |
| card_games | -0.1852 | 0.0103 (true) | -0.0184 | 0.8004 (false) | -0.1668 | -0.1247 | 0.0858 (false) | -0.0215 | 0.7677 (false) | -0.1032 |
| codebase_community | -0.3518 | 8.50e-07 (true) | -0.0236 | 0.7495 (false) | -0.3282 | -0.2889 | 6.35e-05 (true) | -0.0249 | 0.7364 (false) | -0.2641 |
| concert_singer | -0.4348 | 0.0028 (true) | NR | NR | NR | -0.3209 | 0.0316 (true) | NR | NR | NR |
| course_teach | -0.3887 | 0.0337 (true) | NR | NR | NR | -0.3773 | 0.0398 (true) | NR | NR | NR |
| cre_Doc_Template_Mgt | 0.0567 | 0.6085 (false) | -0.0244 | 0.8257 (false) | +0.0811 | 0.0626 | 0.5719 (false) | -0.0244 | 0.8257 (false) | +0.0869 |
| debit_card_specializing | -0.0463 | 0.7163 (false) | NR | NR | NR | 0.0066 | 0.9586 (false) | NR | NR | NR |
| dog_kennels | -0.4448 | 2.83e-05 (true) | NR | NR | NR | -0.3854 | 0.0003 (true) | NR | NR | NR |
| employee_hire_evaluation | -0.1700 | 0.3076 (false) | NR | NR | NR | -0.1700 | 0.3076 (false) | NR | NR | NR |
| european_football_2 | -0.3961 | 3.37e-06 (true) | -0.0680 | 0.4442 (false) | -0.3282 | -0.3590 | 2.95e-05 (true) | -0.0720 | 0.4173 (false) | -0.2869 |
| financial | -0.3213 | 0.0008 (true) | -0.0488 | 0.6196 (false) | -0.2725 | -0.2668 | 0.0057 (true) | -0.0488 | 0.6196 (false) | -0.2180 |
| flight_2 | 0.0310 | 0.7851 (false) | NR | NR | NR | 0.0990 | 0.3825 (false) | NR | NR | NR |
| formula_1 | -0.2167 | 0.0041 (true) | -0.0144 | 0.8507 (false) | -0.2023 | -0.1806 | 0.0171 (true) | -0.0144 | 0.8507 (false) | -0.1662 |
| museum_visit | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| network_1 | -0.1757 | 0.1953 (false) | NR | NR | NR | -0.0904 | 0.5077 (false) | NR | NR | NR |
| orchestra | -0.6695 | 2.31e-06 (true) | -0.0940 | 0.5639 (false) | -0.5755 | -0.4723 | 0.0021 (true) | -0.1056 | 0.5165 (false) | -0.3667 |
| pets_1 | 0.0835 | 0.5990 (false) | NR | NR | NR | 0.0796 | 0.6162 (false) | NR | NR | NR |
| poker_player | 0.0256 | 0.8752 (false) | NR | NR | NR | 0.0256 | 0.8752 (false) | NR | NR | NR |
| real_estate_properties | -0.3906 | 0.6094 (false) | NR | NR | NR | 0.0000 | 1.0000 (false) | NR | NR | NR |
| singer | 0.0891 | 0.6397 (false) | NR | NR | NR | 0.0891 | 0.6397 (false) | NR | NR | NR |
| student_transcripts_tracking | -0.4202 | 0.0001 (true) | NR | NR | NR | -0.3350 | 0.0027 (true) | NR | NR | NR |
| superhero | -0.4778 | 1.03e-08 (true) | NR | NR | NR | -0.4275 | 4.36e-07 (true) | NR | NR | NR |
| thrombosis_prediction | -0.1466 | 0.0619 (false) | NR | NR | NR | -0.1566 | 0.0459 (true) | NR | NR | NR |
| toxicology | -0.1026 | 0.2193 (false) | NR | NR | NR | -0.0613 | 0.4641 (false) | NR | NR | NR |
| tvshow | -0.3393 | 0.0070 (true) | NR | NR | NR | -0.2223 | 0.0824 (false) | NR | NR | NR |
| voter_1 | -0.3121 | 0.2574 (false) | NR | NR | NR | -0.1394 | 0.6203 (false) | NR | NR | NR |
| world_1 | -0.1112 | 0.2268 (false) | NR | NR | NR | -0.1810 | 0.0479 (true) | NR | NR | NR |
| wta_1 | -0.4169 | 0.0007 (true) | NR | NR | NR | -0.2538 | 0.0465 (true) | NR | NR | NR |
| **MODEL VERDICT** | **-0.3314** | **7.34e-63 (true)** | **-0.0665** | **0.0011 (true)** | **-0.2648** | **-0.2687** | **4.07e-41 (true)** | **-0.0710** | **0.0005 (true)** | **-0.1977** |

## Complexity Correlations

| Database | Pearson stats db_conn | Pearson p-value db_conn | Pearson stats text | Pearson p-value text | Pearson delta | Spearman stats db_conn | Spearman p-value db_conn | Spearman stats text | Spearman p-value text | Spearman delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| battle_death | -0.2634 | 0.3242 (false) | -0.4019 | 0.1228 (false) | +0.1384 | -0.3763 | 0.1509 (false) | -0.4224 | 0.1031 (false) | +0.0462 |
| california_schools | -0.1221 | 0.2544 (false) | -0.0805 | 0.4535 (false) | -0.0416 | -0.1019 | 0.3420 (false) | -0.0914 | 0.3940 (false) | -0.0105 |
| car_1 | -0.0399 | 0.7056 (false) | -0.0583 | 0.5808 (false) | +0.0184 | -0.0491 | 0.6421 (false) | -0.0433 | 0.6820 (false) | -0.0058 |
| card_games | -0.2279 | 0.0015 (true) | -0.0742 | 0.3076 (false) | -0.1537 | -0.2305 | 0.0013 (true) | -0.0628 | 0.3880 (false) | -0.1677 |
| codebase_community | -0.1916 | 0.0088 (true) | 0.0164 | 0.8247 (false) | -0.2079 | -0.1874 | 0.0104 (true) | 0.0713 | 0.3338 (false) | -0.2587 |
| concert_singer | -0.4872 | 0.0007 (true) | 0.0295 | 0.8473 (false) | -0.5168 | -0.4812 | 0.0008 (true) | 0.0283 | 0.8534 (false) | -0.5095 |
| course_teach | -0.3526 | 0.0560 (false) | 0.2234 | 0.2354 (false) | -0.5760 | -0.3807 | 0.0380 (true) | 0.2410 | 0.1996 (false) | -0.6216 |
| cre_Doc_Template_Mgt | -0.3148 | 0.0035 (true) | 0.2351 | 0.0313 (true) | -0.5499 | -0.3013 | 0.0054 (true) | 0.2184 | 0.0460 (true) | -0.5196 |
| debit_card_specializing | -0.2101 | 0.0956 (false) | -0.0207 | 0.8711 (false) | -0.1894 | -0.3100 | 0.0127 (true) | 0.0334 | 0.7930 (false) | -0.3434 |
| dog_kennels | -0.2548 | 0.0209 (true) | 0.0290 | 0.7960 (false) | -0.2838 | -0.2278 | 0.0396 (true) | 0.0565 | 0.6140 (false) | -0.2843 |
| employee_hire_evaluation | -0.3680 | 0.0230 (true) | -0.1631 | 0.3279 (false) | -0.2049 | -0.3283 | 0.0442 (true) | -0.1609 | 0.3345 (false) | -0.1673 |
| european_football_2 | -0.1316 | 0.1371 (false) | -0.0740 | 0.4043 (false) | -0.0576 | -0.1396 | 0.1146 (false) | -0.0973 | 0.2725 (false) | -0.0423 |
| financial | 0.0997 | 0.3094 (false) | 0.0512 | 0.6024 (false) | +0.0485 | 0.1148 | 0.2414 (false) | 0.0955 | 0.3300 (false) | +0.0192 |
| flight_2 | -0.2277 | 0.0422 (true) | 0.0658 | 0.5617 (false) | -0.2935 | -0.2324 | 0.0380 (true) | 0.0664 | 0.5584 (false) | -0.2988 |
| formula_1 | -0.1165 | 0.1258 (false) | -0.1075 | 0.1580 (false) | -0.0090 | -0.1203 | 0.1139 (false) | -0.1168 | 0.1249 (false) | -0.0035 |
| museum_visit | NR | NR | -0.2780 | 0.2641 (false) | NR | NR | NR | -0.2945 | 0.2355 (false) | NR |
| network_1 | -0.1805 | 0.1832 (false) | NR | NR | NR | -0.1777 | 0.1900 (false) | NR | NR | NR |
| orchestra | -0.3200 | 0.0441 (true) | 0.0216 | 0.8948 (false) | -0.3416 | -0.3062 | 0.0547 (false) | 0.0293 | 0.8577 (false) | -0.3355 |
| pets_1 | -0.2452 | 0.1176 (false) | -0.0050 | 0.9748 (false) | -0.2402 | -0.2891 | 0.0633 (false) | 0.0464 | 0.7704 (false) | -0.3355 |
| poker_player | 0.1996 | 0.2169 (false) | 0.3244 | 0.0411 (true) | -0.1248 | 0.2249 | 0.1630 (false) | 0.3387 | 0.0325 (true) | -0.1139 |
| real_estate_properties | -0.2294 | 0.7706 (false) | NR | NR | NR | 0.0000 | 1.0000 (false) | NR | NR | NR |
| singer | -0.2428 | 0.1961 (false) | -0.1760 | 0.3523 (false) | -0.0668 | -0.1849 | 0.3281 (false) | -0.1588 | 0.4019 (false) | -0.0261 |
| student_transcripts_tracking | -0.2432 | 0.0319 (true) | NR | NR | NR | -0.2226 | 0.0501 (false) | NR | NR | NR |
| superhero | -0.2234 | 0.0109 (true) | 0.0336 | 0.7053 (false) | -0.2570 | -0.2085 | 0.0177 (true) | 0.0545 | 0.5394 (false) | -0.2631 |
| thrombosis_prediction | -0.1166 | 0.1382 (false) | NR | NR | NR | -0.1183 | 0.1324 (false) | NR | NR | NR |
| toxicology | -0.2007 | 0.0155 (true) | NR | NR | NR | -0.2283 | 0.0058 (true) | NR | NR | NR |
| tvshow | -0.1165 | 0.3671 (false) | -0.0467 | 0.7186 (false) | -0.0698 | -0.1286 | 0.3191 (false) | -0.0901 | 0.4861 (false) | -0.0385 |
| voter_1 | -0.3737 | 0.1701 (false) | NR | NR | NR | -0.3770 | 0.1660 (false) | NR | NR | NR |
| world_1 | -0.0726 | 0.4305 (false) | -0.1039 | 0.2588 (false) | +0.0313 | -0.1318 | 0.1514 (false) | -0.1330 | 0.1474 (false) | +0.0013 |
| wta_1 | -0.2178 | 0.0891 (false) | -0.0418 | 0.7470 (false) | -0.1760 | -0.2087 | 0.1036 (false) | -0.0370 | 0.7754 (false) | -0.1717 |
| **MODEL VERDICT** | **-0.1968** | **1.86e-22 (true)** | **-0.0582** | **0.0043 (true)** | **-0.1386** | **-0.2124** | **5.59e-26 (true)** | **-0.0588** | **0.0039 (true)** | **-0.1535** |

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
| **MODEL VERDICT** | **-0.1682** | **9.41e-17 (true)** | **-0.0397** | **0.0515 (false)** | **-0.1285** | **-0.1253** | **6.76e-10 (true)** | **-0.0141** | **0.4878 (false)** | **-0.1111** |

