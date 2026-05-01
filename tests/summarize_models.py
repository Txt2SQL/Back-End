import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


ModeReports = Dict[str, Dict[str, Any]]

MODES = ("db_conn", "text")


def _safe_get(data: Optional[Dict[str, Any]], *keys: str, default: Any = "N/A") -> Any:
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"Warning: could not parse {path}. Skipping it.")
        return None


def _db_name(results_dir: Path) -> str:
    name = results_dir.name
    return name.removesuffix("_results")


def _format_value(value: Any, suffix: str = "") -> str:
    if value is None or value == "N/A":
        return "N/A"
    if isinstance(value, float):
        if value.is_integer():
            value = int(value)
        else:
            value = round(value, 2)
    return f"{value}{suffix}"


def _format_delta(left: Any, right: Any, suffix: str = "") -> str:
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return "N/A"

    delta = left - right
    if isinstance(delta, float) and not delta.is_integer():
        delta_text = f"{delta:+.2f}"
    else:
        delta_text = f"{int(delta):+d}"
    return f"{delta_text}{suffix}"


def _format_float(value: Any, digits: int = 4) -> str:
    if not isinstance(value, (int, float)):
        return "N/A"
    return f"{float(value):.{digits}f}"


def _format_float_delta(left: Any, right: Any, digits: int = 4) -> str:
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return "N/A"
    return f"{float(left - right):+.{digits}f}"


def _as_number(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _correlation_value(model_data: Optional[Dict[str, Any]], section: str, metric: str) -> Any:
    value = _safe_get(model_data, section, metric)
    if isinstance(value, dict):
        return value.get("float", "N/A")
    return value


def _metric_pair(
    db_conn_model: Optional[Dict[str, Any]],
    text_model: Optional[Dict[str, Any]],
    *keys: str,
    suffix: str = "",
) -> list[str]:
    db_value = _safe_get(db_conn_model, *keys)
    text_value = _safe_get(text_model, *keys)
    return [
        _format_value(db_value, suffix),
        _format_value(text_value, suffix),
        _format_delta(db_value, text_value, suffix),
    ]


def _correlation_pair(
    db_conn_model: Optional[Dict[str, Any]],
    text_model: Optional[Dict[str, Any]],
    section: str,
    metric: str,
) -> list[str]:
    db_value = _correlation_value(db_conn_model, section, metric)
    text_value = _correlation_value(text_model, section, metric)
    return [
        _format_float(db_value),
        _format_float(text_value),
        _format_float_delta(db_value, text_value),
    ]


def _complexity_triplet(model_data: Optional[Dict[str, Any]]) -> str:
    low = _safe_get(model_data, "complexity", "low")
    medium = _safe_get(model_data, "complexity", "medium")
    high = _safe_get(model_data, "complexity", "high")

    if "N/A" in {low, medium, high}:
        return "N/A"

    return f"{low}/{medium}/{high}"


def _add_mode_totals(totals: Dict[str, Dict[str, float]], mode: str, report: Dict[str, Any], model_data: Dict[str, Any]) -> None:
    mode_totals = totals[mode]
    requests = _as_number(_safe_get(report, "num_requests"))
    weight = requests if requests and requests > 0 else 1.0

    success_pct = _as_number(_safe_get(model_data, "status", "correct_pct"))
    avg_time = _as_number(_safe_get(model_data, "time", "avg"))
    avg_attempts = _as_number(_safe_get(model_data, "attempts", "avg"))

    if success_pct is not None:
        mode_totals["success_weighted"] += success_pct * weight
        mode_totals["success_weight"] += weight
    if avg_time is not None:
        mode_totals["time_weighted"] += avg_time * weight
        mode_totals["time_weight"] += weight
    if avg_attempts is not None:
        mode_totals["attempts_weighted"] += avg_attempts * weight
        mode_totals["attempts_weight"] += weight

    for key, path in {
        "attempts_pearson": ("attempts", "pearson"),
        "attempts_spearman": ("attempts", "spearman"),
        "complexity_pearson": ("complexity", "pearson"),
        "complexity_spearman": ("complexity", "spearman"),
    }.items():
        value = _as_number(_correlation_value(model_data, *path))
        if value is not None:
            mode_totals[f"{key}_sum"] += value
            mode_totals[f"{key}_count"] += 1

    for key, path in {
        "eval_correct": ("status", "n_eval_correct"),
        "syntax": ("status", "n_syntax"),
        "runtime": ("status", "n_runtime"),
        "complexity_low": ("complexity", "low"),
        "complexity_medium": ("complexity", "medium"),
        "complexity_high": ("complexity", "high"),
    }.items():
        value = _as_number(_safe_get(model_data, *path))
        if value is not None:
            mode_totals[key] += value


def _weighted_average(totals: Dict[str, float], value_key: str, weight_key: str) -> Any:
    weight = totals[weight_key]
    if weight <= 0:
        return "N/A"
    return totals[value_key] / weight


def _summary_metric_pair(
    totals: Dict[str, Dict[str, float]],
    key: str,
    *,
    suffix: str = "",
    average: Optional[tuple[str, str]] = None,
) -> list[str]:
    if average:
        db_value = _weighted_average(totals["db_conn"], average[0], average[1])
        text_value = _weighted_average(totals["text"], average[0], average[1])
    else:
        db_value = totals["db_conn"][key]
        text_value = totals["text"][key]

    return [
        f"**{_format_value(db_value, suffix)}**",
        f"**{_format_value(text_value, suffix)}**",
        f"**{_format_delta(db_value, text_value, suffix)}**",
    ]


def _summary_correlation_pair(totals: Dict[str, Dict[str, float]], key: str) -> list[str]:
    db_value = _weighted_average(totals["db_conn"], f"{key}_sum", f"{key}_count")
    text_value = _weighted_average(totals["text"], f"{key}_sum", f"{key}_count")
    return [
        f"**{_format_float(db_value)}**",
        f"**{_format_float(text_value)}**",
        f"**{_format_float_delta(db_value, text_value)}**",
    ]


def _summary_complexity_triplet(totals: Dict[str, float]) -> str:
    return (
        f"**{int(totals['complexity_low'])}/"
        f"{int(totals['complexity_medium'])}/"
        f"{int(totals['complexity_high'])}**"
    )


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return slug or "model"


def iter_database_reports(base_dir: Path) -> Iterable[tuple[str, ModeReports]]:
    for results_dir in sorted(path for path in base_dir.iterdir() if path.is_dir()):
        reports: ModeReports = {}

        for mode in MODES:
            report = _load_json(results_dir / mode / "test_report.json")
            if report is not None:
                reports[mode] = report

        if reports:
            yield _db_name(results_dir), reports


def discover_models(base_dir: Path) -> list[str]:
    models: set[str] = set()

    for _, reports in iter_database_reports(base_dir):
        for report in reports.values():
            report_models = report.get("models", {})
            if isinstance(report_models, dict):
                models.update(report_models.keys())

    return sorted(models)


def generate_model_report(base_dir: Path, model_name: str) -> str:
    rows: list[list[str]] = []
    summary_totals = {
        mode: {
            "success_weighted": 0.0,
            "success_weight": 0.0,
            "eval_correct": 0.0,
            "time_weighted": 0.0,
            "time_weight": 0.0,
            "attempts_weighted": 0.0,
            "attempts_weight": 0.0,
            "attempts_pearson_sum": 0.0,
            "attempts_pearson_count": 0.0,
            "attempts_spearman_sum": 0.0,
            "attempts_spearman_count": 0.0,
            "complexity_pearson_sum": 0.0,
            "complexity_pearson_count": 0.0,
            "complexity_spearman_sum": 0.0,
            "complexity_spearman_count": 0.0,
            "syntax": 0.0,
            "runtime": 0.0,
            "complexity_low": 0.0,
            "complexity_medium": 0.0,
            "complexity_high": 0.0,
        }
        for mode in MODES
    }
    total_tables = 0
    total_requests = 0

    for db_name, reports in iter_database_reports(base_dir):
        db_conn_report = reports.get("db_conn")
        text_report = reports.get("text")

        db_conn_model = _safe_get(db_conn_report, "models", model_name, default=None)
        text_model = _safe_get(text_report, "models", model_name, default=None)

        if not isinstance(db_conn_model, dict) and not isinstance(text_model, dict):
            continue

        db_conn_requests = _safe_get(db_conn_report, "num_requests")
        text_requests = _safe_get(text_report, "num_requests")
        requests = db_conn_requests if db_conn_requests != "N/A" else text_requests

        db_conn_tables = _safe_get(db_conn_report, "num_tables")
        text_tables = _safe_get(text_report, "num_tables")
        tables = db_conn_tables if db_conn_tables != "N/A" else text_tables

        if isinstance(tables, int):
            total_tables += tables
        if isinstance(requests, int):
            total_requests += requests

        if isinstance(db_conn_report, dict) and isinstance(db_conn_model, dict):
            _add_mode_totals(summary_totals, "db_conn", db_conn_report, db_conn_model)
        if isinstance(text_report, dict) and isinstance(text_model, dict):
            _add_mode_totals(summary_totals, "text", text_report, text_model)

        row = [
            db_name,
            str(tables),
            str(requests),
            *_metric_pair(db_conn_model, text_model, "status", "correct_pct", suffix="%"),
            *_metric_pair(db_conn_model, text_model, "status", "n_eval_correct"),
            *_metric_pair(db_conn_model, text_model, "time", "avg", suffix="s"),
            *_metric_pair(db_conn_model, text_model, "attempts", "avg"),
            *_correlation_pair(db_conn_model, text_model, "attempts", "pearson"),
            *_correlation_pair(db_conn_model, text_model, "attempts", "spearman"),
            *_correlation_pair(db_conn_model, text_model, "complexity", "pearson"),
            *_correlation_pair(db_conn_model, text_model, "complexity", "spearman"),
            *_metric_pair(db_conn_model, text_model, "status", "n_syntax"),
            *_metric_pair(db_conn_model, text_model, "status", "n_runtime"),
            _complexity_triplet(db_conn_model),
            _complexity_triplet(text_model),
        ]
        rows.append(row)

    if not rows:
        return f"# Model Performance Comparison: `{model_name}`\n\nNo data found for this model."

    rows.append([
        "**MODEL VERDICT**",
        f"**{total_tables}**",
        f"**{total_requests}**",
        *_summary_metric_pair(
            summary_totals,
            "success",
            suffix="%",
            average=("success_weighted", "success_weight"),
        ),
        *_summary_metric_pair(summary_totals, "eval_correct"),
        *_summary_metric_pair(
            summary_totals,
            "time",
            suffix="s",
            average=("time_weighted", "time_weight"),
        ),
        *_summary_metric_pair(
            summary_totals,
            "attempts",
            average=("attempts_weighted", "attempts_weight"),
        ),
        *_summary_correlation_pair(summary_totals, "attempts_pearson"),
        *_summary_correlation_pair(summary_totals, "attempts_spearman"),
        *_summary_correlation_pair(summary_totals, "complexity_pearson"),
        *_summary_correlation_pair(summary_totals, "complexity_spearman"),
        *_summary_metric_pair(summary_totals, "syntax"),
        *_summary_metric_pair(summary_totals, "runtime"),
        _summary_complexity_triplet(summary_totals["db_conn"]),
        _summary_complexity_triplet(summary_totals["text"]),
    ])

    headers = [
        "Database",
        "Tables",
        "Requests",
        "Success db_conn",
        "Success text",
        "Success delta",
        "Eval correct db_conn",
        "Eval correct text",
        "Eval correct delta",
        "Avg time db_conn",
        "Avg time text",
        "Avg time delta",
        "Avg attempts db_conn",
        "Avg attempts text",
        "Avg attempts delta",
        "Attempts Pearson db_conn",
        "Attempts Pearson text",
        "Attempts Pearson delta",
        "Attempts Spearman db_conn",
        "Attempts Spearman text",
        "Attempts Spearman delta",
        "Complexity Pearson db_conn",
        "Complexity Pearson text",
        "Complexity Pearson delta",
        "Complexity Spearman db_conn",
        "Complexity Spearman text",
        "Complexity Spearman delta",
        "Syntax db_conn",
        "Syntax text",
        "Syntax delta",
        "Runtime db_conn",
        "Runtime text",
        "Runtime delta",
        "Complexity L/M/H db_conn",
        "Complexity L/M/H text",
    ]

    return "\n".join(
        [
            f"# Model Performance Comparison: `{model_name}`",
            "",
            f"**Base directory:** `{base_dir}`",
            "",
            "Each row compares the same database in `db_conn` mode against `text` mode. Deltas are `db_conn - text`.",
            "",
            _markdown_table(headers, rows),
            "",
        ]
    )


def write_model_reports(base_dir: Path, output_dir: Path, selected_model: Optional[str] = None) -> list[Path]:
    models = [selected_model] if selected_model else discover_models(base_dir)
    if not models:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    for model_name in models:
        if model_name is None:
            continue

        markdown = generate_model_report(base_dir, model_name)
        output_path = output_dir / f"{_slugify(model_name)}.md"
        output_path.write_text(markdown, encoding="utf-8")
        written_paths.append(output_path)

    return written_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate one Markdown db_conn-vs-text comparison table for each model."
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("tests/output/generations"),
        help="Path to the base directory containing *_results folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tests/output/model_summaries"),
        help="Directory where model Markdown files will be written.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional exact model name. If omitted, one .md file is generated for every model found.",
    )

    args = parser.parse_args()

    if not args.base_dir.exists():
        raise SystemExit(f"Base directory not found: {args.base_dir}")

    written_paths = write_model_reports(args.base_dir, args.output_dir, args.model)
    if not written_paths:
        raise SystemExit("No model data found.")

    for path in written_paths:
        print(f"Wrote {path}")

    print(f"Done. Written files: {len(written_paths)}.")


if __name__ == "__main__":
    main()
