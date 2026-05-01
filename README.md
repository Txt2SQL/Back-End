## venv dependencies

windows:

```bash
py -3.12 -m venv venv
venv\Scripts\activate
```

ubuntu:

```bash
python3 -m venv venv
source venv/bin/activate
```

## `pip install`

```bash
pip install requests mysql-connector-python Faker python-dotenv openai sqlglot langchain_openai langchain_core langchain_chroma langchain_ollama fastapi scipy nltk func_timeout
```

---

## API

```bash
uvicorn main:app --reload
```

---

## MySQL

### Host

```bash
87.9.229.214
```

### Database

```bash
supermarket
```

### Port

```bash
3306
```

### Username

```bash
webuser
```

### Password

```bash
PietroGasparini237317
```

### Connection string

```bash
mysql://webuser:PietroGasparini237317@87.9.229.214:3306/supermarket?allowPublicKeyRetrieval=true&ssl=false
```

---

## Test commands

### Custom database

```bash
python .\tests\test_sql_generation.py --database-name supermarket --mode text --output-name text
python .\tests\test_sql_generation.py --database-name hacker_news --mode text --output-name text
python .\tests\test_sql_generation.py --database-name akaunting --mode text --output-name text
python .\tests\test_sql_generation.py --database-name monica --mode text --output-name text
python .\tests\test_sql_generation.py --database-name supermarket --output-name mysql
python .\tests\test_sql_generation.py --database-name hacker_news --output-name mysql
python .\tests\test_sql_generation.py --database-name akaunting --output-name mysql
python .\tests\test_sql_generation.py --database-name monica --output-name mysql
```

### BIRD dataset

```bash
python .\tests\dataset_test.py --dataset bird --database-name california_schools --mode text
python .\tests\dataset_test.py --dataset bird --database-name financial --mode text
python .\tests\dataset_test.py --dataset bird --database-name toxicology --mode text
python .\tests\dataset_test.py --dataset bird --database-name card_games --mode text
python .\tests\dataset_test.py --dataset bird --database-name codebase_community --mode text
python .\tests\dataset_test.py --dataset bird --database-name superhero --mode text
python .\tests\dataset_test.py --dataset bird --database-name formula_1 --mode text
python .\tests\dataset_test.py --dataset bird --database-name european_football_2 --mode text
python .\tests\dataset_test.py --dataset bird --database-name thrombosis prediction --mode text
python .\tests\dataset_test.py --dataset bird --database-name student_club --mode text
python .\tests\dataset_test.py --dataset bird --database-name debit_card_specializing --mode text
```

### Spider dataset

```bash
python .\tests\dataset_test.py --dataset spider --database-name concert_singer --mode text
python .\tests\dataset_test.py --dataset spider --database-name pets_1 --mode text
python .\tests\dataset_test.py --dataset spider --database-name car_1 --mode text
python .\tests\dataset_test.py --dataset spider --database-name flight_2 --mode text
python .\tests\dataset_test.py --dataset spider --database-name employee_hire_evaluation --mode text 
python .\tests\dataset_test.py --dataset spider --database-name cre_Doc_Template_Mgt --mode text
python .\tests\dataset_test.py --dataset spider --database-name course_teach --mode text
python .\tests\dataset_test.py --dataset spider --database-name museum_visit --mode text
python .\tests\dataset_test.py --dataset spider --database-name wta_1 --mode text
python .\tests\dataset_test.py --dataset spider --database-name battle_death --mode text
python .\tests\dataset_test.py --dataset spider --database-name student_transcripts_tracking --mode text
python .\tests\dataset_test.py --dataset spider --database-name tvshow --mode text
python .\tests\dataset_test.py --dataset spider --database-name poker_player --mode text
python .\tests\dataset_test.py --dataset spider --database-name voter_1 --mode text
python .\tests\dataset_test.py --dataset spider --database-name world_1 --mode text
python .\tests\dataset_test.py --dataset spider --database-name orchestra --mode text
python .\tests\dataset_test.py --dataset spider --database-name network_1 --mode text
python .\tests\dataset_test.py --dataset spider --database-name dog_kennels --mode text
python .\tests\dataset_test.py --dataset spider --database-name singer --mode text
python .\tests\dataset_test.py --dataset spider --database-name real_estate_properties --mode text
```