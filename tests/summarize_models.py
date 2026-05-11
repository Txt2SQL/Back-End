import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from scipy import stats


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import OUTPUT_DIR


GENERATIONS_DIR = OUTPUT_DIR / "generations"
MODEL_SUMMARIES_DIR = OUTPUT_DIR / "model_summaries"
DATABASE_SUMMARY_FILENAME = "databases.md"
DB_CONN_MODE = "db_conn"
TEXT_MODE = "text"
MODE_DIR_CANDIDATES = {
    DB_CONN_MODE: ("db_conn", "mysql"),
    TEXT_MODE: ("text",),
}
CORRECT_OUTCOME = "correct"
INCORRECT_OUTCOMES = {"incorrect gen", "incorrect eval"}
LOW_COMPLEXITY_MAX = 3
MEDIUM_COMPLEXITY_MAX = 6


@dataclass
class ModeReport:
    dataset: str | None
    num_tables: int | None
    num_columns: int | None
    num_requests: int
    complexity_vector: list[float | None]
    models: dict[str, dict[str, list[Any]]]


@dataclass
class DatabaseReports:
    database: str
    modes: dict[str, ModeReport]


@dataclass
class ModeStatus:
    total: int
    success: int
    avg_time: float | None
    avg_attempts: float | None
    syntax: int
    runtime: int
    incorrect: int

    @property
    def success_rate(self) -> float | None:
        if self.total == 0:
            return None
        return self.success / self.total * 100


@dataclass
class CorrelationResult:
    stat: float | None
    pvalue: float | None
    not_detectable: bool = False


def _load_report(path: Path) -> ModeReport:
    raw = json.loads(path.read_text(encoding="utf-8"))
    complexity_vector = [
        float(value) if _is_number(value) else None
        for value in raw.get("complexity_vector", [])
    ]

    return ModeReport(
        dataset=raw.get("dataset"),
        num_tables=_optional_int(raw.get("num_tables")),
        num_columns=_optional_int(raw.get("num_columns")),
        num_requests=_optional_int(raw.get("num_requests")) or 0,
        complexity_vector=complexity_vector,
        models=raw.get("models", {}),
    )


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _read_database_reports(base_dir: Path) -> list[DatabaseReports]:
    databases: list[DatabaseReports] = []

    for db_dir in sorted(base_dir.glob("*_results")):
        if not db_dir.is_dir():
            continue

        modes: dict[str, ModeReport] = {}
        for mode, candidates in MODE_DIR_CANDIDATES.items():
            for candidate in candidates:
                report_path = db_dir / candidate / "test_report.json"
                if report_path.exists():
                    modes[mode] = _load_report(report_path)
                    break

        if modes:
            databases.append(
                DatabaseReports(
                    database=db_dir.name.removesuffix("_results"),
                    modes=modes,
                )
            )

    return databases


def _all_models(databases: Iterable[DatabaseReports]) -> list[str]:
    models: set[str] = set()
    for database_reports in databases:
        for report in database_reports.modes.values():
            models.update(report.models.keys())
    return sorted(models, key=str.lower)


def _model_payload(report: ModeReport | None, model: str) -> dict[str, list[Any]] | None:
    if report is None:
        return None
    payload = report.models.get(model)
    return payload if isinstance(payload, dict) else None


def _status_for(report: ModeReport | None, model: str) -> ModeStatus:
    payload = _model_payload(report, model)
    if payload is None:
        return ModeStatus(0, 0, None, None, 0, 0, 0)

    outcomes = _as_list(payload.get("outcomes"))
    times = _numeric_values(payload.get("times"))
    attempts = _numeric_values(payload.get("attempts"))

    return ModeStatus(
        total=len(outcomes),
        success=sum(1 for outcome in outcomes if outcome == CORRECT_OUTCOME),
        avg_time=_average(times),
        avg_attempts=_average(attempts),
        syntax=sum(1 for outcome in outcomes if outcome == "syntax error"),
        runtime=sum(1 for outcome in outcomes if outcome == "runtime error"),
        incorrect=sum(1 for outcome in outcomes if outcome in INCORRECT_OUTCOMES),
    )


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _numeric_values(value: Any) -> list[float]:
    return [float(item) for item in _as_list(value) if _is_number(item)]


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _success_vector(payload: dict[str, list[Any]]) -> list[int]:
    return [1 if outcome == CORRECT_OUTCOME else 0 for outcome in _as_list(payload.get("outcomes"))]


def _aligned_numeric_and_success(
    values: list[Any],
    outcomes: list[Any],
) -> tuple[list[float], list[int]]:
    x_values: list[float] = []
    y_values: list[int] = []

    for value, outcome in zip(values, outcomes):
        if not _is_number(value):
            continue
        x_values.append(float(value))
        y_values.append(1 if outcome == CORRECT_OUTCOME else 0)

    return x_values, y_values


def _correlation(x_values: list[float], y_values: list[int], method: str) -> CorrelationResult:
    if len(x_values) < 2 or len(y_values) < 2:
        return CorrelationResult(None, None)
    if len(set(x_values)) < 2 or len(set(y_values)) < 2:
        return CorrelationResult(None, None, not_detectable=True)

    if method == "pearson":
        result = stats.pearsonr(x_values, y_values)
    elif method == "spearman":
        result = stats.spearmanr(x_values, y_values)
    else:
        raise ValueError(f"Unknown correlation method: {method}")

    statistic = float(result.statistic) # pyright: ignore[reportAttributeAccessIssue]
    pvalue = float(result.pvalue) # pyright: ignore[reportAttributeAccessIssue]
    if not math.isfinite(statistic) or not math.isfinite(pvalue):
        return CorrelationResult(None, None, not_detectable=True)
    return CorrelationResult(statistic, pvalue)


def _attempts_correlation(report: ModeReport | None, model: str, method: str) -> CorrelationResult:
    payload = _model_payload(report, model)
    if payload is None:
        return CorrelationResult(None, None)

    x_values, y_values = _aligned_numeric_and_success(
        _as_list(payload.get("attempts")),
        _as_list(payload.get("outcomes")),
    )
    return _correlation(x_values, y_values, method)


def _complexity_correlation(report: ModeReport | None, model: str, method: str) -> CorrelationResult:
    payload = _model_payload(report, model)
    if payload is None:
        return CorrelationResult(None, None)

    outcomes = _as_list(payload.get("outcomes"))
    x_values, y_values = _aligned_numeric_and_success(report.complexity_vector if report else [], outcomes)
    return _correlation(x_values, y_values, method)


def _collect_status_values(
    databases: list[DatabaseReports],
    model: str,
    mode: str,
) -> ModeStatus:
    total = 0
    success = 0
    times: list[float] = []
    attempts: list[float] = []
    syntax = 0
    runtime = 0
    incorrect = 0

    for database_reports in databases:
        report = database_reports.modes.get(mode)
        payload = _model_payload(report, model)
        if payload is None:
            continue

        outcomes = _as_list(payload.get("outcomes"))
        total += len(outcomes)
        success += sum(1 for outcome in outcomes if outcome == CORRECT_OUTCOME)
        times.extend(_numeric_values(payload.get("times")))
        attempts.extend(_numeric_values(payload.get("attempts")))
        syntax += sum(1 for outcome in outcomes if outcome == "syntax error")
        runtime += sum(1 for outcome in outcomes if outcome == "runtime error")
        incorrect += sum(1 for outcome in outcomes if outcome in INCORRECT_OUTCOMES)

    return ModeStatus(
        total=total,
        success=success,
        avg_time=_average(times),
        avg_attempts=_average(attempts),
        syntax=syntax,
        runtime=runtime,
        incorrect=incorrect,
    )


def _metadata_report(database_reports: DatabaseReports) -> ModeReport:
    return (
        database_reports.modes.get(DB_CONN_MODE)
        or database_reports.modes.get(TEXT_MODE)
        or next(iter(database_reports.modes.values()))
    )


def _mode_success_rate(report: ModeReport | None) -> float | None:
    if report is None:
        return None

    total = 0
    success = 0
    for payload in report.models.values():
        if not isinstance(payload, dict):
            continue
        outcomes = _as_list(payload.get("outcomes"))
        total += len(outcomes)
        success += sum(1 for outcome in outcomes if outcome == CORRECT_OUTCOME)

    if total == 0:
        return None
    return success / total * 100


def _complexity_triplet(complexity_vector: list[float | None]) -> tuple[int, int, int]:
    low = 0
    medium = 0
    high = 0

    for score in complexity_vector:
        if score is None:
            continue
        if score <= LOW_COMPLEXITY_MAX:
            low += 1
        elif score <= MEDIUM_COMPLEXITY_MAX:
            medium += 1
        else:
            high += 1

    return low, medium, high


def _format_triplet(triplet: tuple[int, int, int]) -> str:
    low, medium, high = triplet
    return f"({low}/{medium}/{high})"


def _database_overview_headers() -> list[str]:
    return [
        "Dataset",
        "Database",
        "Tables",
        "Columns",
        "avg columns",
        "Requests",
        "Triplet score",
        "Complexity score",
        "Success rate text",
        "Success rate db_conn",
    ]


def _database_overview_row(database_reports: DatabaseReports) -> list[str]:
    metadata = _metadata_report(database_reports)
    num_tables = metadata.num_tables
    num_columns = metadata.num_columns
    avg_columns = (
        num_columns / num_tables
        if num_columns is not None and num_tables not in (None, 0)
        else None
    )
    complexity_scores = [score for score in metadata.complexity_vector if score is not None]

    return [
        metadata.dataset or "N/A",
        database_reports.database,
        str(num_tables) if num_tables is not None else "N/A",
        str(num_columns) if num_columns is not None else "N/A",
        _format_number(avg_columns),
        str(metadata.num_requests),
        _format_triplet(_complexity_triplet(metadata.complexity_vector)),
        _format_number(_average(complexity_scores)),
        _format_percent(_mode_success_rate(database_reports.modes.get(TEXT_MODE))),
        _format_percent(_mode_success_rate(database_reports.modes.get(DB_CONN_MODE))),
    ]


def _render_database_overview(databases: list[DatabaseReports], base_dir: Path) -> str:
    rows = [_database_overview_row(database_reports) for database_reports in databases]
    return "\n\n".join(
        [
            "# Database Overview",
            f"**Base directory:** `{base_dir}`",
            (
                "Triplet score is formatted as `(low/medium/high)` with thresholds "
                f"`low <= {LOW_COMPLEXITY_MAX}`, "
                f"`medium <= {MEDIUM_COMPLEXITY_MAX}`, "
                f"`high > {MEDIUM_COMPLEXITY_MAX}`."
            ),
            _markdown_table(_database_overview_headers(), rows),
            "",
        ]
    )


def _collect_correlation_values(
    databases: list[DatabaseReports],
    model: str,
    mode: str,
    source: str,
) -> tuple[list[float], list[int]]:
    x_values: list[float] = []
    y_values: list[int] = []

    for database_reports in databases:
        report = database_reports.modes.get(mode)
        payload = _model_payload(report, model)
        if report is None or payload is None:
            continue

        values = payload.get("attempts") if source == "attempts" else report.complexity_vector
        x_part, y_part = _aligned_numeric_and_success(
            _as_list(values),
            _as_list(payload.get("outcomes")),
        )
        x_values.extend(x_part)
        y_values.extend(y_part)

    return x_values, y_values


def _status_row(database: str, db_status: ModeStatus, text_status: ModeStatus) -> list[str]:
    return [
        database,
        _format_percent(db_status.success_rate),
        _format_percent(text_status.success_rate),
        _format_delta_percent(_delta(db_status.success_rate, text_status.success_rate)),
        _format_seconds(db_status.avg_time),
        _format_seconds(text_status.avg_time),
        _format_delta_seconds(_delta(db_status.avg_time, text_status.avg_time)),
        _format_number(db_status.avg_attempts),
        _format_number(text_status.avg_attempts),
        _format_delta_number(_delta(db_status.avg_attempts, text_status.avg_attempts)),
        str(db_status.syntax),
        str(text_status.syntax),
        _format_delta_int(db_status.syntax - text_status.syntax),
        str(db_status.runtime),
        str(text_status.runtime),
        str(db_status.incorrect),
        str(text_status.incorrect),
        _format_delta_int(db_status.incorrect - text_status.incorrect),
    ]


def _correlation_row(database: str, db_report: ModeReport | None, text_report: ModeReport | None, model: str) -> list[str]:
    attempts_pearson_db = _attempts_correlation(db_report, model, "pearson")
    attempts_pearson_text = _attempts_correlation(text_report, model, "pearson")
    attempts_spearman_db = _attempts_correlation(db_report, model, "spearman")
    attempts_spearman_text = _attempts_correlation(text_report, model, "spearman")
    complexity_pearson_db = _complexity_correlation(db_report, model, "pearson")
    complexity_pearson_text = _complexity_correlation(text_report, model, "pearson")
    complexity_spearman_db = _complexity_correlation(db_report, model, "spearman")
    complexity_spearman_text = _complexity_correlation(text_report, model, "spearman")

    return _format_correlation_row(
        database,
        attempts_pearson_db,
        attempts_pearson_text,
        attempts_spearman_db,
        attempts_spearman_text,
        complexity_pearson_db,
        complexity_pearson_text,
        complexity_spearman_db,
        complexity_spearman_text,
    )


def _format_correlation_row(
    database: str,
    attempts_pearson_db: CorrelationResult,
    attempts_pearson_text: CorrelationResult,
    attempts_spearman_db: CorrelationResult,
    attempts_spearman_text: CorrelationResult,
    complexity_pearson_db: CorrelationResult,
    complexity_pearson_text: CorrelationResult,
    complexity_spearman_db: CorrelationResult,
    complexity_spearman_text: CorrelationResult,
) -> list[str]:
    return [
        database,
        _format_stat(attempts_pearson_db),
        _format_pvalue(attempts_pearson_db),
        _format_stat(attempts_pearson_text),
        _format_pvalue(attempts_pearson_text),
        _format_delta_stat(attempts_pearson_db, attempts_pearson_text),
        _format_stat(attempts_spearman_db),
        _format_pvalue(attempts_spearman_db),
        _format_stat(attempts_spearman_text),
        _format_pvalue(attempts_spearman_text),
        _format_delta_stat(attempts_spearman_db, attempts_spearman_text),
        _format_stat(complexity_pearson_db),
        _format_pvalue(complexity_pearson_db),
        _format_stat(complexity_pearson_text),
        _format_pvalue(complexity_pearson_text),
        _format_delta_stat(complexity_pearson_db, complexity_pearson_text),
        _format_stat(complexity_spearman_db),
        _format_pvalue(complexity_spearman_db),
        _format_stat(complexity_spearman_text),
        _format_pvalue(complexity_spearman_text),
        _format_delta_stat(complexity_spearman_db, complexity_spearman_text),
    ]


def _model_verdict_correlation_row(databases: list[DatabaseReports], model: str) -> list[str]:
    results: dict[tuple[str, str, str], CorrelationResult] = {}

    for source in ("attempts", "complexity"):
        for method in ("pearson", "spearman"):
            for mode in (DB_CONN_MODE, TEXT_MODE):
                x_values, y_values = _collect_correlation_values(databases, model, mode, source)
                results[(source, method, mode)] = _correlation(x_values, y_values, method)

    return _format_correlation_row(
        "**MODEL VERDICT**",
        results[("attempts", "pearson", DB_CONN_MODE)],
        results[("attempts", "pearson", TEXT_MODE)],
        results[("attempts", "spearman", DB_CONN_MODE)],
        results[("attempts", "spearman", TEXT_MODE)],
        results[("complexity", "pearson", DB_CONN_MODE)],
        results[("complexity", "pearson", TEXT_MODE)],
        results[("complexity", "spearman", DB_CONN_MODE)],
        results[("complexity", "spearman", TEXT_MODE)],
    )


def _delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _format_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{_trim_float(value)}%"


def _format_delta_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{_format_signed(value)}%"


def _format_seconds(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{_trim_float(value)}s"


def _format_delta_seconds(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{_format_signed(value)}s"


def _format_number(value: float | None) -> str:
    if value is None:
        return "N/A"
    return _trim_float(value)


def _format_delta_number(value: float | None) -> str:
    if value is None:
        return "N/A"
    return _format_signed(value)


def _format_delta_int(value: int) -> str:
    return f"{value:+d}"


def _format_stat(result: CorrelationResult) -> str:
    if result.not_detectable:
        return "NR"
    if result.stat is None:
        return "N/A"
    return f"{result.stat:.4f}"


def _format_pvalue(result: CorrelationResult) -> str:
    if result.not_detectable:
        return "NR"
    if result.pvalue is None:
        return "N/A"
    formatted = f"{result.pvalue:.2e}" if result.pvalue < 0.0001 else f"{result.pvalue:.4f}"
    return f"{formatted} ({str(result.pvalue < 0.05).lower()})"


def _format_delta_stat(left: CorrelationResult, right: CorrelationResult) -> str:
    if (left.stat is None and not left.not_detectable) or (right.stat is None and not right.not_detectable):
        return "N/A"
    if left.not_detectable or right.not_detectable:
        return "NR"
    value = _delta(left.stat, right.stat)
    if value is None:
        return "N/A"
    return f"{value:+.4f}"


def _format_signed(value: float) -> str:
    rounded = round(value, 2)
    if rounded == 0:
        rounded = 0.0
    sign = "+" if rounded >= 0 else ""
    return f"{sign}{_trim_float(rounded)}"


def _trim_float(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _filename_for_model(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("_") + ".md"


def _status_headers() -> list[str]:
    return [
        "Database",
        "Success db_conn",
        "Success text",
        "Success delta",
        "Avg time db_conn",
        "Avg time text",
        "Avg time delta",
        "Avg attempts db_conn",
        "Avg attempts text",
        "Avg attempts delta",
        "Syntax db_conn",
        "Syntax text",
        "Syntax delta",
        "Runtime db_conn",
        "Runtime text",
        "Incorrect db_conn",
        "Incorrect text",
        "Incorrect delta",
    ]


def _correlation_headers() -> list[str]:
    return [
        "Database",
        "Attempts Pearson stats db_conn",
        "Attempts Pearson p-value db_conn",
        "Attempts Pearson stats text",
        "Attempts Pearson p-value text",
        "Attempts Pearson delta",
        "Attempts Spearman stats db_conn",
        "Attempts Spearman p-value db_conn",
        "Attempts Spearman stats text",
        "Attempts Spearman p-value text",
        "Attempts Spearman delta",
        "Complexity Pearson stats db_conn",
        "Complexity Pearson p-value db_conn",
        "Complexity Pearson stats text",
        "Complexity Pearson p-value text",
        "Complexity Pearson delta",
        "Complexity Spearman stats db_conn",
        "Complexity Spearman p-value db_conn",
        "Complexity Spearman stats text",
        "Complexity Spearman p-value text",
        "Complexity Spearman delta",
    ]


def _render_model_summary(model: str, databases: list[DatabaseReports], base_dir: Path) -> str:
    status_rows: list[list[str]] = []
    correlation_rows: list[list[str]] = []

    for database_reports in databases:
        db_report = database_reports.modes.get(DB_CONN_MODE)
        text_report = database_reports.modes.get(TEXT_MODE)
        status_rows.append(
            _status_row(
                database_reports.database,
                _status_for(db_report, model),
                _status_for(text_report, model),
            )
        )
        correlation_rows.append(
            _correlation_row(database_reports.database, db_report, text_report, model)
        )

    db_status_total = _collect_status_values(databases, model, DB_CONN_MODE)
    text_status_total = _collect_status_values(databases, model, TEXT_MODE)
    status_rows.append(_bold_row(_status_row("MODEL VERDICT", db_status_total, text_status_total)))
    correlation_rows.append(_bold_row(_model_verdict_correlation_row(databases, model)))

    return "\n\n".join(
        [
            f"# Model Performance Summary: `{model}`",
            f"**Base directory:** `{base_dir}`",
            "Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.",
            "## Status",
            _markdown_table(_status_headers(), status_rows),
            "## Correlations",
            _markdown_table(_correlation_headers(), correlation_rows),
            "",
        ]
    )


def _bold_row(row: list[str]) -> list[str]:
    return [cell if cell.startswith("**") and cell.endswith("**") else f"**{cell}**" for cell in row]


def write_model_summaries(base_dir: Path, output_dir: Path) -> list[Path]:
    databases = _read_database_reports(base_dir)
    if not databases:
        raise FileNotFoundError(f"No test_report.json files found under {base_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    for model in _all_models(databases):
        output_path = output_dir / _filename_for_model(model)
        output_path.write_text(
            _render_model_summary(model, databases, base_dir),
            encoding="utf-8",
        )
        written_paths.append(output_path)

    database_summary_path = output_dir / DATABASE_SUMMARY_FILENAME
    database_summary_path.write_text(
        _render_database_overview(databases, base_dir),
        encoding="utf-8",
    )
    written_paths.append(database_summary_path)

    return written_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate one Markdown summary per model from test_report.json files."
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=GENERATIONS_DIR,
        help="Directory containing *_results folders. Defaults to tests/output/generations.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=MODEL_SUMMARIES_DIR,
        help="Directory where model Markdown summaries are written. Defaults to tests/output/model_summaries.",
    )
    args = parser.parse_args()

    written_paths = write_model_summaries(args.base_dir, args.output_dir)
    model_summary_count = sum(1 for path in written_paths if path.name != DATABASE_SUMMARY_FILENAME)
    print(
        f"Wrote {model_summary_count} model summaries and "
        f"{DATABASE_SUMMARY_FILENAME} to: {args.output_dir}"
    )


if __name__ == "__main__":
    main()
