import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypeAlias

from config import OUTPUT_DIR, QUERY_MODELS
from src.classes.domain_states import QuerySession, Records, QueryStatus

logger = logging.getLogger(__name__)

@dataclass
class RequestResult:
    request_index: int
    model_name: str
    query_session: Optional[QuerySession]
    time_taken: float
    success: bool
    complexity: Optional[int] = None
    evaluation_method: Optional[str] = None
    evaluation_status: Optional[str] = None
    evaluation_verdict: Optional[str] = None
    evaluation_reason: Optional[str] = None

    def get_query_complexity(self) -> Optional[int]:
        logger.info("Getting query complexity for request %d, model %s: %s", self.request_index, self.model_name, self.complexity)
        return self.complexity

    def format_output_content(self, index: int) -> str:
        logger.info("Formatting output content for request %d, model %s", self.request_index, self.model_name)
        query_session = self.query_session
        lines = []

        lines.append(f"{index}. 🤖[{self.model_name}]\n")
        lines.append(f"🧮 Query:\n\n{query_session.sql_code if query_session else 'N/A'}\n")

        if self.evaluation_status == "success":
            status_label = "SUCCESS"
            logger.info("Request %d model %s: evaluation status is SUCCESS", self.request_index, self.model_name)
        elif self.evaluation_status == "incorrect":
            status_label = "INCORRECT"
            logger.info("Request %d model %s: evaluation status is INCORRECT", self.request_index, self.model_name)
        elif self.evaluation_status == "error":
            status_label = "EVAL_ERROR"
            logger.info("Request %d model %s: evaluation status is EVAL_ERROR", self.request_index, self.model_name)
        elif query_session and query_session.status:
            if query_session.status.value == "SUCCESS":
                status_label = "NOT_EVALUATED"
                logger.info("Request %d model %s: status is NOT_EVALUATED", self.request_index, self.model_name)
            else:
                status_label = query_session.status.value
                logger.info("Request %d model %s: status from query_session is %s", self.request_index, self.model_name, status_label)
        else:
            status_label = "RUNTIME_ERROR"
            logger.info("Request %d model %s: fallback status is RUNTIME_ERROR", self.request_index, self.model_name)

        execution_result = query_session.execution_result if query_session else None

        if status_label in ("SUCCESS", "INCORRECT", "NOT_EVALUATED"):
            rows_fetched = query_session.rows_fetched if query_session else None
            if rows_fetched is None and isinstance(execution_result, Records):
                rows_fetched = len(execution_result)
                logger.info("Request %d model %s: rows_fetched derived from Records: %d", self.request_index, self.model_name, rows_fetched)

            if rows_fetched is not None:
                outcome = f"({rows_fetched} rows fetched)"
                logger.info("Request %d model %s: outcome with rows_fetched=%d", self.request_index, self.model_name, rows_fetched)
            else:
                if status_label == "SUCCESS":
                    outcome = "(Query executed successfully)"
                elif status_label == "INCORRECT":
                    outcome = "(Query executed)"
                else:
                    outcome = "(Query executed, dataset evaluation not available)"
                logger.info("Request %d model %s: outcome without rows_fetched: %s", self.request_index, self.model_name, outcome)
            if status_label == "SUCCESS":
                status_emoji = "🍾SUCCESS"
            elif status_label == "INCORRECT":
                status_emoji = "⚠️INCORRECT"
            else:
                status_emoji = "✅NOT_EVALUATED"
        else:
            outcome = f"({execution_result})" if execution_result else ""
            status_emoji = f"❌{status_label}"
            logger.info("Request %d model %s: error outcome: %s", self.request_index, self.model_name, outcome)

        lines.append(f"📌 Status:\n\n{status_emoji} {outcome}\n")

        if self.evaluation_method:
            logger.info("Request %d model %s: evaluation_method=%s", self.request_index, self.model_name, self.evaluation_method)
            lines.append(f"🧪 Eval Method:\n\n{self.evaluation_method}\n")
        if self.evaluation_verdict:
            logger.info("Request %d model %s: evaluation_verdict=%s", self.request_index, self.model_name, self.evaluation_verdict)
            lines.append(f"⚖️ Eval Verdict:\n\n{self.evaluation_verdict}\n")
        if self.evaluation_reason:
            logger.info("Request %d model %s: evaluation_reason=%s", self.request_index, self.model_name, self.evaluation_reason[:100] if len(self.evaluation_reason) > 100 else self.evaluation_reason)
            lines.append(f"📝 Eval Reason:\n\n{self.evaluation_reason}\n")

        lines.append(f"⏱️ Time: {self.time_taken:.2f}s")
        logger.info("Request %d model %s: format_output_content completed, time_taken=%.2f", self.request_index, self.model_name, self.time_taken)
        return "\n".join(lines)

ResultsByIndex: TypeAlias = Dict[int, Dict[str, RequestResult]]

DATABASE_REPORT_PATH = OUTPUT_DIR / "database_report.json"


@dataclass
class ModelStats:
    correct: int = 0
    incorrect: int = 0
    generation_correct: int = 0
    generation_incorrect: int = 0
    evaluation_correct: int = 0
    evaluation_incorrect: int = 0
    runtime: int = 0
    syntax: int = 0
    executions: int = 0
    total_time: float = 0.0
    attempts: int = 0
    count: int = 0
    not_started: int = 0
    official_evaluation: int = 0
    custom_evaluation: int = 0
    llm_judge: int = 0

    @property
    def avg_attempts(self) -> float:
        result = self.attempts / self.count if self.count > 0 else 0.0
        logger.debug("avg_attempts: attempts=%d, count=%d, result=%.2f", self.attempts, self.count, result)
        return result

    @property
    def avg_time(self) -> float:
        result = self.total_time / self.count if self.count > 0 else 0.0
        logger.debug("avg_time: total_time=%.2f, count=%d, result=%.2f", self.total_time, self.count, result)
        return result

    @property
    def success_rate(self) -> float:
        result = (self.evaluation_correct / self.executions * 100) if self.executions > 0 else 0.0
        logger.debug("success_rate: evaluation_correct=%d, executions=%d, result=%.2f%%", self.evaluation_correct, self.executions, result)
        return result

    def increment_evaluation_type(self, eval_type: Optional[str]) -> None:
        logger.info("Incrementing evaluation type: %s", eval_type)
        if eval_type == "official_evaluation":
            self.official_evaluation += 1
        elif eval_type == "custom_evaluation":
            self.custom_evaluation += 1
        elif eval_type == "llm_judge":
            self.llm_judge += 1


@dataclass
class AggregatedStats:
    total_tests: int = 0
    total_requests: int = 0
    correct_queries: int = 0
    incorrect_queries: int = 0
    runtime_errors: int = 0
    syntax_errors: int = 0
    other_errors: int = 0
    total_attempts: int = 0
    global_total_time: float = 0.0
    error_type_counts: Dict[tuple[str, str], int] = field(default_factory=dict)
    evaluation_type_counts: Dict[str, int] = field(
        default_factory=lambda: {
            "not_started": 0,
            "official_evaluation": 0,
            "custom_evaluation": 0,
            "llm_judge": 0,
        }
    )
    models: Dict[str, ModelStats] = field(default_factory=dict)


@dataclass
class ComplexityAnalysis:
    request_scores: Dict[int, Optional[float]] = field(default_factory=dict)
    average_score: Optional[float] = None


def _normalize_evaluation_method(method: Optional[str], status: Optional[str] = None) -> Optional[str]:
    logger.info("Normalizing evaluation method: method=%s, status=%s", method, status)
    if method == "dataset_eval":
        logger.info("Normalized to: official_evaluation")
        return "official_evaluation"
    if method == "llm_judge":
        logger.info("Normalized to: llm_judge")
        return "llm_judge"
    if method == "sqlite_execution":
        result = None if status == "error" else "custom_evaluation"
        logger.info("sqlite_execution with status=%s -> %s", status, result)
        return result
    if method == "custom_compare":
        logger.info("Normalized to: custom_evaluation")
        return "custom_evaluation"
    logger.info("Could not normalize, returning None")
    return None


def _extract_error_category(session: Optional[QuerySession], fallback_status: QueryStatus) -> str:
    if session and session.error_type:
        result = session.error_type.value
        logger.info("Extracted error category from session.error_type: %s", result)
        return result
    result = fallback_status.value
    logger.info("Using fallback error category: %s", result)
    return result


def aggregate_results(
    results_by_index: ResultsByIndex,
    num_requests: int,
) -> AggregatedStats:
    logger.info("Starting aggregate_results with num_requests=%d", num_requests)
    stats = AggregatedStats(
        total_requests=num_requests,
        models={model: ModelStats() for model in QUERY_MODELS.keys()},
    )
    logger.info("Initialized AggregatedStats with models: %s", list(QUERY_MODELS.keys()))

    for request_index, models_dict in results_by_index.items():
        logger.info("Processing request_index=%d with %d models", request_index, len(models_dict))
        for model, res in models_dict.items():
            logger.info("Processing request %d, model %s", request_index, model)
            stats.total_tests += 1
            model_stats = stats.models[model]
            model_stats.executions += 1

            if not res.success:
                stats.other_errors += 1
                logger.info("Request %d model %s: not successful, incrementing other_errors", request_index, model)
                continue

            query_session = res.query_session
            attempts = query_session.attempt if query_session else 0
            stats.total_attempts += attempts
            logger.info("Request %d model %s: attempts=%d", request_index, model, attempts)

            model_stats.attempts += attempts
            model_stats.total_time += res.time_taken
            stats.global_total_time += res.time_taken
            model_stats.count += 1

            evaluation_type = _normalize_evaluation_method(res.evaluation_method, res.evaluation_status)
            if evaluation_type is not None:
                stats.evaluation_type_counts[evaluation_type] += 1
                model_stats.increment_evaluation_type(evaluation_type)
                logger.info("Request %d model %s: evaluation_type=%s, count now=%d", request_index, model, evaluation_type, stats.evaluation_type_counts[evaluation_type])
            elif query_session and query_session.status != QueryStatus.SUCCESS:
                stats.evaluation_type_counts["not_started"] += 1
                model_stats.not_started += 1
                logger.info("Request %d model %s: not_started incremented, count now=%d", request_index, model, stats.evaluation_type_counts["not_started"])

            evaluation_status = res.evaluation_status
            logger.info("Request %d model %s: evaluation_status=%s", request_index, model, evaluation_status)
            if evaluation_status == "success":
                stats.correct_queries += 1
                model_stats.correct += 1
                model_stats.evaluation_correct += 1
                logger.info("Request %d model %s: correct query, total_correct=%d", request_index, model, stats.correct_queries)
            elif evaluation_status == "incorrect":
                stats.incorrect_queries += 1
                model_stats.incorrect += 1
                model_stats.evaluation_incorrect += 1
                error_category = "UNKNOWN_ERROR"
                stats.error_type_counts[(error_category, "INCORRECT")] = (
                    stats.error_type_counts.get((error_category, "INCORRECT"), 0) + 1
                )
                logger.info("Request %d model %s: incorrect query, error_category=%s", request_index, model, error_category)
            elif evaluation_status == "error":
                stats.error_type_counts[("EVALUATION_ERROR", res.evaluation_method or "unknown")] = (
                    stats.error_type_counts.get(("EVALUATION_ERROR", res.evaluation_method or "unknown"), 0) + 1
                )
                logger.info("Request %d model %s: evaluation error, method=%s", request_index, model, res.evaluation_method)

            status = query_session.status if query_session else None
            logger.info("Request %d model %s: query_session.status=%s", request_index, model, status)
            if status == QueryStatus.SUCCESS:
                model_stats.generation_correct += 1
                logger.info("Request %d model %s: generation correct", request_index, model)
            elif status == QueryStatus.INCORRECT:
                model_stats.generation_incorrect += 1
                logger.info("Request %d model %s: generation incorrect", request_index, model)
            elif status == QueryStatus.RUNTIME_ERROR:
                stats.runtime_errors += 1
                model_stats.runtime += 1
                runtime_category = _extract_error_category(query_session, QueryStatus.RUNTIME_ERROR)
                stats.error_type_counts[(runtime_category, "RUNTIME_ERROR")] = (
                    stats.error_type_counts.get((runtime_category, "RUNTIME_ERROR"), 0) + 1
                )
                logger.info("Request %d model %s: runtime error, category=%s", request_index, model, runtime_category)
            elif status == QueryStatus.SYNTAX_ERROR:
                stats.syntax_errors += 1
                model_stats.syntax += 1
                syntax_category = _extract_error_category(query_session, QueryStatus.SYNTAX_ERROR)
                stats.error_type_counts[(syntax_category, "SYNTAX_ERROR")] = (
                    stats.error_type_counts.get((syntax_category, "SYNTAX_ERROR"), 0) + 1
                )
                logger.info("Request %d model %s: syntax error, category=%s", request_index, model, syntax_category)
            elif status == QueryStatus.TIMEOUT_ERROR:
                stats.other_errors += 1
                timeout_category = _extract_error_category(query_session, QueryStatus.TIMEOUT_ERROR)
                stats.error_type_counts[(timeout_category, "TIMEOUT_ERROR")] = (
                    stats.error_type_counts.get((timeout_category, "TIMEOUT_ERROR"), 0) + 1
                )
                logger.info("Request %d model %s: timeout error, category=%s", request_index, model, timeout_category)
            elif evaluation_status not in {"success", "incorrect", "error"}:
                stats.other_errors += 1
                logger.info("Request %d model %s: other error, evaluation_status=%s", request_index, model, evaluation_status)

    logger.info("aggregate_results completed: total_tests=%d, correct=%d, incorrect=%d, runtime_errors=%d, syntax_errors=%d",
                stats.total_tests, stats.correct_queries, stats.incorrect_queries, stats.runtime_errors, stats.syntax_errors)
    return stats


def calculate_rankings(stats: AggregatedStats) -> Dict[str, List[Tuple[str, ModelStats]]]:
    logger.info("Starting calculate_rankings")
    rankings = {
        "attempts": sorted(
            stats.models.items(),
            key=lambda item: item[1].avg_attempts if item[1].count > 0 else float("inf"),
        ),
        "time": sorted(
            stats.models.items(),
            key=lambda item: item[1].avg_time if item[1].count > 0 else float("inf"),
        ),
        "status": sorted(
            stats.models.items(),
            key=lambda item: (
                -item[1].success_rate,
                -item[1].evaluation_correct,
                item[1].evaluation_incorrect,
                item[1].runtime,
                item[1].syntax,
            ),
        ),
    }
    logger.info("Attempts ranking: %s", [model for model, _ in rankings["attempts"]])
    logger.info("Time ranking: %s", [model for model, _ in rankings["time"]])
    logger.info("Status ranking: %s", [model for model, _ in rankings["status"]])
    return rankings


def _database_name_from_stats_path(stats_path: Path) -> str:
    logger.info("Extracting database name from stats_path: %s", stats_path)
    for part in reversed(stats_path.parts):
        if part.endswith("_results"):
            result = part.removesuffix("_results")
            logger.info("Found database name: %s", result)
            return result

    raise ValueError(f"Could not infer database name from stats path: {stats_path}")


def _load_database_report(report_path: Path = DATABASE_REPORT_PATH) -> List[Dict[str, Any]]:
    logger.info("Loading database report from: %s", report_path)
    if not report_path.exists():
        logger.error("Database report not found: %s", report_path)
        raise FileNotFoundError(
            f"Database report not found: {report_path}. "
            "Run tests/summarize_database.py before generating stats."
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, list):
        logger.error("Invalid database report format in %s: expected a JSON list", report_path)
        raise ValueError(f"Invalid database report format in {report_path}: expected a JSON list.")

    logger.info("Loaded database report with %d entries", len(report))
    return report


def _load_database_report_entry(
    stats_path: Path,
    dataset_name: str,
) -> Dict[str, Any]:
    logger.info("Loading database report entry for stats_path=%s, dataset_name=%s", stats_path, dataset_name)
    database_name = _database_name_from_stats_path(stats_path)
    normalized_dataset = dataset_name.lower()
    logger.info("Looking for database_name=%s, normalized_dataset=%s", database_name, normalized_dataset)

    for entry in _load_database_report():
        if not isinstance(entry, dict):
            logger.debug("Skipping non-dict entry in database report")
            continue
        if str(entry.get("dataset", "")).lower() != normalized_dataset:
            continue
        if entry.get("database_name") != database_name:
            continue
        logger.info("Found matching database report entry")
        return entry

    logger.error("Database %s for dataset %s not found in %s", database_name, normalized_dataset, DATABASE_REPORT_PATH)
    raise ValueError(
        f"Database {database_name!r} for dataset {normalized_dataset!r} not found in "
        f"{DATABASE_REPORT_PATH}."
    )


def _load_complexity_vector(
    database_report_entry: Dict[str, Any],
    num_requests: int,
) -> List[float]:
    database_name = database_report_entry.get("database_name", "unknown")
    logger.info("Loading complexity vector for database %s, num_requests=%d", database_name, num_requests)
    vector = database_report_entry.get("complexity_vector")
    if not isinstance(vector, list):
        logger.error("Missing complexity_vector for database %s", database_name)
        raise ValueError(f"Missing complexity_vector for database {database_name!r}.")
    if len(vector) != num_requests:
        logger.error("Complexity vector length mismatch for database %s: expected %d, found %d", database_name, num_requests, len(vector))
        raise ValueError(
            f"Complexity vector length mismatch for database {database_name!r}: "
            f"expected {num_requests}, found {len(vector)}."
        )

    result = [float(score) for score in vector]
    logger.info("Loaded complexity vector with %d scores", len(result))
    return result


def calculate_complexity(
    stats: AggregatedStats,
    complexity_vector: List[float],
) -> ComplexityAnalysis:
    logger.info("Calculating complexity for %d requests", stats.total_requests)
    request_scores: Dict[int, Optional[float]] = {}

    for request_index in range(1, stats.total_requests + 1):
        request_complexity = complexity_vector[request_index - 1]
        request_scores[request_index] = request_complexity

    average_score = sum(complexity_vector) / len(complexity_vector) if complexity_vector else None
    logger.info("Complexity analysis: average_score=%.4f", average_score)
    return ComplexityAnalysis(
        request_scores=request_scores,
        average_score=average_score,
    )


def _format_ascii_table(
    title: str,
    headers: List[str],
    rows: List[List[str]],
    footer: Optional[List[str]] = None,
) -> str:
    logger.info("Formatting ASCII table: %s with %d rows", title, len(rows))
    lines: List[str] = [f"\n{title}", "-" * 60]
    all_data = [headers] + rows
    if footer:
        all_data.append(footer)

    col_widths = [
        max(len(str(cell)) for cell in [row[i] for row in all_data])
        for i in range(len(headers))
    ]
    logger.debug("Column widths: %s", col_widths)

    def format_row(row: List[str]) -> str:
        return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

    lines.append(format_row(headers))
    separator = "-+-".join("-" * w for w in col_widths)
    lines.append(separator)

    for row in rows:
        lines.append(format_row(row))

    if footer:
        lines.append(separator)
        lines.append(format_row(footer))

    return "\n".join(lines)


def _detect_report_mode(stats_path: Path) -> Optional[str]:
    logger.info("Detecting report mode from stats_path: %s", stats_path)
    for part in reversed(stats_path.parts):
        normalized = part.lower()
        if normalized in {"db_conn", "database_connection", "mysql"}:
            logger.info("Detected mode: db_conn")
            return "db_conn"
        if normalized == "text":
            logger.info("Detected mode: text")
            return "text"
    logger.info("Could not detect report mode, returning None")
    return None


def _json_evaluation_label(method: Optional[str], status: Optional[str]) -> Optional[str]:
    evaluation_type = _normalize_evaluation_method(method, status)
    if evaluation_type == "official_evaluation":
        logger.debug("JSON evaluation label: official eval")
        return "official eval"
    if evaluation_type == "custom_evaluation":
        logger.debug("JSON evaluation label: custom eval")
        return "custom eval"
    if evaluation_type == "llm_judge":
        logger.debug("JSON evaluation label: llm judge")
        return "llm judge"
    logger.debug("JSON evaluation label: None")
    return None


def _has_empty_result(res: RequestResult) -> bool:
    query_session = res.query_session
    result = (
        query_session is None
        or not query_session.sql_code
        or (not res.success and query_session.status == QueryStatus.PENDING)
    )
    if result:
        logger.info("Request %d model %s: has empty result", res.request_index, res.model_name)
    return result


def _json_outcome(res: RequestResult, mode: Optional[str]) -> str:
    logger.info("Determining JSON outcome for request %d model %s, mode=%s", res.request_index, res.model_name, mode)
    query_session = res.query_session

    if _has_empty_result(res):
        logger.info("Request %d model %s: outcome=empty result", res.request_index, res.model_name)
        return "empty result"

    status = query_session.status if query_session else None
    logger.info("Request %d model %s: query_session.status=%s", res.request_index, res.model_name, status)
    if status == QueryStatus.SYNTAX_ERROR:
        logger.info("Request %d model %s: outcome=syntax error", res.request_index, res.model_name)
        return "syntax error"
    if status in {QueryStatus.RUNTIME_ERROR, QueryStatus.TIMEOUT_ERROR}:
        logger.info("Request %d model %s: outcome=runtime error", res.request_index, res.model_name)
        return "runtime error"
    if status == QueryStatus.INCORRECT:
        logger.info("Request %d model %s: outcome=incorrect gen", res.request_index, res.model_name)
        return "incorrect gen"

    if res.evaluation_status == "success":
        logger.info("Request %d model %s: outcome=correct", res.request_index, res.model_name)
        return "correct"
    if res.evaluation_status == "incorrect":
        logger.info("Request %d model %s: outcome=incorrect eval", res.request_index, res.model_name)
        return "incorrect eval"
    if res.evaluation_status == "error":
        outcome = "runtime error" if mode == "text" else "incorrect eval"
        logger.info("Request %d model %s: evaluation error, outcome=%s", res.request_index, res.model_name, outcome)
        return outcome

    if not res.success:
        outcome = "runtime error" if status == QueryStatus.RUNTIME_ERROR else "empty result"
        logger.info("Request %d model %s: not successful, outcome=%s", res.request_index, res.model_name, outcome)
        return outcome

    logger.info("Request %d model %s: outcome=incorrect gen (fallback)", res.request_index, res.model_name)
    return "incorrect gen"


def _json_error(res: RequestResult, outcome: str) -> str:
    logger.debug("Determining JSON error for request %d, outcome=%s", res.request_index, outcome)
    if outcome == "correct":
        return "C"
    if outcome == "empty result":
        return "NK"

    query_session = res.query_session
    if query_session and query_session.error_type:
        logger.debug("Request %d: error from error_type=%s", res.request_index, query_session.error_type.value)
        return query_session.error_type.value
    if query_session and query_session.status:
        logger.debug("Request %d: error from status=%s", res.request_index, query_session.status.value)
        return query_session.status.value
    if res.evaluation_status == "error":
        logger.debug("Request %d: error=EVALUATION_ERROR", res.request_index)
        return "EVALUATION_ERROR"
    if outcome in {"incorrect gen", "incorrect eval"}:
        logger.debug("Request %d: error=UNKNOWN_ERROR", res.request_index)
        return "UNKNOWN_ERROR"
    logger.debug("Request %d: error=NK (fallback)", res.request_index)
    return "NK"


def _build_statistics_json(
    results_by_index: ResultsByIndex,
    num_requests: int,
    dataset_name: str,
    stats_path: Path,
    complexity_analysis: ComplexityAnalysis,
    database_report_entry: Dict[str, Any],
) -> Dict[str, object]:
    logger.info("Building statistics JSON: dataset=%s, num_requests=%d", dataset_name, num_requests)
    mode = _detect_report_mode(stats_path)
    logger.info("Report mode: %s", mode)
    complexity_average = complexity_analysis.average_score
    logger.info("Complexity average: %s", complexity_average)

    json_report: Dict[str, object] = {
        "dataset": dataset_name,
        "num_tables": database_report_entry.get("num_tables"),
        "num_columns": database_report_entry.get("num_columns"),
        "num_requests": num_requests,
        "complexity_vector": [
            complexity_analysis.request_scores[index]
            for index in range(1, num_requests + 1)
        ],
        "complexity_average_score": round(complexity_average, 2) if complexity_average is not None else None,
        "models": {},
    }
    logger.info("JSON report metadata: num_tables=%s, num_columns=%s",
                database_report_entry.get("num_tables"), database_report_entry.get("num_columns"))

    models_report: Dict[str, object] = {}

    for model in QUERY_MODELS.keys():
        logger.info("Building JSON for model: %s", model)
        attempts: List[Optional[int]] = []
        times: List[Optional[float]] = []
        outcomes: List[Optional[str]] = []
        errors: List[Optional[str]] = []
        evaluations: List[Optional[str]] = []

        for request_index in range(1, num_requests + 1):
            res = results_by_index.get(request_index, {}).get(model)

            if res is None:
                attempts.append(None)
                times.append(None)
                outcomes.append("empty result")
                errors.append("NK")
                evaluations.append(None)
                logger.debug("Model %s request %d: no result found", model, request_index)
                continue

            query_session = res.query_session
            outcome = _json_outcome(res, mode)
            logger.debug("Model %s request %d: outcome=%s", model, request_index, outcome)

            attempts.append(query_session.attempt if query_session else None)
            times.append(round(res.time_taken, 2))
            outcomes.append(outcome)
            errors.append(_json_error(res, outcome))
            evaluations.append(_json_evaluation_label(res.evaluation_method, res.evaluation_status))

        models_report[model] = {
            "attempts": attempts,
            "times": times,
            "outcomes": outcomes,
            "errors": errors,
            "evaluation": evaluations,
        }
        logger.info("Model %s JSON built: %d outcomes", model, len(outcomes))

    json_report["models"] = models_report
    logger.info("Statistics JSON build completed")
    return json_report


def _format_summary_header(stats: AggregatedStats, complexity: ComplexityAnalysis) -> str:
    logger.info("Formatting summary header")
    total_correct_percent = (
        stats.correct_queries / stats.total_tests * 100
        if stats.total_tests > 0 else 0.0
    )
    average_complexity = (
        f"{complexity.average_score:.2f}"
        if complexity.average_score is not None
        else "N/A"
    )
    logger.info("Summary: total_requests=%d, total_tests=%d, correct_percent=%.2f%%, avg_complexity=%s",
                stats.total_requests, stats.total_tests, total_correct_percent, average_complexity)

    return "\n".join([
        "/°" * 50 + "/\n",
        "📊 TEST SUMMARY",
        "\n" + "/°" * 50 + "/",
        "",
        f"Total requests tested : {stats.total_requests}",
        f"Total model executions: {stats.total_tests}",
        f"Average complexity score: {average_complexity}",
        f"🎯 Total correct %    : {total_correct_percent:.2f}%",
        "",
    ])


def _format_rankings_table(
    rankings: Dict[str, List[Tuple[str, ModelStats]]],
    stats: AggregatedStats,
) -> str:
    logger.info("Formatting rankings table")
    total_correct_percent = (
        stats.correct_queries / stats.total_tests * 100
        if stats.total_tests > 0 else 0.0
    )
    global_avg_attempts = (
        stats.total_attempts / stats.total_tests
        if stats.total_tests > 0 else 0.0
    )
    global_avg_time = (
        stats.global_total_time / stats.total_tests
        if stats.total_tests > 0 else 0.0
    )
    logger.info("Global averages: avg_attempts=%.2f, avg_time=%.2f, correct_percent=%.2f%%",
                global_avg_attempts, global_avg_time, total_correct_percent)

    attempts_table = _format_ascii_table(
        "🏁 Attempts ranking (avg)",
        ["Rank", "Model", "Avg Attempts", "Total Attempts"],
        [
            [
                str(i + 1),
                model,
                f"{model_stats.avg_attempts:.2f}",
                f"{model_stats.attempts:.0f}",
            ]
            for i, (model, model_stats) in enumerate(rankings["attempts"])
        ],
        footer=["", "TOTAL", f"{global_avg_attempts:.2f}", f"{stats.total_attempts:.0f}"],
    )

    time_table = _format_ascii_table(
        "🏁 Time ranking (avg)",
        ["Rank", "Model", "Avg Time (s)", "Total Time (s)"],
        [
            [
                str(i + 1),
                model,
                f"{model_stats.avg_time:.2f}",
                f"{model_stats.total_time:.1f}",
            ]
            for i, (model, model_stats) in enumerate(rankings["time"])
        ],
        footer=["", "TOTAL", f"{global_avg_time:.2f}", f"{stats.global_total_time:.1f}"],
    )

    status_table = _format_ascii_table(
        "🏁 Status ranking",
        [
            "Rank",
            "Model",
            "SYNTAX",
            "RUNTIME",
            "GEN INCORRECT",
            "GEN CORRECT",
            "EVAL INCORRECT",
            "EVAL CORRECT",
            "CORRECT %",
        ],
        [
            [
                str(i + 1),
                model,
                str(model_stats.syntax),
                str(model_stats.runtime),
                str(model_stats.generation_incorrect),
                str(model_stats.generation_correct),
                str(model_stats.evaluation_incorrect),
                str(model_stats.evaluation_correct),
                f"{model_stats.success_rate:.2f}%",
            ]
            for i, (model, model_stats) in enumerate(rankings["status"])
        ],
        footer=[
            "",
            "TOTAL",
            str(stats.syntax_errors),
            str(stats.runtime_errors),
            str(sum(model_stats.generation_incorrect for model_stats in stats.models.values())),
            str(sum(model_stats.generation_correct for model_stats in stats.models.values())),
            str(stats.incorrect_queries),
            str(stats.correct_queries),
            f"{total_correct_percent:.2f}%",
        ],
    )

    logger.info("Rankings tables formatted successfully")
    return "\n".join([attempts_table, time_table, status_table])


def _format_evaluation_table(stats: AggregatedStats) -> str:
    logger.info("Formatting evaluation table")
    
    sorted_models = sorted(
        stats.models.items(),
        key=lambda item: (
            -item[1].not_started,
            -item[1].official_evaluation,
            -item[1].custom_evaluation,
            -item[1].llm_judge,
            item[0],
        ),
    )
    logger.info("Evaluation table sorted by: not_started, official, custom, llm_judge")

    evaluation_table = _format_ascii_table(
        "🏁 Evaluation table",
        ["Rank", "Model", "Not started", "Official", "Custom", "LLM Judge"],
        [
            [
                str(i + 1),
                model,
                str(model_stats.not_started),
                str(model_stats.official_evaluation),
                str(model_stats.custom_evaluation),
                str(model_stats.llm_judge),
            ]
            for i, (model, model_stats) in enumerate(sorted_models)
        ],
        footer=[
            "",
            "TOTAL",
            str(stats.evaluation_type_counts["not_started"]),
            str(stats.evaluation_type_counts["official_evaluation"]),
            str(stats.evaluation_type_counts["custom_evaluation"]),
            str(stats.evaluation_type_counts["llm_judge"]),
        ],
    )
    logger.info("Evaluation type counts: %s", stats.evaluation_type_counts)

    error_type_rows = [
        [str(i + 1), category, source_type, str(count)]
        for i, ((category, source_type), count) in enumerate(
            sorted(
                stats.error_type_counts.items(),
                key=lambda item: (-item[1], item[0][1], item[0][0]),
            )
        )
    ]
    logger.info("Error type rows: %d entries", len(error_type_rows))
    
    error_type_table = _format_ascii_table(
        "🏁 Error type ranking",
        ["Rank", "Category", "Type", "Count"],
        error_type_rows,
        footer=["", "TOTAL", "", str(sum(stats.error_type_counts.values()))],
    )
    logger.info("Total error count: %d", sum(stats.error_type_counts.values()))

    return "\n".join([evaluation_table, error_type_table])


def write_statistics_report(
    results_by_index: ResultsByIndex,
    num_requests: int,
    stats_path: Path,
    num_tables: int,
    dataset_name: str,
) -> None:
    """Aggregate statistics and write to final_stats.txt and final_stats.json."""
    logger.info("=" * 60)
    logger.info("Starting write_statistics_report")
    logger.info("Parameters: num_requests=%d, stats_path=%s, num_tables=%d, dataset_name=%s",
                num_requests, stats_path, num_tables, dataset_name)
    
    stats = aggregate_results(results_by_index, num_requests)
    logger.info("Aggregated stats completed")

    rankings = calculate_rankings(stats)
    logger.info("Rankings calculated")

    database_report_entry = _load_database_report_entry(stats_path, dataset_name)
    logger.info("Database report entry loaded")

    complexity_vector = _load_complexity_vector(database_report_entry, num_requests)
    logger.info("Complexity vector loaded")

    complexity_analysis = calculate_complexity(stats, complexity_vector)
    logger.info("Complexity analysis calculated")

    json_report = _build_statistics_json(
        results_by_index,
        num_requests,
        dataset_name,
        stats_path,
        complexity_analysis,
        database_report_entry,
    )
    logger.info("Statistics JSON built")

    best_model = rankings["status"][0][0] if rankings["status"] else "N/A"
    logger.info("Best overall model: %s", best_model)
    
    report = "\n".join([
        _format_summary_header(stats, complexity_analysis),
        _format_rankings_table(rankings, stats),
        _format_evaluation_table(stats),
        f"\n🏆 Best overall model: {best_model}",
        "=" * 60,
    ])
    logger.info("Report text generated")

    logger.info("Writing report to: %s", stats_path)
    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info("Report written successfully")

    json_path = stats_path.parent / "test_report.json"
    logger.info("Writing JSON report to: %s", json_path)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2)
    logger.info("JSON report written successfully")
    logger.info("write_statistics_report completed")
    logger.info("=" * 60)