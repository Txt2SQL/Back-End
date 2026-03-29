"""
Spider evaluation runner for QueryOrchestrator.

Loads Spider dev examples and table metadata, builds a text-based schema for a
selected database, then runs all configured query models concurrently. Each
generated SQL query is evaluated through the Spider execution evaluator in a
subprocess that exits with:

- 0 when execution matches the gold query
- 1 when execution does not match
"""

import argparse
import json
import os
import queue
import re
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from enum import Enum

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import QUERY_MODELS, SPIDER_DATA, TESTS_DIR, TIMEOUT_PER_REQUEST, SPIDER_REPO, INPUT_DIR
from src.classes.RAG_service.query_store import QueryStore
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.domain_states import QuerySession, QueryStatus, Schema, SchemaSource
from src.classes.logger import LoggerManager
from src.classes.llm_factory import LLMFactory
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from tests.output_object import RequestResult
from tests.test_sql_generation import empty_tmp_dir, printer_thread, create_output_dir, ThreadSafeQueryStore


TMP_DIR = TESTS_DIR / "tmp"
SPIDER_DEV_PATH = SPIDER_DATA / "dev.json"
SPIDER_TABLES_PATH = SPIDER_DATA / "tables.json"
SPIDER_DB_DIR = SPIDER_DATA / "database"
EVAL_FILE = INPUT_DIR / "evaluation_scripts" / "evaluation.py"
NLTK_DATA_DIR = TMP_DIR / "nltk_data"
_nltk_setup_lock = threading.Lock()
_nltk_setup_done = False

LoggerManager.setup_project_logger()
main_logger = LoggerManager.get_logger("spider_test")


class ComparisonResult(Enum):
    EXACT_MATCH = "exact_match"
    SUPERSET_COLUMNS_MATCH = "superset_columns_match"
    SET_MATCH = "set_match"
    PARTIAL_MATCH = "partial_match"
    ROW_COUNT_MISMATCH = "row_count_mismatch"
    NO_MATCH = "no_match"

@dataclass
class SpiderEvaluationReport:
    exec_result: subprocess.CompletedProcess[str]
    execution_accuracy: Optional[float]
    report_file: Path

@dataclass
class SQLiteExecutionReport:
    sql: str
    rows: Optional[list[tuple]]
    error: Optional[str]

@dataclass
class LLMJudgeReport:
    verdict: str
    reason: str
    raw_response: str

def _extract_metric(output: str, metric_name: str) -> Optional[float]:
    for line in output.splitlines():
        if line.strip().startswith(metric_name):
            numbers = re.findall(r"[0-9]*\.?[0-9]+", line)
            if numbers:
                return float(numbers[-1])
    return None


def custom_execution_compare(gold_result, pred_result):

    def normalize_value(v):
        if v is None:
            return None
        if isinstance(v, float):
            return round(v, 6)
        return str(v).strip()

    def normalize_row(row):
        return tuple(normalize_value(v) for v in row)

    gold_norm = [normalize_row(r) for r in gold_result]
    pred_norm = [normalize_row(r) for r in pred_result]

    # 1. exact match (order-insensitive)
    if sorted(pred_norm) == sorted(gold_norm):
        return ComparisonResult.EXACT_MATCH

    # 2. row count mismatch
    if len(pred_norm) != len(gold_norm):
        return ComparisonResult.ROW_COUNT_MISMATCH

    # 3. superset columns
    gold_width = len(gold_norm[0])
    pred_projected = [row[:gold_width] for row in pred_norm]

    if sorted(pred_projected) == sorted(gold_norm):
        return ComparisonResult.SUPERSET_COLUMNS_MATCH

    # 4. set match
    if set(pred_norm) == set(gold_norm):
        return ComparisonResult.SET_MATCH

    # 5. partial match
    intersection = set(pred_norm) & set(gold_norm)
    ratio = len(intersection) / max(len(gold_norm), 1)

    if ratio > 0.8:
        return ComparisonResult.PARTIAL_MATCH

    return ComparisonResult.NO_MATCH


def _is_custom_match(result: ComparisonResult) -> bool:
    return result in {
        ComparisonResult.EXACT_MATCH,
        ComparisonResult.SUPERSET_COLUMNS_MATCH,
        ComparisonResult.SET_MATCH,
    }

def _write_eval_artifacts(
    report_file: Path,
    gold_sql: str,
    predicted_sql: str,
    result: subprocess.CompletedProcess[str],
) -> None:
    sections = [
        "=== Gold SQL ===",
        gold_sql.strip(),
        "",
        "=== Predicted SQL ===",
        predicted_sql.strip(),
        "",
        "=== Spider exec stdout ===",
        (result.stdout or "").strip(),
        "",
        "=== Spider exec stderr ===",
        (result.stderr or "").strip(),
        "",
    ]
    report_file.write_text("\n".join(sections), encoding="utf-8")


def _write_combined_report(report_file: Path, sections: list[tuple[str, str]]) -> None:
    rendered_sections: list[str] = []
    for title, content in sections:
        rendered_sections.append(f"=== {title} ===")
        rendered_sections.append(content.strip() if content.strip() else "(empty)")
        rendered_sections.append("")
    report_file.write_text("\n".join(rendered_sections), encoding="utf-8")


def _build_eval_summary(report: SpiderEvaluationReport) -> str:
    parts = [
        (
            "Spider evaluation summary: "
            f"execution_accuracy={report.execution_accuracy if report.execution_accuracy is not None else 'N/A'}, "
            f"report_file={report.report_file}"
        )
    ]

    if report.exec_result.stdout.strip():
        parts.append("=== Spider exec stdout ===")
        parts.append(report.exec_result.stdout.strip())
    if report.exec_result.stderr.strip():
        parts.append("=== Spider exec stderr ===")
        parts.append(report.exec_result.stderr.strip())

    return "\n".join(parts)


def _build_spider_summary(report: SpiderEvaluationReport) -> str:
    parts = [
        f"execution_accuracy={report.execution_accuracy if report.execution_accuracy is not None else 'N/A'}",
    ]
    if report.exec_result.stdout.strip():
        parts.append("stdout:")
        parts.append(report.exec_result.stdout.strip())
    if report.exec_result.stderr.strip():
        parts.append("stderr:")
        parts.append(report.exec_result.stderr.strip())
    return "\n".join(parts)


def _build_custom_compare_summary(
    sqlite_file: Path,
    gold_exec: Optional[SQLiteExecutionReport],
    pred_exec: Optional[SQLiteExecutionReport],
    custom_result: Optional[ComparisonResult],
) -> str:
    parts = [f"sqlite_file={sqlite_file}"]

    if gold_exec is None:
        parts.append("gold_execution=not_run")
    else:
        parts.append("gold_execution:")
        parts.append(_format_sqlite_execution(gold_exec))

    if pred_exec is None:
        parts.append("predicted_execution=not_run")
    else:
        parts.append("predicted_execution:")
        parts.append(_format_sqlite_execution(pred_exec))

    parts.append(
        f"comparison_result={custom_result.value if custom_result is not None else 'not_run'}"
    )
    return "\n".join(parts)


def _build_llm_verdict_summary(llm_judge_report: Optional[LLMJudgeReport]) -> str:
    if llm_judge_report is None:
        return "not_run"
    return "\n".join(
        [
            f"verdict={llm_judge_report.verdict}",
            f"reason={llm_judge_report.reason}",
            "raw_response:",
            llm_judge_report.raw_response.strip() if llm_judge_report.raw_response.strip() else "(empty)",
        ]
    )


def _normalize_sql_for_spider(sql: str) -> str:
    return " ".join(sql.split())


def _execute_sqlite_query(sqlite_file: Path, sql: str) -> SQLiteExecutionReport:
    normalized_sql = _normalize_sql_for_spider(sql)
    conn = sqlite3.connect(sqlite_file)
    try:
        cursor = conn.cursor()
        cursor.execute(normalized_sql)
        rows = cursor.fetchall()
        return SQLiteExecutionReport(sql=normalized_sql, rows=rows, error=None)
    except Exception as exc:
        return SQLiteExecutionReport(sql=normalized_sql, rows=None, error=str(exc))
    finally:
        conn.close()


def _format_sqlite_execution(report: SQLiteExecutionReport, row_limit: int = 20) -> str:
    parts = [f"SQL: {report.sql}"]
    if report.error is not None:
        parts.append(f"Error: {report.error}")
        return "\n".join(parts)

    rows = report.rows or []
    parts.append(f"Row count: {len(rows)}")
    preview = rows[:row_limit]
    parts.append(f"Rows preview ({len(preview)} shown): {preview}")
    if len(rows) > row_limit:
        parts.append(f"Additional rows omitted: {len(rows) - row_limit}")
    return "\n".join(parts)


def _build_llm_judge_prompt(
    question: str,
    database_name: str,
    gold_report: SQLiteExecutionReport,
    pred_report: SQLiteExecutionReport,
) -> str:
    return f"""
You are judging whether a predicted SQL query should be considered correct for a Spider-style text-to-SQL example.

Database id: {database_name}
Question: {question}

Gold query:
{gold_report.sql}

Gold query result:
{gold_report.rows if gold_report.error is None else f"ERROR: {gold_report.error}"}

Predicted query:
{pred_report.sql}

Predicted query result:
{pred_report.rows if pred_report.error is None else f"ERROR: {pred_report.error}"}

Decide whether the predicted query is semantically correct relative to the gold query and the observed execution results.

Return JSON only in this format:
{{"verdict":"correct"|"incorrect","reason":"short explanation"}}
""".strip()


def _run_llm_judge(
    question: str,
    database_name: str,
    gold_report: SQLiteExecutionReport,
    pred_report: SQLiteExecutionReport,
) -> LLMJudgeReport:
    judge = LLMFactory.create(QUERY_MODELS["Qwen3-coder-next"])
    response = judge.generate(
        _build_llm_judge_prompt(
            question=question,
            database_name=database_name,
            gold_report=gold_report,
            pred_report=pred_report,
        )
    )

    verdict = "incorrect"
    reason = response.strip()

    try:
        parsed = json.loads(response)
        verdict = str(parsed.get("verdict", "incorrect")).strip().lower()
        reason = str(parsed.get("reason", response)).strip()
    except Exception:
        lowered = response.lower()
        if '"verdict":"correct"' in lowered or '"verdict": "correct"' in lowered:
            verdict = "correct"
        elif re.search(r"\bcorrect\b", lowered) and not re.search(r"\bincorrect\b", lowered):
            verdict = "correct"

    return LLMJudgeReport(verdict=verdict, reason=reason, raw_response=response)


def _build_nltk_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("NLTK_DATA", "").strip()
    search_paths = [str(NLTK_DATA_DIR)]
    if existing:
        search_paths.append(existing)
    env["NLTK_DATA"] = os.pathsep.join(search_paths)
    return env


def _ensure_nltk_tokenizers(logger) -> None:
    global _nltk_setup_done

    if _nltk_setup_done:
        return

    with _nltk_setup_lock:
        if _nltk_setup_done:
            return

        NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)
        env = _build_nltk_env()

        check_result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import nltk; "
                    "nltk.data.find('tokenizers/punkt_tab/english'); "
                    "nltk.data.find('tokenizers/punkt')"
                ),
            ],
            cwd=SPIDER_REPO,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

        if check_result.returncode != 0:
            logger.info("Downloading NLTK tokenizer data into %s", NLTK_DATA_DIR)
            download_result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import nltk; "
                        f"download_dir = r'{NLTK_DATA_DIR}'; "
                        "ok = True; "
                        "ok = nltk.download('punkt_tab', download_dir=download_dir, quiet=True) and ok; "
                        "ok = nltk.download('punkt', download_dir=download_dir, quiet=True) and ok; "
                        "raise SystemExit(0 if ok else 1)"
                    ),
                ],
                cwd=SPIDER_REPO,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )

            if download_result.returncode != 0:
                logger.warning(
                    "Failed to provision NLTK tokenizer data. stdout=%s stderr=%s",
                    download_result.stdout.strip(),
                    download_result.stderr.strip(),
                )
            else:
                logger.info("NLTK tokenizer data ready in %s", NLTK_DATA_DIR)
        else:
            logger.info("NLTK tokenizer data already available")

        _nltk_setup_done = True


def spider_schema_to_internal(spider_schema: dict) -> dict:
    tables = spider_schema["table_names_original"]
    columns = spider_schema["column_names_original"]
    column_types = spider_schema["column_types"]
    primary_keys = set(spider_schema["primary_keys"])
    foreign_keys = spider_schema["foreign_keys"]

    type_map = {
        "text": "TEXT",
        "number": "INT",
        "time": "DATETIME",
        "boolean": "BOOLEAN",
    }

    db = {table: [] for table in tables}

    for idx, ((table_id, col_name), col_type) in enumerate(zip(columns, column_types)):
        if table_id == -1:
            continue

        table_name = tables[table_id]
        constraints = []

        if idx in primary_keys:
            constraints.append("PRIMARY KEY")

        db[table_name].append(
            {
                "name": col_name,
                "type": type_map.get(col_type, "TEXT"),
                "constraints": constraints,
            }
        )

    for fk_col, ref_col in foreign_keys:
        fk_table_id, fk_name = columns[fk_col]
        ref_table_id, ref_name = columns[ref_col]

        fk_table = tables[fk_table_id]
        ref_table = tables[ref_table_id]

        for col in db[fk_table]:
            if col["name"] == fk_name:
                col["constraints"].append(
                    f"FOREIGN KEY REFERENCES {ref_table}({ref_name})"
                )

    return {
        "tables": [
            {
                "name": table_name,
                "columns": cols,
            }
            for table_name, cols in db.items()
        ]
    }


def load_spider_dataset() -> tuple[List[dict], List[dict]]:
    with SPIDER_DEV_PATH.open("r", encoding="utf-8") as f:
        spider_data = json.load(f)

    with SPIDER_TABLES_PATH.open("r", encoding="utf-8") as f:
        spider_tables = json.load(f)

    return spider_data, spider_tables


def print_database_table_counts(spider_tables: List[dict]) -> List[dict]:
    ordered_tables = sorted(spider_tables, key=lambda item: item["db_id"])
    print("Available Spider databases:")
    for entry in ordered_tables:
        print(f"{entry['db_id']} {len(entry['table_names'])}")
    return ordered_tables


def select_database(spider_tables: List[dict], database_name: str | None = None) -> str:
    ordered_tables = print_database_table_counts(spider_tables)
    db_names = [entry["db_id"] for entry in ordered_tables]

    if database_name is not None:
        if database_name not in db_names:
            raise ValueError(f"Unknown Spider database: {database_name}")
        print(f"Using database: {database_name}")
        return database_name

    while True:
        choice = input("Select database by name: ").strip()
        if choice in db_names:
            print(f"Using database: {choice}")
            return choice
        print("Invalid database name. Try again.")


def build_spider_schema(
    database_name: str,
    tables_by_db: dict[str, dict],
) -> tuple[Schema, SchemaStore]:
    spider_schema = tables_by_db[database_name]
    converted_schema = spider_schema_to_internal(spider_schema)

    schema = Schema(
        database_name=database_name,
        schema_source=SchemaSource.TEXT,
        path=TESTS_DIR / "tmp",
    )
    schema.parse_response(converted_schema)

    schema_store = SchemaStore(TMP_DIR / "vector_stores")
    schema_store.add_schema(schema)

    return schema, schema_store


def evaluate_with_spider(
    database_name: str,
    request_index: int,
    model_key: str,
    gold_sql: str,
    predicted_sql: str,
    logs_dir: Path,
) -> SpiderEvaluationReport:
    eval_dir = logs_dir / "spider_eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    eval_env = _build_nltk_env()

    model_slug = QUERY_MODELS[model_key]["log_file"]
    report_file = eval_dir / f"{request_index:02d}_{model_slug}_evaluation.log"
    tmp_eval_dir = TMP_DIR / "spider_eval_inputs"
    tmp_eval_dir.mkdir(parents=True, exist_ok=True)
    gold_file = tmp_eval_dir / f"{request_index:02d}_{model_slug}_gold.sql"
    pred_file = tmp_eval_dir / f"{request_index:02d}_{model_slug}_pred.sql"
    normalized_gold_sql = _normalize_sql_for_spider(gold_sql)
    normalized_predicted_sql = _normalize_sql_for_spider(predicted_sql)

    def run_evaluation(eval_type: str) -> subprocess.CompletedProcess[str]:
        gold_file.write_text(f"{normalized_gold_sql}\t{database_name}\n", encoding="utf-8")
        pred_file.write_text(f"{normalized_predicted_sql}\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(EVAL_FILE),
                "--gold",
                str(gold_file),
                "--pred",
                str(pred_file),
                "--etype",
                eval_type,
                "--db",
                str(SPIDER_DB_DIR),
                "--table",
                str(SPIDER_TABLES_PATH),
            ],
            cwd=SPIDER_REPO,
            capture_output=True,
            text=True,
            check=False,
            env=eval_env,
        )
        _write_eval_artifacts(report_file, normalized_gold_sql, normalized_predicted_sql, result)
        gold_file.unlink(missing_ok=True)
        pred_file.unlink(missing_ok=True)
        return result

    exec_result = run_evaluation("exec")

    return SpiderEvaluationReport(
        exec_result=exec_result,
        execution_accuracy=_extract_metric(exec_result.stdout, "execution"),
        report_file=report_file,
    )


def text_generator_thread(
    database_name: str,
    model_key: str,
    requests: List[dict],
    result_queue: queue.Queue,
    schema_store: SchemaStore,
    query_store: ThreadSafeQueryStore,
    logs_dir: Path,
    schema: Schema,
) -> None:
    """
    Runs a single Spider model on all given requests concurrently,
    writes per-request result files, and produces a summary statistics file.
    """
    log_name = QUERY_MODELS[model_key]["log_file"]
    log_file = logs_dir / f"{log_name}.log"

    logger = LoggerManager.get_logger(name=f"spider_thread_{log_name}", log_file=log_file)
    LoggerManager.set_thread_logger(logger)

    try:
        _ensure_nltk_tokenizers(logger)
        logger.info(
            "Started Spider generator thread for model=%s schema_source=%s schema_path=%s",
            model_key,
            schema.source.value,
            schema.file_path,
        )

        for idx, request in enumerate(requests, start=1):
            question = request["question"]
            gold_sql = request["query"]

            LoggerManager.set_request_index(f"[Request: {idx}]")
            logger.info("Processing Spider request for db=%s: %s", database_name, question)

            start_time = time.time()

            try:
                orch = QueryOrchestrator(
                    database_name=database_name,
                    schema_store=schema_store,
                    model_name=model_key,
                    database_client=None,
                    query_store=query_store,
                    max_attempts=3,
                    instance_path=TMP_DIR,
                )

                result_session = orch.generation(question)

                elapsed = time.time() - start_time

                predicted_sql = result_session.sql_code or ""
                eval_result = evaluate_with_spider(
                    database_name=database_name,
                    request_index=idx,
                    model_key=model_key,
                    gold_sql=gold_sql,
                    predicted_sql=predicted_sql,
                    logs_dir=logs_dir,
                )
                eval_summary = _build_eval_summary(eval_result)
                normalized_gold_sql = _normalize_sql_for_spider(gold_sql)
                normalized_predicted_sql = _normalize_sql_for_spider(predicted_sql)
                spider_summary = _build_spider_summary(eval_result)
                sqlite_file = SPIDER_DB_DIR / database_name / f"{database_name}.sqlite"
                gold_exec: Optional[SQLiteExecutionReport] = None
                pred_exec: Optional[SQLiteExecutionReport] = None
                custom_result: Optional[ComparisonResult] = None
                llm_judge_report: Optional[LLMJudgeReport] = None

                logger.info("Spider gold SQL:\n%s", gold_sql)
                logger.info("Spider predicted SQL:\n%s", predicted_sql)
                logger.info("%s", eval_summary)

                if eval_result.exec_result.returncode != 0:
                    result_session.status = QueryStatus.RUNTIME_ERROR
                    result_session.execution_status = QueryStatus.RUNTIME_ERROR
                    result_session.execution_result = eval_summary
                    success = False
                elif eval_result.execution_accuracy == 1.0:
                    result_session.status = QueryStatus.SUCCESS
                    result_session.execution_status = QueryStatus.SUCCESS
                    result_session.execution_result = eval_summary
                    success = True
                else:
                    gold_exec = _execute_sqlite_query(sqlite_file, gold_sql)
                    pred_exec = _execute_sqlite_query(sqlite_file, predicted_sql)
                    
                    ge_formatted = _format_sqlite_execution(gold_exec)
                    pe_formatted = _format_sqlite_execution(pred_exec)

                    logger.info("Running custom SQLite comparison using %s", sqlite_file)
                    logger.info("Gold SQLite execution:\n%s", ge_formatted)
                    logger.info("Pred SQLite execution:\n%s", pe_formatted)

                    if gold_exec.error is None and pred_exec.error is None:
                        custom_result = custom_execution_compare(gold_exec.rows or [], pred_exec.rows or [])
                        logger.info("Custom execution comparison result: %s", custom_result.value)

                    if custom_result is not None and _is_custom_match(custom_result):
                        result_session.status = QueryStatus.SUCCESS
                        result_session.execution_status = QueryStatus.SUCCESS
                        result_session.execution_result = (
                            f"{eval_summary}\nCustom comparison result: {custom_result.value}"
                        )
                    else:
                        llm_judge_report = _run_llm_judge(
                            question=question,
                            database_name=database_name,
                            gold_report=gold_exec,
                            pred_report=pred_exec,
                        )
                        logger.info("LLM judge verdict=%s reason=%s", llm_judge_report.verdict, llm_judge_report.reason)
                        logger.info("LLM judge raw response:\n%s", llm_judge_report.raw_response)

                        if llm_judge_report.verdict == "correct":
                            result_session.status = QueryStatus.SUCCESS
                            result_session.execution_status = QueryStatus.SUCCESS
                        else:
                            result_session.status = QueryStatus.INCORRECT
                            result_session.execution_status = QueryStatus.INCORRECT

                        custom_value = custom_result.value if custom_result is not None else "not_available"
                        result_session.execution_result = (
                            f"{eval_summary}\n"
                            f"Custom comparison result: {custom_value}\n"
                            f"LLM judge verdict: {llm_judge_report.verdict}\n"
                            f"LLM judge reason: {llm_judge_report.reason}"
                        )

                    success = True

                report_sections = [
                    ("Gold SQL", normalized_gold_sql),
                    ("Predicted SQL", normalized_predicted_sql),
                    ("Spider Summary", spider_summary),
                    (
                        "Custom compare summary",
                        _build_custom_compare_summary(
                            sqlite_file=sqlite_file,
                            gold_exec=gold_exec,
                            pred_exec=pred_exec,
                            custom_result=custom_result,
                        ),
                    ),
                    ("LLM verdict", _build_llm_verdict_summary(llm_judge_report)),
                ]
                _write_combined_report(eval_result.report_file, report_sections)

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=result_session,
                    time_taken=elapsed,
                    success=success,
                )

                logger.info(
                    "Completed Spider request with status=%s in %.2fs",
                    result_session.status.value,
                    elapsed,
                )

            except TimeoutError as exc:
                elapsed = TIMEOUT_PER_REQUEST
                logger.exception("Timeout after %ss", elapsed)

                timeout_session = QuerySession(user_request=question)
                timeout_session.execution_result = str(exc)
                timeout_session.status = QueryStatus.TIMEOUT_ERROR

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=timeout_session,
                    time_taken=elapsed,
                    success=False,
                )
            except Exception as exc:
                elapsed = time.time() - start_time
                logger.exception("Failed after %.2fs", elapsed)

                failed_session = QuerySession(user_request=question)
                failed_session.execution_result = str(exc)
                failed_session.status = QueryStatus.RUNTIME_ERROR

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=failed_session,
                    time_taken=elapsed,
                    success=False,
                )

            result_queue.put((idx, model_key, res))

        logger.info("Spider generator thread finished for model=%s", model_key)
    finally:
        LoggerManager.clear_thread_logger()


def run_spider_test(database_name: str | None, output_name: str | None = None) -> None:
    print("=== SPIDER TEST INITIALIZATION ===")
    main_logger.info("Starting Spider test")

    spider_data, spider_tables = load_spider_dataset()
    spider_db_ids = {example["db_id"] for example in spider_data}
    filtered_spider_tables = [
        entry for entry in spider_tables if entry["db_id"] in spider_db_ids
    ]
    tables_by_db = {entry["db_id"]: entry for entry in filtered_spider_tables}

    db_name = select_database(filtered_spider_tables, database_name)
    requests = [example for example in spider_data if example["db_id"] == db_name]
    request_texts = [example["question"] for example in requests]

    if not requests:
        raise ValueError(f"No Spider dev requests found for database: {db_name}")
    if db_name not in tables_by_db:
        raise ValueError(f"No Spider schema metadata found in tables.json for database: {db_name}")

    main_logger.info("Loaded %s Spider requests for db=%s", len(requests), db_name)

    output_dir, queries_dir, logs_dir = create_output_dir(db_name, output_name)
    empty_tmp_dir()

    schema, schema_store = build_spider_schema(db_name, tables_by_db)
    query_store_lock = threading.Lock()
    thread_safe_query_store = ThreadSafeQueryStore(TMP_DIR / "vector_stores", query_store_lock)

    result_queue: queue.Queue = queue.Queue()
    num_models = len(QUERY_MODELS)

    printer = threading.Thread(
        target=printer_thread,
        args=(result_queue, num_models, len(requests), queries_dir, logs_dir, request_texts),
    )
    printer.start()
    main_logger.info("Printer thread started")

    threads = []
    for model_key in QUERY_MODELS.keys():
        thread = threading.Thread(
            target=text_generator_thread,
            args=(
                db_name,
                model_key,
                requests,
                result_queue,
                schema_store,
                thread_safe_query_store,
                logs_dir,
                schema,
            ),
        )
        thread.start()
        threads.append(thread)
        main_logger.info("Generator thread started for model=%s", model_key)

    for thread in threads:
        thread.join()

    printer.join()

    print(f"All Spider threads finished. Output written to: {output_dir}")
    main_logger.info("Spider test completed. Output written to: %s", output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Spider evaluation across configured query models.")
    parser.add_argument(
        "--database-name",
        type=str,
        default=None,
        help="Spider database id to test. If omitted, the script prints all databases and prompts for one.",
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Custom name for the output run directory. Defaults to a timestamped name.",
    )
    args = parser.parse_args()

    run_spider_test(args.database_name, args.output_name)


if __name__ == "__main__":
    main()
