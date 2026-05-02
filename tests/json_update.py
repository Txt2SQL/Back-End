import argparse
import json
from pathlib import Path
from typing import Any


def remove_model_complexity_buckets(report: dict[str, Any]) -> int:
    removed = 0

    models = report.get("models", {})
    if not isinstance(models, dict):
        return removed

    for model_data in models.values():
        if not isinstance(model_data, dict):
            continue

        complexity = model_data.get("complexity")
        if not isinstance(complexity, dict):
            continue

        for key in ("low", "medium", "high"):
            if key in complexity:
                del complexity[key]
                removed += 1

    return removed


def update_reports(base_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    updated_files = 0
    removed_fields = 0

    for report_path in sorted(base_dir.rglob("test_report.json")):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        removed = remove_model_complexity_buckets(report)

        if removed == 0:
            continue

        updated_files += 1
        removed_fields += removed

        if not dry_run:
            report_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        print(f"UPDATED {report_path}: removed {removed} fields")

    return updated_files, removed_fields


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove per-model complexity low/medium/high buckets from test_report.json files."
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("tests/output/generations"),
        help="Base directory containing *_results folders.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing files.",
    )

    args = parser.parse_args()

    if not args.base_dir.exists():
        raise SystemExit(f"Base directory not found: {args.base_dir}")

    updated_files, removed_fields = update_reports(args.base_dir, args.dry_run)

    print(
        f"Done. Updated files: {updated_files}. "
        f"Removed fields: {removed_fields}."
    )


if __name__ == "__main__":
    main()