import json
import math
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeAlias

from config import QUERY_MODELS
from scipy.stats import pearsonr, spearmanr
from src.classes.domain_states.query import QuerySession, Records
from src.classes.domain_states import QueryStatus

@dataclass
class RequestResult:
    request_index: int
    model_name: str
    query_session: Optional[QuerySession]
    time_taken: float
    success: bool
    gold_query_sql: Optional[str] = None
    complexity: int = 0
    evaluation_method: Optional[str] = None
    evaluation_status: Optional[str] = None
    evaluation_verdict: Optional[str] = None
    evaluation_reason: Optional[str] = None

    def compute_query_complexity(self) -> None:
        sql = self.gold_query_sql

        if not sql:
            return

        score = 0
        score += len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE)) * 2
        score += len(re.findall(r"\b(SUM|AVG|MIN|MAX|COUNT)\s*\(", sql, re.IGNORECASE)) * 2

        if re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE):
            score += 2

        if re.search(r"\bHAVING\b", sql, re.IGNORECASE):
            score += 2

        score += len(re.findall(r"\bOVER\s*\(", sql, re.IGNORECASE)) * 3
        score += len(re.findall(r"\bSELECT\b", sql, re.IGNORECASE)) - 1
        self.complexity = score

    def get_query_complexity(self) -> Optional[int]:
        sql = self.gold_query_sql
        if not sql:
            return None

        if self.complexity == 0:
            self.compute_query_complexity()

        return self.complexity

    @staticmethod
    def complexity_level_from_score(score: float) -> str:
        if score <= 2:
            return "low"
        if score <= 5:
            return "medium"
        return "high"

    def get_complexity_level(self) -> Optional[str]:
        complexity = self.get_query_complexity()
        if complexity is None:
            return None

        return self.complexity_level_from_score(complexity)

    def format_output_content(self, index: int) -> str:
        query_session = self.query_session
        lines = []

        lines.append(f"{index}. 🤖[{self.model_name}]\n")
        lines.append(f"🧮 Query:\n\n{query_session.sql_code if query_session else 'N/A'}\n")

        if self.evaluation_status == "success":
            status_label = "SUCCESS"
        elif self.evaluation_status == "incorrect":
            status_label = "INCORRECT"
        elif self.evaluation_status == "error":
            status_label = "EVAL_ERROR"
        elif query_session and query_session.status:
            if query_session.status.value == "SUCCESS":
                status_label = "NOT_EVALUATED"
            else:
                status_label = query_session.status.value
        else:
            status_label = "RUNTIME_ERROR"

        execution_result = query_session.execution_result if query_session else None

        if status_label in ("SUCCESS", "INCORRECT", "NOT_EVALUATED"):
            rows_fetched = query_session.rows_fetched if query_session else None
            if rows_fetched is None and isinstance(execution_result, Records):
                rows_fetched = len(execution_result)

            if rows_fetched is not None:
                outcome = f"({rows_fetched} rows fetched)"
            else:
                if status_label == "SUCCESS":
                    outcome = "(Query executed successfully)"
                elif status_label == "INCORRECT":
                    outcome = "(Query executed)"
                else:
                    outcome = "(Query executed, dataset evaluation not available)"
            if status_label == "SUCCESS":
                status_emoji = "🍾SUCCESS"
            elif status_label == "INCORRECT":
                status_emoji = "⚠️INCORRECT"
            else:
                status_emoji = "✅NOT_EVALUATED"
        else:
            outcome = f"({execution_result})" if execution_result else ""
            status_emoji = f"❌{status_label}"

        lines.append(f"📌 Status:\n\n{status_emoji} {outcome}\n")

        if self.evaluation_method:
            lines.append(f"🧪 Eval Method:\n\n{self.evaluation_method}\n")
        if self.evaluation_verdict:
            lines.append(f"⚖️ Eval Verdict:\n\n{self.evaluation_verdict}\n")
        if self.evaluation_reason:
            lines.append(f"📝 Eval Reason:\n\n{self.evaluation_reason}\n")

        lines.append(f"⏱️ Time: {self.time_taken:.2f}s")
        return "\n".join(lines)

ResultsByIndex: TypeAlias = Dict[int, Dict[str, RequestResult]]

COMPLEXITY_LOW_THRESHOLD = 2
COMPLEXITY_MEDIUM_THRESHOLD = 5


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
        return self.attempts / self.count if self.count > 0 else 0.0

    @property
    def avg_time(self) -> float:
        return self.total_time / self.count if self.count > 0 else 0.0

    @property
    def success_rate(self) -> float:
        return (self.evaluation_correct / self.executions * 100) if self.executions > 0 else 0.0

    def increment_evaluation_type(self, eval_type: Optional[str]) -> None:
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
    request_levels: Dict[int, Optional[str]] = field(default_factory=dict)
    per_model_buckets: Dict[str, Dict[str, List[int]]] = field(default_factory=dict)
    global_buckets: Dict[str, List[int]] = field(default_factory=dict)


@dataclass
class CorrelationMetric:
    statistic: float
    p_value: float


@dataclass
class ModelCorrelationResults:
    attempts_pearson: Optional[CorrelationMetric] = None
    attempts_spearman: Optional[CorrelationMetric] = None
    complexity_pearson: Optional[CorrelationMetric] = None
    complexity_spearman: Optional[CorrelationMetric] = None


@dataclass
class CorrelationResults:
    global_attempts_pearson: Optional[CorrelationMetric] = None
    global_attempts_spearman: Optional[CorrelationMetric] = None
    global_complexity_pearson: Optional[CorrelationMetric] = None
    global_complexity_spearman: Optional[CorrelationMetric] = None
    per_model: Dict[str, ModelCorrelationResults] = field(default_factory=dict)


def _normalize_evaluation_method(method: Optional[str], status: Optional[str] = None) -> Optional[str]:
    if method == "dataset_eval":
        return "official_evaluation"
    if method == "llm_judge":
        return "llm_judge"
    if method == "sqlite_execution":
        return None if status == "error" else "custom_evaluation"
    if method == "custom_compare":
        return "custom_evaluation"
    return None


def _extract_error_category(session: Optional[QuerySession], fallback_status: QueryStatus) -> str:
    if session and session.error_type:
        return session.error_type.value
    return fallback_status.value


def aggregate_results(
    results_by_index: ResultsByIndex,
    num_requests: int,
) -> AggregatedStats:
    stats = AggregatedStats(
        total_requests=num_requests,
        models={model: ModelStats() for model in QUERY_MODELS.keys()},
    )

    for models_dict in results_by_index.values():
        for model, res in models_dict.items():
            stats.total_tests += 1
            model_stats = stats.models[model]
            model_stats.executions += 1

            if not res.success:
                stats.other_errors += 1
                continue

            query_session = res.query_session
            attempts = query_session.attempt if query_session else 0
            stats.total_attempts += attempts

            model_stats.attempts += attempts
            model_stats.total_time += res.time_taken
            stats.global_total_time += res.time_taken
            model_stats.count += 1

            evaluation_type = _normalize_evaluation_method(res.evaluation_method, res.evaluation_status)
            if evaluation_type is not None:
                stats.evaluation_type_counts[evaluation_type] += 1
                model_stats.increment_evaluation_type(evaluation_type)
            elif query_session and query_session.status != QueryStatus.SUCCESS:
                stats.evaluation_type_counts["not_started"] += 1
                model_stats.not_started += 1

            evaluation_status = res.evaluation_status
            if evaluation_status == "success":
                stats.correct_queries += 1
                model_stats.correct += 1
                model_stats.evaluation_correct += 1
            elif evaluation_status == "incorrect":
                stats.incorrect_queries += 1
                model_stats.incorrect += 1
                model_stats.evaluation_incorrect += 1
                error_category = "UNKNOWN_ERROR"
                stats.error_type_counts[(error_category, "INCORRECT")] = (
                    stats.error_type_counts.get((error_category, "INCORRECT"), 0) + 1
                )
            elif evaluation_status == "error":
                stats.error_type_counts[("EVALUATION_ERROR", res.evaluation_method or "unknown")] = (
                    stats.error_type_counts.get(("EVALUATION_ERROR", res.evaluation_method or "unknown"), 0) + 1
                )

            status = query_session.status if query_session else None
            if status == QueryStatus.SUCCESS:
                model_stats.generation_correct += 1
            elif status == QueryStatus.INCORRECT:
                model_stats.generation_incorrect += 1
            elif status == QueryStatus.RUNTIME_ERROR:
                stats.runtime_errors += 1
                model_stats.runtime += 1
                runtime_category = _extract_error_category(query_session, QueryStatus.RUNTIME_ERROR)
                stats.error_type_counts[(runtime_category, "RUNTIME_ERROR")] = (
                    stats.error_type_counts.get((runtime_category, "RUNTIME_ERROR"), 0) + 1
                )
            elif status == QueryStatus.SYNTAX_ERROR:
                stats.syntax_errors += 1
                model_stats.syntax += 1
                syntax_category = _extract_error_category(query_session, QueryStatus.SYNTAX_ERROR)
                stats.error_type_counts[(syntax_category, "SYNTAX_ERROR")] = (
                    stats.error_type_counts.get((syntax_category, "SYNTAX_ERROR"), 0) + 1
                )
            elif status == QueryStatus.TIMEOUT_ERROR:
                stats.other_errors += 1
                timeout_category = _extract_error_category(query_session, QueryStatus.TIMEOUT_ERROR)
                stats.error_type_counts[(timeout_category, "TIMEOUT_ERROR")] = (
                    stats.error_type_counts.get((timeout_category, "TIMEOUT_ERROR"), 0) + 1
                )
            elif evaluation_status not in {"success", "incorrect", "error"}:
                stats.other_errors += 1

    return stats


def calculate_rankings(stats: AggregatedStats) -> Dict[str, List[Tuple[str, ModelStats]]]:
    return {
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


def calculate_complexity(
    results_by_index: ResultsByIndex,
    stats: AggregatedStats,
) -> ComplexityAnalysis:
    request_scores: Dict[int, Optional[float]] = {}
    request_levels: Dict[int, Optional[str]] = {}
    per_model_buckets = {
        model: {
            "low": [],
            "medium": [],
            "high": [],
            "total": [],
        }
        for model in stats.models.keys()
    }
    global_buckets = {
        "low": [],
        "medium": [],
        "high": [],
        "total": [],
    }

    for request_index in range(1, stats.total_requests + 1):
        models_dict = results_by_index.get(request_index, {})
        correct_complexities: List[float] = []
        all_complexities: List[float] = []

        for res in models_dict.values():
            complexity = res.get_query_complexity()
            if complexity is None:
                continue

            all_complexities.append(complexity)

            if res.success and res.query_session and res.evaluation_status == "success":
                correct_complexities.append(complexity)

        request_complexity: Optional[float]
        if correct_complexities:
            request_complexity = float(random.choice(correct_complexities))
        elif all_complexities:
            request_complexity = sum(all_complexities) / len(all_complexities)
        else:
            request_complexity = None

        request_scores[request_index] = request_complexity
        request_levels[request_index] = (
            RequestResult.complexity_level_from_score(request_complexity)
            if request_complexity is not None
            else None
        )

    for request_index, models_dict in results_by_index.items():
        request_complexity = request_scores.get(request_index)
        request_level = request_levels.get(request_index)

        for model, res in models_dict.items():
            if not (res.success and res.query_session):
                continue

            success = 1 if res.evaluation_status == "success" else 0

            if request_complexity is None:
                continue

            per_model_buckets[model]["total"].append(success)
            global_buckets["total"].append(success)

            if request_level is not None:
                per_model_buckets[model][request_level].append(success)

            if request_complexity <= COMPLEXITY_LOW_THRESHOLD:
                global_buckets["low"].append(success)
            elif request_complexity <= COMPLEXITY_MEDIUM_THRESHOLD:
                global_buckets["medium"].append(success)
            else:
                global_buckets["high"].append(success)

    return ComplexityAnalysis(
        request_scores=request_scores,
        request_levels=request_levels,
        per_model_buckets=per_model_buckets,
        global_buckets=global_buckets,
    )


def calculate_correlations(
    complexity_analysis: ComplexityAnalysis,
    results_by_index: ResultsByIndex,
) -> CorrelationResults:
    def safe_corr(values: List[float], outcomes: List[int], method: str) -> Optional[CorrelationMetric]:
        if len(values) < 2 or len(outcomes) < 2:
            return None
        if len(set(values)) <= 1 or len(set(outcomes)) <= 1:
            return None

        result = pearsonr(values, outcomes) if method == "pearson" else spearmanr(values, outcomes)
        statistic = getattr(result, "statistic", None)
        pvalue = getattr(result, "pvalue", None)

        if statistic is None or pvalue is None:
            return None
        if math.isnan(statistic) or math.isnan(pvalue):
            return None

        return CorrelationMetric(statistic=float(statistic), p_value=float(pvalue))

    global_attempts: List[float] = []
    global_attempt_successes: List[int] = []
    global_complexities: List[float] = []
    global_complexity_successes: List[int] = []
    per_model_data = {
        model: {
            "attempts": [],
            "attempt_successes": [],
            "complexities": [],
            "complexity_successes": [],
        }
        for model in QUERY_MODELS.keys()
    }

    for request_index, models_dict in results_by_index.items():
        request_complexity = complexity_analysis.request_scores.get(request_index)

        for model, res in models_dict.items():
            if not (res.success and res.query_session):
                continue

            success = 1 if res.evaluation_status == "success" else 0
            attempt = float(res.query_session.attempt)

            global_attempts.append(attempt)
            global_attempt_successes.append(success)
            per_model_data[model]["attempts"].append(attempt)
            per_model_data[model]["attempt_successes"].append(success)

            if request_complexity is None:
                continue

            global_complexities.append(request_complexity)
            global_complexity_successes.append(success)
            per_model_data[model]["complexities"].append(request_complexity)
            per_model_data[model]["complexity_successes"].append(success)

    per_model = {
        model: ModelCorrelationResults(
            attempts_pearson=safe_corr(model_data["attempts"], model_data["attempt_successes"], "pearson"),
            attempts_spearman=safe_corr(model_data["attempts"], model_data["attempt_successes"], "spearman"),
            complexity_pearson=safe_corr(model_data["complexities"], model_data["complexity_successes"], "pearson"),
            complexity_spearman=safe_corr(model_data["complexities"], model_data["complexity_successes"], "spearman"),
        )
        for model, model_data in per_model_data.items()
    }

    return CorrelationResults(
        global_attempts_pearson=safe_corr(global_attempts, global_attempt_successes, "pearson"),
        global_attempts_spearman=safe_corr(global_attempts, global_attempt_successes, "spearman"),
        global_complexity_pearson=safe_corr(global_complexities, global_complexity_successes, "pearson"),
        global_complexity_spearman=safe_corr(global_complexities, global_complexity_successes, "spearman"),
        per_model=per_model,
    )


def _format_ascii_table(
    title: str,
    headers: List[str],
    rows: List[List[str]],
    footer: Optional[List[str]] = None,
) -> str:
    lines: List[str] = [f"\n{title}", "-" * 60]
    all_data = [headers] + rows
    if footer:
        all_data.append(footer)

    col_widths = [
        max(len(str(cell)) for cell in [row[i] for row in all_data])
        for i in range(len(headers))
    ]

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


def _format_success_rate(values: List[int]) -> str:
    if not values:
        return "N/A"
    return f"{(sum(values) / len(values)):.2%}"


def _format_correlation(metric: Optional[CorrelationMetric]) -> str:
    if metric is None:
        return "N/A"
    return "true" if metric.p_value < 0.05 else "false"


def _success_rate_percent(values: List[int]) -> Optional[float]:
    if not values:
        return None
    return float(sum(values) / len(values) * 100)


def _correlation_statistic(metric: Optional[CorrelationMetric]) -> Optional[float]:
    if metric is None:
        return None
    return metric.statistic


def _build_statistics_json(
    stats: AggregatedStats,
    complexity: ComplexityAnalysis,
    correlations: CorrelationResults,
) -> Dict[str, Dict[str, Dict[str, Optional[float]]]]:
    json_report: Dict[str, Dict[str, Dict[str, Optional[float]]]] = {}

    for model in QUERY_MODELS.keys():
        model_stats = stats.models[model]
        model_buckets = complexity.per_model_buckets[model]
        model_correlations = correlations.per_model[model]

        json_report[model] = {
            "attempts": {
                "avg": round(model_stats.avg_attempts, 2),
                "total": model_stats.attempts,
                "pearson": _correlation_statistic(model_correlations.attempts_pearson),
                "spearman": _correlation_statistic(model_correlations.attempts_spearman),
            },
            "time": {
                "avg": round(model_stats.avg_time, 2),
                "total": round(model_stats.total_time, 1),
            },
            "status": {
                "n_syntax": model_stats.syntax,
                "n_runtime": model_stats.runtime,
                "n_eval_correct": model_stats.evaluation_correct,
                "correct_pct": round(model_stats.success_rate, 2),
            },
            "csr": {
                "low": _success_rate_percent(model_buckets["low"]),
                "medium": _success_rate_percent(model_buckets["medium"]),
                "high": _success_rate_percent(model_buckets["high"]),
                "pearson": _correlation_statistic(model_correlations.complexity_pearson),
                "spearman": _correlation_statistic(model_correlations.complexity_spearman),
            },
        }

    return json_report


def _format_summary_header(stats: AggregatedStats, complexity: ComplexityAnalysis) -> str:
    total_correct_percent = (
        stats.correct_queries / stats.total_tests * 100
        if stats.total_tests > 0 else 0.0
    )
    request_complexity_counts = {"low": 0, "medium": 0, "high": 0}
    for level in complexity.request_levels.values():
        if level in request_complexity_counts:
            request_complexity_counts[level] += 1

    return "\n".join([
        "/°" * 50 + "/\n",
        "📊 TEST SUMMARY",
        "\n" + "/°" * 50 + "/",
        "",
        f"Total requests tested : {stats.total_requests}",
        f"Total model executions: {stats.total_tests}",
        f"🟢 Low complexity requests   : {request_complexity_counts['low']}",
        f"🟡 Medium complexity requests: {request_complexity_counts['medium']}",
        f"🔴 High complexity requests  : {request_complexity_counts['high']}",
        f"🎯 Total correct %    : {total_correct_percent:.2f}%",
        "",
    ])


def _format_rankings_table(
    rankings: Dict[str, List[Tuple[str, ModelStats]]],
    stats: AggregatedStats,
) -> str:
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

    return "\n".join([attempts_table, time_table, status_table])


def _format_evaluation_table(stats: AggregatedStats) -> str:
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
            for i, (model, model_stats) in enumerate(
                sorted(
                    stats.models.items(),
                    key=lambda item: (
                        -item[1].not_started,
                        -item[1].official_evaluation,
                        -item[1].custom_evaluation,
                        -item[1].llm_judge,
                        item[0],
                    ),
                )
            )
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

    error_type_rows = [
        [str(i + 1), category, source_type, str(count)]
        for i, ((category, source_type), count) in enumerate(
            sorted(
                stats.error_type_counts.items(),
                key=lambda item: (-item[1], item[0][1], item[0][0]),
            )
        )
    ]
    error_type_table = _format_ascii_table(
        "🏁 Error type ranking",
        ["Rank", "Category", "Type", "Count"],
        error_type_rows,
        footer=["", "TOTAL", "", str(sum(stats.error_type_counts.values()))],
    )

    return "\n".join([evaluation_table, error_type_table])


def _format_complexity_table(complexity: ComplexityAnalysis) -> str:
    complexity_rows = []
    for model in QUERY_MODELS.keys():
        model_buckets = complexity.per_model_buckets[model]
        complexity_rows.append([
            model,
            _format_success_rate(model_buckets["low"]),
            _format_success_rate(model_buckets["medium"]),
            _format_success_rate(model_buckets["high"]),
            _format_success_rate(model_buckets["total"]),
        ])

    return _format_ascii_table(
        "🏁 Complexity success rate by model",
        ["Model", "Low", "Medium", "High", "Total"],
        complexity_rows,
    )


def _format_correlations_table(correlations: CorrelationResults) -> str:
    per_model_corr_rows = []
    for model in QUERY_MODELS.keys():
        model_correlations = correlations.per_model[model]
        per_model_corr_rows.append([
            model,
            _format_correlation(model_correlations.attempts_pearson),
            _format_correlation(model_correlations.attempts_spearman),
            _format_correlation(model_correlations.complexity_pearson),
            _format_correlation(model_correlations.complexity_spearman),
        ])

    return _format_ascii_table(
        "🏁 Correlation by model",
        ["Model", "Attempts Pearson", "Attempts Spearman", "Complexity Pearson", "Complexity Spearman"],
        per_model_corr_rows,
    )


def write_statistics_report(
    results_by_index: ResultsByIndex,
    num_requests: int,
    stats_path: Path,
) -> None:
    """Aggregate statistics and write to final_stats.txt and final_stats.json."""
    stats = aggregate_results(results_by_index, num_requests)
    rankings = calculate_rankings(stats)
    complexity_analysis = calculate_complexity(results_by_index, stats)
    correlations = calculate_correlations(complexity_analysis, results_by_index)
    json_report = _build_statistics_json(stats, complexity_analysis, correlations)

    best_model = rankings["status"][0][0] if rankings["status"] else "N/A"
    report = "\n".join([
        _format_summary_header(stats, complexity_analysis),
        _format_rankings_table(rankings, stats),
        _format_evaluation_table(stats),
        _format_complexity_table(complexity_analysis),
        _format_correlations_table(correlations),
        f"\n🏆 Best overall model: {best_model}",
        "=" * 60,
    ])

    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write(report)

    json_path = stats_path.with_suffix(".json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2)
