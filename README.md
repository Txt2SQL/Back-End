# README

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
pip install requests mysql-connector-python Faker python-dotenv openai sqlglot langchain_openai langchain_core langchain_chroma langchain_ollama fastapi scipy
```

---

## API

```bash
uvicorn main:app --reload
```

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
python .\tests\dataset_test.py --dataset bird --database-name california_schools 
python .\tests\dataset_test.py --dataset bird --database-name financial 
python .\tests\dataset_test.py --dataset bird --database-name toxicology 
python .\tests\dataset_test.py --dataset bird --database-name card_games 
python .\tests\dataset_test.py --dataset bird --database-name codebase_community 
python .\tests\dataset_test.py --dataset bird --database-name superhero 
python .\tests\dataset_test.py --dataset bird --database-name formula_1 
python .\tests\dataset_test.py --dataset bird --database-name european_football_2 
python .\tests\dataset_test.py --dataset bird --database-name thrombosis prediction 
python .\tests\dataset_test.py --dataset bird --database-name student_club 
python .\tests\dataset_test.py --dataset bird --database-name debit_card_specializing 
```

### Spider dataset

```bash
python .\tests\dataset_test.py --dataset spider --database-name concert_singer 
python .\tests\dataset_test.py --dataset spider --database-name pets_1 
python .\tests\dataset_test.py --dataset spider --database-name car_1 
python .\tests\dataset_test.py --dataset spider --database-name flight_2 
python .\tests\dataset_test.py --dataset spider --database-name employee_hire_evaluation 
python .\tests\dataset_test.py --dataset spider --database-name cre_Doc_Template_Mgt 
python .\tests\dataset_test.py --dataset spider --database-name course_teach 
python .\tests\dataset_test.py --dataset spider --database-name museum_visit 
python .\tests\dataset_test.py --dataset spider --database-name wta_1 
python .\tests\dataset_test.py --dataset spider --database-name battle_death 
python .\tests\dataset_test.py --dataset spider --database-name student_transcripts_tracking 
python .\tests\dataset_test.py --dataset spider --database-name tvshow 
python .\tests\dataset_test.py --dataset spider --database-name poker_player 
python .\tests\dataset_test.py --dataset spider --database-name voter_1 
python .\tests\dataset_test.py --dataset spider --database-name world_1 
python .\tests\dataset_test.py --dataset spider --database-name orchestra 
python .\tests\dataset_test.py --dataset spider --database-name network_1 
python .\tests\dataset_test.py --dataset spider --database-name dog_kennels 
python .\tests\dataset_test.py --dataset spider --database-name singer 
python .\tests\dataset_test.py --dataset spider --database-name real_estate_properties 
```
