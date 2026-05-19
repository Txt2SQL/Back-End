import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import OUTPUT_DIR
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


def summarize_database(dataset: BaseDataset, db_name: str, table_count: int) -> dict[str, Any] | None:
    requests = dataset.get_requests(db_name)
    num_requests = len(requests)
    if num_requests == 0:
        return None

    schema = dataset.get_schema(db_name)
    complexity_scores: list[int] = []

    for request in requests:
        gold_sql = dataset._get_gold_sql(db_name, request)
        complexity_scores.append(compute_query_complexity(gold_sql))

    return {
        "dataset": dataset.name,
        "database_name": db_name,
        "num_tables": table_count,
        "num_columns": count_schema_columns(schema),
        "num_requests": num_requests,
        "complexity_vector": complexity_scores,
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
        default=OUTPUT_DIR / "database_report.json",
        help="Output JSON path. Defaults to tests/output/database_report.json.",
    )
    args = parser.parse_args()

    output_path = write_report(args.output)
    print(f"Database report written to: {output_path}")


if __name__ == "__main__":
    main()
