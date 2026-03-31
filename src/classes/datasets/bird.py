import json, subprocess, os, re
import multiprocessing as mp
from pathlib import Path
from typing import Optional

from config.paths import DATASET_DIR, INPUT_DIR, TMP_DIR

from .base_dataset import BaseDataset


class BirdDataset(BaseDataset):
    BIRD_DELIMITER = "\t----- bird -----\t"
    DEFAULT_TIMEOUT_SECONDS = 30.0

    def __init__(self) -> None:
        super().__init__("bird")

    def get_requests(self, db_name: str) -> list[str]:
        return [item["question"] for item in self.dev if item["db_id"] == db_name]

    def get_dbs(self) -> list[tuple[str, int]]:
        table_counts = {
            schema["db_id"]: len(schema["table_names_original"])
            for schema in self.tables
        }
        seen = set()
        dbs = []

        for example in self.dev:
            db_name = example["db_id"]
            if db_name not in seen:
                seen.add(db_name)
                dbs.append((db_name, table_counts.get(db_name, 0)))

        return dbs

    def get_schema(self, db_name: str) -> dict:
        for entry in self.tables:
            if entry["db_id"] == db_name:
                table_names = entry["table_names_original"]
                column_names = entry["column_names_original"]
                column_types = entry["column_types"]
                primary_keys = entry.get("primary_keys", [])
                foreign_keys = entry.get("foreign_keys", [])

                type_map = {
                    "text": "TEXT",
                    "integer": "INTEGER",
                    "number": "NUMERIC",
                    "real": "REAL",
                    "date": "DATE",
                    "datetime": "DATETIME",
                    "time": "TIME",
                    "boolean": "BOOLEAN",
                }

                tables = {table_name: [] for table_name in table_names}

                flat_primary_keys: set[int] = set()
                composite_primary_keys: list[tuple[int, ...]] = []
                for pk in primary_keys:
                    if isinstance(pk, list):
                        composite_primary_keys.append(tuple(pk))
                    else:
                        flat_primary_keys.add(pk)

                for idx, ((table_id, col_name), col_type) in enumerate(
                    zip(column_names, column_types)
                ):
                    if table_id == -1:
                        continue

                    constraints: list[str] = []
                    if idx in flat_primary_keys:
                        constraints.append("PRIMARY KEY")

                    tables[table_names[table_id]].append(
                        {
                            "name": col_name,
                            "type": type_map.get(col_type.lower(), col_type.upper()),
                            "constraints": constraints,
                        }
                    )

                for composite_key in composite_primary_keys:
                    for column_idx in composite_key:
                        table_id, column_name = column_names[column_idx]
                        if table_id == -1:
                            continue

                        for column in tables[table_names[table_id]]:
                            if column["name"] == column_name:
                                if "PRIMARY KEY" not in column["constraints"]:
                                    column["constraints"].append("PRIMARY KEY")
                                break

                for source_idx, target_idx in foreign_keys:
                    source_table_id, source_column_name = column_names[source_idx]
                    target_table_id, target_column_name = column_names[target_idx]

                    if source_table_id == -1 or target_table_id == -1:
                        continue

                    reference = (
                        f"FOREIGN KEY REFERENCES "
                        f"{table_names[target_table_id]}({target_column_name})"
                    )

                    for column in tables[table_names[source_table_id]]:
                        if column["name"] == source_column_name:
                            column["constraints"].append(reference)
                            break

                return {
                    "tables": [
                        {
                            "name": table_name,
                            "columns": columns,
                        }
                        for table_name, columns in tables.items()
                    ]
                }
        raise ValueError(f"Schema not found for db: {db_name}")

    def _extract_accuracy(self, output: str) -> float:
        for line in output.splitlines():
            if line.strip().startswith("accuracy"):
                numbers = re.findall(r"[0-9]+\.?[0-9]*", line)
                if numbers:
                    return float(numbers[-1])
        return 0.0

    def dataset_evaluation(
        self,
        predicted_sql: str,
        gold_sql: str,
        db_id: str,
        question: Optional[str] = None,
    ) -> dict:
        example = self._find_example(db_id=db_id, question=question)

        predicted_sql = self._normalize_sql(predicted_sql)
        gold_sql = self._normalize_sql(gold_sql)

        try:
            with TMP_DIR as tmpdir:
                tmp_path = Path(tmpdir)

                # 📁 paths temporanei
                pred_dir = tmp_path / "pred"
                gold_dir = tmp_path / "gold"
                pred_dir.mkdir()
                gold_dir.mkdir()

                # 📄 1. predict_dev.json (FORMATO BIRD)
                pred_file = pred_dir / "predict_dev.json"
                pred_content = {
                    "0": f"{predicted_sql}{self.BIRD_DELIMITER}{db_id}"
                }

                with open(pred_file, "w", encoding="utf-8") as f:
                    json.dump(pred_content, f)

                # 📄 2. dev_gold.sql
                gold_file = gold_dir / "dev_gold.sql"
                with open(gold_file, "w", encoding="utf-8") as f:
                    f.write(f"{gold_sql}\t{db_id}\n")

                # ⚙️ 3. subprocess call
                cmd = [
                    "python",
                    str(self.eval_file),  # deve puntare a evaluation.py
                    "--predicted_sql_path", str(pred_dir) + "/",
                    "--ground_truth_path", str(gold_dir) + "/",
                    "--data_mode", "dev",
                    "--db_root_path", str(self.db_dir) + "/",
                    "--num_cpus", "1",
                    "--meta_time_out", str(self.DEFAULT_TIMEOUT_SECONDS),
                    "--mode_gt", "gt",
                    "--mode_predict", "gpt",
                    "--diff_json_path", str(self.dev),
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                )

                stdout = result.stdout
                stderr = result.stderr

                # 🔍 4. parsing accuracy
                accuracy = self._extract_accuracy(stdout)

                eval_result = {
                    "success": accuracy == 100.0,
                    "accuracy": accuracy,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": result.returncode,
                }

        except Exception as e:
            eval_result = {
                "success": False,
                "error": str(e),
            }

        return {
            "status": "success" if eval_result.get("success") else "incorrect",
            "method": "bird_exec",
            "details": eval_result,
            "difficulty": example.get("difficulty") if example else None,
            "question_id": example.get("question_id") if example else None,
        }

    def _format_bird_record(self, sql: str, db_id: str) -> str:
        return f"{self._normalize_sql(sql)}{self.BIRD_DELIMITER}{db_id}\n"
