import sqlite3, json, re, os, sys

from src.classes.logger import LoggerManager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from src.classes.llm_factory import LLMFactory
from src.classes.prompt_builder import PromptBuilder
from src.classes.clients import SQLiteExecutionReport
from config import DATASET_DIR, QUERY_MODELS
from config.paths import BIRD_DATA, SPIDER_DATA

class ComparisonResult(Enum):
    EXACT_MATCH = "exact_match"
    SUPERSET_COLUMNS_MATCH = "superset_columns_match"
    SET_MATCH = "set_match"
    PARTIAL_MATCH = "partial_match"
    ROW_COUNT_MISMATCH = "row_count_mismatch"
    NO_MATCH = "no_match"

@dataclass
class EvaluationResult:
    status: str  # "success", "incorrect", "error"
    method: str  # "dataset_eval", "sqlite_execution", "custom_compare", "llm_judge", "fallback"

    # dataset-level info (Spider/BIRD)
    execution_accuracy: Optional[float] = None
    official_details: Optional[object] = None

    # execution reports
    gold: Optional[SQLiteExecutionReport] = None
    pred: Optional[SQLiteExecutionReport] = None

    # comparison info
    comparison: Optional[str] = None

    # llm judge
    verdict: Optional[str] = None
    reason: Optional[str] = None
    raw_response: Optional[str] = None

    def is_success(self) -> bool:
        return self.status == "success"

    def is_error(self) -> bool:
        return self.status == "error"

    def summary(self) -> str:
        parts = [
            f"Status: {self.status}",
            f"Method: {self.method}",
        ]

        if self.execution_accuracy is not None:
            parts.append(f"Execution accuracy: {self.execution_accuracy}")

        if self.comparison:
            parts.append(f"Comparison: {self.comparison}")

        if self.verdict:
            parts.append(f"LLM verdict: {self.verdict}")

        if self.reason:
            parts.append(f"Reason: {self.reason}")

        return "\n".join(parts)

class BaseDataset(ABC):
    
    def __init__(self, name: str) -> None:
        self.name = name
        self.path = DATASET_DIR / name
        dev_file = self.path / "dev.json"
        with open(dev_file, "r", encoding="utf-8") as f:
            self.dev = json.load(f)
            
        tables_file = self.path / "tables.json"
        with open(tables_file, "r", encoding="utf-8") as f:
            self.tables = json.load(f)
        self.eval_file = self.path / "evaluation.py"
        
        if self.name == "spider":
            self.db_dir = SPIDER_DATA / "databases"
        else:
            self.db_dir = BIRD_DATA / "databases"

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)
    
    @abstractmethod
    def get_requests(self, db_name: str) -> list[str]:
        pass
    
    @abstractmethod
    def get_schema(self, db_name: str) -> dict:
        pass
    
    @abstractmethod
    def get_dbs(self) -> list[tuple[str, int]]:
        pass
    
    def _find_example(self, db_id: str, question: Optional[str] = None) -> dict:
        for example in self.dev:
            if example["db_id"] == db_id:
                if question is None or example["question"] == question:
                    return example
        raise ValueError(f"Example not found for db_id: {db_id} and question: {question}")
    
    def evaluation(
        self,
        predicted_sql: str,
        db_id: str,
        question: Optional[str] = None,
    ) -> EvaluationResult:
        self.logger.info(
            "Starting dataset evaluation for db_id=%s question=%r",
            db_id,
            question,
        )
        example = self._find_example(db_id=db_id, question=question)
        gold_sql = example["query"]
        self.logger.debug("Gold SQL: %s", gold_sql)
        self.logger.debug("Predicted SQL: %s", predicted_sql)
        
        official_report = self.dataset_evaluation(
            predicted_sql=predicted_sql,
            gold_sql=gold_sql,
            db_id=db_id,
            question=question,
        )

        execution_accuracy = official_report.get("execution_accuracy")
        official_match = bool(official_report.get("official_match"))
        self.logger.info(
            "Dataset evaluation finished with execution_accuracy=%s official_match=%s returncode=%s report_file=%s",
            execution_accuracy,
            official_match,
            official_report.get("returncode"),
            official_report.get("report_file"),
        )

        # dataset evaluation enough
        if official_match or execution_accuracy == 1.0:
            self.logger.info("Dataset evaluation returned an exact execution match")
            return EvaluationResult(
                status="success",
                method="dataset_eval",
                execution_accuracy=execution_accuracy,
                official_details=official_report,
            )

        sqlite_file = self.db_dir / db_id / f"{db_id}.sqlite"
        self.logger.info("Falling back to local SQLite comparison using %s", sqlite_file)
        gold_exec = self._execute_sqlite_query(sqlite_file, gold_sql)
        pred_exec = self._execute_sqlite_query(sqlite_file, predicted_sql)

        # ❌ Caso 2: errore esecuzione
        if gold_exec.error or pred_exec.error:
            self.logger.warning(
                "SQLite execution failed. gold_error=%r pred_error=%r",
                gold_exec.error,
                pred_exec.error,
            )
            return EvaluationResult(
                status="error",
                method="sqlite_execution",
                execution_accuracy=execution_accuracy,
                official_details=official_report,
                gold=gold_exec,
                pred=pred_exec,
            )

        cmp_result = self.custom_execution_compare(
            gold_exec.rows or [],
            pred_exec.rows or [],
        )
        self.logger.info("Custom execution comparison result: %s", cmp_result.value)

        # acceptable match, no need for LLM judge
        if cmp_result in {
            ComparisonResult.EXACT_MATCH,
            ComparisonResult.SUPERSET_COLUMNS_MATCH,
            ComparisonResult.SET_MATCH,
        }:
            self.logger.info("Skipping LLM judge because execution comparison is acceptable")
            return EvaluationResult(
                status="success",
                method="custom_compare",
                execution_accuracy=execution_accuracy,
                official_details=official_report,
                comparison=cmp_result.value,
                gold=gold_exec,
                pred=pred_exec,
            )

        # LLM judge
        if question is not None:
            self.logger.info("Invoking LLM judge for semantic comparison")
            judge = self._run_llm_judge(
                question=question,
                database_name=db_id,
                gold_report=gold_exec,
                pred_report=pred_exec,
            )

            return EvaluationResult(
                status="success" if judge["verdict"] == "correct" else "incorrect",
                method="llm_judge",
                execution_accuracy=execution_accuracy,
                official_details=official_report,
                comparison=cmp_result.value,
                gold=gold_exec,
                pred=pred_exec,
                verdict=judge["verdict"],
                reason=judge["reason"],
                raw_response=judge["raw_response"],
            )

        # fallback
        return EvaluationResult(
            status="incorrect",
            method="fallback",
            execution_accuracy=execution_accuracy,
            official_details=official_report,
            comparison=cmp_result.value,
            gold=gold_exec,
            pred=pred_exec,
        )
    
    @abstractmethod
    def dataset_evaluation(self, predicted_sql: str, gold_sql: str, db_id: str, question: Optional[str] = None) -> dict:
        pass
    
    def custom_execution_compare(self,gold_result, pred_result):

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

    def _execute_sqlite_query(self, sqlite_file: Path, sql: str) -> SQLiteExecutionReport:
        normalized_sql = self._normalize_sql(sql)
        self.logger.debug("Opening SQLite database: %s", sqlite_file)
        self.logger.debug("Executing normalized SQL: %s", normalized_sql)
        conn = sqlite3.connect(sqlite_file)
        try:
            cursor = conn.cursor()
            cursor.execute(normalized_sql)
            rows = cursor.fetchall()
            self.logger.debug("SQLite query succeeded with %d rows", len(rows))
            return SQLiteExecutionReport(sql=normalized_sql, rows=rows, error=None)
        except Exception as exc:
            self.logger.exception("SQLite query failed: %s", exc)
            return SQLiteExecutionReport(sql=normalized_sql, rows=None, error=str(exc))
        finally:
            conn.close()
            
    def _normalize_sql(self, sql: str) -> str:
        return " ".join(sql.split())
    
    def _run_llm_judge(self,
        question: str,
        database_name: str,
        gold_report: SQLiteExecutionReport,
        pred_report: SQLiteExecutionReport,
    ) -> dict:
        self.logger.debug("Creating LLM judge for db_id=%s question=%r", database_name, question)
        judge = LLMFactory.create(QUERY_MODELS["Qwen3-coder-next"])
        prompt = PromptBuilder().build_llm_judge_prompt(
            question=question,
            database_name=database_name,
            gold_report=gold_report,
            pred_report=pred_report,
        )
        response = judge.generate(prompt)
        self.logger.debug("LLM judge raw response: %s", response)

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

        return {
            "verdict": verdict,
            "reason": reason,
            "raw_response": response,
        }
