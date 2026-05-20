import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import INPUT_DIR
from src.classes.datasets import BirdDataset, SpiderDataset
from src.classes.datasets.base_dataset import BaseDataset


def compute_query_complexity(sql: str | None) -> int:
    if not sql:
        return 0

    score = 0
    score += len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE)) * 2
    score += len(re.findall(r"\b(SUM|AVG|MIN|MAX|COUNT)\s*\(", sql, re.IGNORECASE)) * 2

    if re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE):
        score += 2

    if re.search(r"\bHAVING\b", sql, re.IGNORECASE):
        score += 2

    score += len(re.findall(r"\bOVER\s*\(", sql, re.IGNORECASE)) * 3
    score += len(re.findall(r"\bSELECT\b", sql, re.IGNORECASE)) - 1
    return max(score, 0)


def count_schema_columns(schema: dict[str, Any]) -> int:
    return sum(
        len(table.get("columns", []))
        for table in schema.get("tables", [])
        if isinstance(table, dict)
    )


def _column_has_constraint(column: dict[str, Any], constraint_name: str) -> bool:
    constraints = column.get("constraints", [])
    if not isinstance(constraints, list):
        return False

    normalized_constraint_name = constraint_name.upper()
    return any(
        isinstance(constraint, str)
        and normalized_constraint_name in constraint.upper()
        for constraint in constraints
    )


def _structural_column_weight(column: dict[str, Any]) -> float:
    is_primary_key = _column_has_constraint(column, "PRIMARY KEY")
    is_foreign_key = _column_has_constraint(column, "FOREIGN KEY")

    if is_primary_key and is_foreign_key:
        return 2.5
    if is_foreign_key:
        return 2.0
    if is_primary_key:
        return 1.5
    return 1.0


def _semantic_type_bonus(sql_type: Any) -> float:
    if not isinstance(sql_type, str):
        return 0.0

    normalized_type = sql_type.upper()
    if "TEXT" in normalized_type or "VARCHAR" in normalized_type:
        return 0.2
    if any(temporal_type in normalized_type for temporal_type in ("DATE", "DATETIME", "TIME", "TIMESTAMP")):
        return 0.1
    return 0.0


def _column_complexity(column: dict[str, Any]) -> float:
    return _structural_column_weight(column) + _semantic_type_bonus(column.get("type"))


def _outgoing_foreign_key_count(table: dict[str, Any]) -> int:
    return sum(
        1
        for column in table.get("columns", [])
        if isinstance(column, dict) and _column_has_constraint(column, "FOREIGN KEY")
    )


def compute_table_complexity_vector(schema: dict[str, Any]) -> list[float]:
    table_complexities: list[float] = []

    for table in schema.get("tables", []):
        if not isinstance(table, dict):
            continue

        table_complexity = 0.0
        for column in table.get("columns", []):
            if isinstance(column, dict):
                table_complexity += _column_complexity(column)

        relation_factor = 1 + 0.15 * _outgoing_foreign_key_count(table)
        final_table_complexity = table_complexity * relation_factor
        table_complexities.append(round(final_table_complexity, 2))

    return table_complexities


def summarize_database(dataset: BaseDataset, db_name: str, table_count: int) -> dict[str, Any] | None:
    requests = dataset.get_requests(db_name)
    num_requests = len(requests)
    if num_requests == 0:
        return None

    schema = dataset.get_schema(db_name)
    query_complexity_scores: list[int] = []

    for request in requests:
        gold_sql = dataset._get_gold_sql(db_name, request)
        query_complexity_scores.append(compute_query_complexity(gold_sql))

    return {
        "dataset": dataset.name,
        "database_name": db_name,
        "num_tables": table_count,
        "num_columns": count_schema_columns(schema),
        "num_requests": num_requests,
        "query_complexity_vector": query_complexity_scores,
        "table_complexity_vector": compute_table_complexity_vector(schema),
    }


def build_report() -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []

    for dataset in (BirdDataset(), SpiderDataset()):
        for db_name, table_count in dataset.get_dbs():
            database_summary = summarize_database(dataset, db_name, table_count)
            if database_summary is not None:
                report.append(database_summary)

    return report


def write_report(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_report()
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate database_report.json for BIRD and Spider datasets."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=INPUT_DIR / "datasets" / "database_report.json",
        help="Output JSON path. Defaults to tests/output/database_report.json.",
    )
    args = parser.parse_args()

    output_path = write_report(args.output)
    print(f"Database report written to: {output_path}")


if __name__ == "__main__":
    main()
