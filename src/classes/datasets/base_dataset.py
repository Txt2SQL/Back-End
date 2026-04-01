import json, re, os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from abc import ABC, abstractmethod
from types import SimpleNamespace
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict

from src.classes.domain_states import QuerySession
from src.classes.llm_factory import LLMFactory
from src.classes.prompt_builder import PromptBuilder
from src.classes.clients import SQLiteClient
from config import DATASET_DIR, QUERY_MODELS
from config.paths import DATASET_DATA
from src.classes.logger import LoggerManager

class ComparisonResult(Enum):
    EXACT_MATCH = "exact_match"
    SUPERSET_COLUMNS_MATCH = "superset_columns_match"
    SET_MATCH = "set_match"
    PARTIAL_MATCH = "partial_match"
    ROW_COUNT_MISMATCH = "row_count_mismatch"
    NO_MATCH = "no_match"

# ---------------------------------------------------------
# 1. EVALUATION RETURN VALUES: Strongly typed dataclass
# ---------------------------------------------------------
@dataclass
class OfficialEvalReport:
    execution_accuracy: float
    official_match: bool
    returncode: int
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        """Allows fallback for base_dataset.py if it expects a dict"""
        return asdict(self)

@dataclass
class EvaluationResult:
    status: str  # "success", "incorrect", "error"
    method: str  # "dataset_eval", "sqlite_execution", "custom_compare", "llm_judge", "fallback"
    execution_accuracy: Optional[float] = None

    # dataset-level info (Spider/BIRD)
    official_eval: Optional[OfficialEvalReport] = None

    # execution reports
    gold: Optional[QuerySession] = None
    pred: Optional[QuerySession] = None

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
        
        self.db_dir = DATASET_DATA / "databases"

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)
    
    def get_requests(self, db_name: str) -> list[str]:
        """Fetch all requests (questions) for a given database."""
        return [item["question"] for item in self.dev if item["db_id"] == db_name]

    @abstractmethod
    def get_dbs(self) -> list[tuple[str, int]]:
        """Get a list of unique databases and their table counts, preserving order."""
        pass

    @abstractmethod
    def get_schema(self, db_name: str) -> dict:
        """Return the schema for a given database in a consistent format."""
        pass
    
    @abstractmethod
    def _get_gold_sql(self, db_id: str, question: str) -> str:
        """Find the gold SQL query for a given db_id and question."""
        pass

    @abstractmethod
    def _get_question_index(self, db_id: str, question: str) -> int:
        """Find the index of the question in the dev set for evaluation purposes."""
        pass
    
    def evaluation(
        self,
        predicted_query: QuerySession,
        db_id: str,
        question: str,
        model_name: str,
        log_dir: Path,
        db_client: SQLiteClient,
    ) -> EvaluationResult:
        self.logger.info(
            "Starting dataset evaluation for db_id=%s question=%r",
            db_id,
            question,
        )
        question_index = self._get_question_index(db_id=db_id, question=question)
        gold_sql = self._get_gold_sql(db_id=db_id, question=question)
        self.logger.debug("Gold SQL: %s", gold_sql)
        self.logger.debug("Predicted SQL: %s", predicted_query.sql_code)
        self.logger.debug("Resolved question index: %s", question_index)
        
        gold_query = QuerySession(sql_query=gold_sql)
        
        # Call the evaluation
        official_report = self.dataset_evaluation(
            predicted_query=predicted_query,
            gold_query=gold_query,
            db_id=db_id,
            question_index=question_index,
            model_name=model_name,
        )
        execution_accuracy = official_report.execution_accuracy
        official_match = official_report.official_match
        report_info = official_report.to_dict()

        self.logger.info(
            "Dataset evaluation finished with execution_accuracy=%s official_match=%s",
            execution_accuracy,
            official_match,
        )

        # dataset evaluation enough
        if official_match or execution_accuracy == 1.0:
            self.logger.info("Dataset evaluation returned an exact execution match")
            result = EvaluationResult(
                status="success",
                method="dataset_eval",
                execution_accuracy=execution_accuracy,
                official_eval=official_report,
            )
            self._write_evaluation_log(
                result=result,
                output_dir=log_dir,
                question_index=question_index,
                model_name=model_name,
            )
            return result

        self.logger.info("Falling back to local SQLite comparison")
        gold_exec = db_client.execute_query(gold_query)
        pred_exec = db_client.execute_query(predicted_query)

        gold_error = gold_exec.execution_result if isinstance(gold_exec.execution_result, str) else None
        pred_error = pred_exec.execution_result if isinstance(pred_exec.execution_result, str) else None

        if gold_error or pred_error:
            self.logger.warning(
                "SQLite execution failed. gold_error=%r pred_error=%r",
                gold_error,
                pred_error,
            )
            result = EvaluationResult(
                status="error",
                method="sqlite_execution",
                execution_accuracy=execution_accuracy,
                official_eval=official_report,
                gold=gold_exec,
                pred=pred_exec,
            )
            self._write_evaluation_log(
                result=result,
                output_dir=log_dir,
                question_index=question_index,
                model_name=model_name,
            )
            return result

        cmp_result = self.custom_execution_compare(
            self._extract_rows(gold_exec),
            self._extract_rows(pred_exec),
        )
        self.logger.info("Custom execution comparison result: %s", cmp_result.value)

        # acceptable match, no need for LLM judge
        if cmp_result in {
            ComparisonResult.EXACT_MATCH,
            ComparisonResult.SUPERSET_COLUMNS_MATCH,
            ComparisonResult.SET_MATCH,
        }:
            self.logger.info("Skipping LLM judge because execution comparison is acceptable")
            result = EvaluationResult(
                status="success",
                method="custom_compare",
                execution_accuracy=execution_accuracy,
                official_eval=official_report,
                comparison=cmp_result.value,
                gold=gold_exec,
                pred=pred_exec,
            )
            self._write_evaluation_log(
                result=result,
                output_dir=log_dir,
                question_index=question_index,
                model_name=model_name,
            )
            return result

        # LLM judge
        if question is not None:
            self.logger.info("Invoking LLM judge for semantic comparison")
            judge = self._run_llm_judge(
                question=question,
                database_name=db_id,
                gold_report=gold_exec,
                pred_report=pred_exec,
            )

            result = EvaluationResult(
                status="success" if judge["verdict"] == "correct" else "incorrect",
                method="llm_judge",
                execution_accuracy=execution_accuracy,
                official_eval=official_report,
                comparison=cmp_result.value,
                gold=gold_exec,
                pred=pred_exec,
                verdict=judge["verdict"],
                reason=judge["reason"],
                raw_response=judge["raw_response"],
            )
            self._write_evaluation_log(
                result=result,
                output_dir=log_dir,
                question_index=question_index,
                model_name=model_name,
            )
            return result

        # fallback
        result = EvaluationResult(
            status="incorrect",
            method="fallback",
            execution_accuracy=execution_accuracy,
            official_eval=official_report,
            official_details=report_info,
            comparison=cmp_result.value,
            gold=gold_exec,
            pred=pred_exec,
        )
        self._write_evaluation_log(
            result=result,
            output_dir=output_dir,
            question_index=question_index,
            model_name=model_name,
        )
        return result
    
    @abstractmethod
    def dataset_evaluation(
        self, 
        predicted_query: QuerySession, 
        gold_query: QuerySession, 
        db_id: str, 
        question_index: int,
        model_name: str,
    ) -> OfficialEvalReport:
        pass
    
    def custom_execution_compare(self, gold_result: list[Any], pred_result: list[Any]) -> ComparisonResult:

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
        if not gold_norm:
            return ComparisonResult.EXACT_MATCH if not pred_norm else ComparisonResult.ROW_COUNT_MISMATCH

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
    
    def _extract_rows(self, query_session: QuerySession) -> list[Any]:
        execution_result = query_session.execution_result
        if execution_result is None or isinstance(execution_result, str):
            return []
        return list(getattr(execution_result, "rows", []) or [])

    def _serialize_query_session(self, query_session: Optional[QuerySession]) -> Optional[dict[str, Any]]:
        if query_session is None:
            return None

        execution_result = query_session.execution_result
        error = execution_result if isinstance(execution_result, str) else None
        rows = [] if error else self._extract_rows(query_session)

        return {
            "sql": query_session.sql_code,
            "valid_syntax": query_session.valid_syntax,
            "rows_fetched": query_session.rows_fetched,
            "error": error,
            "rows": rows,
        }

    def _sanitize_filename_part(self, value: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "unknown"

    def _write_evaluation_log(
        self,
        result: EvaluationResult,
        output_dir: Path,
        question_index: int,
        model_name: str,
    ) -> None:
        log_dir = output_dir / "eval_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        safe_model_name = self._sanitize_filename_part(model_name)
        log_file = log_dir / f"{question_index}_{safe_model_name}.log"

        payload = {
            "dataset": self.name,
            "question_index": question_index,
            "model_name": model_name,
            "result": {
                "status": result.status,
                "method": result.method,
                "execution_accuracy": result.execution_accuracy,
                "comparison": result.comparison,
                "verdict": result.verdict,
                "reason": result.reason,
                "raw_response": result.raw_response,
            },
            "gold": self._serialize_query_session(result.gold),
            "pred": self._serialize_query_session(result.pred),
            "summary": result.summary(),
        }

        log_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    def _build_judge_report(self, query_session: QuerySession) -> SimpleNamespace:
        execution_result = query_session.execution_result
        error = execution_result if isinstance(execution_result, str) else None
        rows = [] if error else self._extract_rows(query_session)
        return SimpleNamespace(
            sql=query_session.sql_code or "",
            rows=rows,
            error=error,
        )

    def _run_llm_judge(
        self,
        question: str,
        database_name: str,
        gold_report: QuerySession,
        pred_report: QuerySession,
    ) -> dict[str, str]:
        self.logger.debug("Creating LLM judge for db_id=%s question=%r", database_name, question)
        judge = LLMFactory.create(QUERY_MODELS["Qwen3-coder-next"])
        gold_judge_report = self._build_judge_report(gold_report)
        pred_judge_report = self._build_judge_report(pred_report)
        prompt = PromptBuilder().build_llm_judge_prompt(
            question=question,
            database_name=database_name,
            gold_report=gold_judge_report,
            pred_report=pred_judge_report,
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
