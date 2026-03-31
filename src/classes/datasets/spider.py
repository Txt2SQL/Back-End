import os, re, subprocess
from dataclasses import dataclass
import sys
from typing import Optional
from pathlib import Path


from config.paths import SPIDER_REPO
from tests.dataset_test import TMP_DIR, SPIDER_DATA
from .base_dataset import BaseDataset

NLTK_DATA_DIR = TMP_DIR / "nltk_data"

@dataclass
class SpiderEvaluationReport:
    exec_result: subprocess.CompletedProcess[str]
    execution_accuracy: Optional[float]
    report_file: Path

class SpiderDataset(BaseDataset):
    
    def __init__(self) -> None:
        super().__init__("spider")
        self.db_dir = SPIDER_DATA / "databases"
              
    def get_requests(self, db_name: str) -> list[str]:
        return [item["question"] for item in self.dev if item["db_id"] == db_name]

    def get_schema(self, db_name: str) -> dict:
        spider_schema = self.tables[db_name]
        tables = spider_schema["table_names_original"]
        columns = spider_schema["column_names_original"]
        column_types = spider_schema["column_types"]
        primary_keys = set(spider_schema["primary_keys"])
        foreign_keys = spider_schema["foreign_keys"]

        type_map = {
            "text": "TEXT",
            "number": "INT",
            "time": "DATETIME",
            "boolean": "BOOLEAN",
        }

        db = {table: [] for table in tables}

        for idx, ((table_id, col_name), col_type) in enumerate(zip(columns, column_types)):
            if table_id == -1:
                continue

            table_name = tables[table_id]
            constraints = []

            if idx in primary_keys:
                constraints.append("PRIMARY KEY")

            db[table_name].append(
                {
                    "name": col_name,
                    "type": type_map.get(col_type, "TEXT"),
                    "constraints": constraints,
                }
            )

        for fk_col, ref_col in foreign_keys:
            fk_table_id, fk_name = columns[fk_col]
            ref_table_id, ref_name = columns[ref_col]

            fk_table = tables[fk_table_id]
            ref_table = tables[ref_table_id]

            for col in db[fk_table]:
                if col["name"] == fk_name:
                    col["constraints"].append(
                        f"FOREIGN KEY REFERENCES {ref_table}({ref_name})"
                    )

        return {
            "tables": [
                {
                    "name": table_name,
                    "columns": cols,
                }
                for table_name, cols in db.items()
            ]
        }

    def get_dbs(self) -> list[tuple[str, int]]:
        table_counts = {
            schema["db_id"]: len(schema["table_names_original"])
            for schema in self.tables
        }
        seen = set()
        dbs = []

        for item in self.dev:
            db_name = item["db_id"]
            if db_name not in seen:
                seen.add(db_name)
                dbs.append((db_name, table_counts.get(db_name, 0)))

        return dbs
    
    def _build_nltk_env(self) -> dict[str, str]:
        env = os.environ.copy()
        existing = env.get("NLTK_DATA", "").strip()
        search_paths = [str(NLTK_DATA_DIR)]
        if existing:
            search_paths.append(existing)
        env["NLTK_DATA"] = os.pathsep.join(search_paths)
        return env

    def _extract_metric(self, output: str, metric_name: str) -> Optional[float]:
        for line in output.splitlines():
            if line.strip().startswith(metric_name):
                numbers = re.findall(r"[0-9]*\.?[0-9]+", line)
                if numbers:
                    return float(numbers[-1])
        return None
    
    def dataset_evaluation(
        self,
        predicted_sql: str, 
        gold_sql: str, 
        db_id: str, 
        question: Optional[str] = None
    ) -> dict:
        eval_dir = TMP_DIR / "spider_eval"
        eval_dir.mkdir(parents=True, exist_ok=True)

        report_file = eval_dir / f"{db_id}_evaluation.log"
        gold_file = eval_dir / f"{db_id}_gold.sql"
        pred_file = eval_dir / f"{db_id}_pred.sql"

        normalized_gold_sql = self._normalize_sql(gold_sql)
        normalized_predicted_sql = self._normalize_sql(predicted_sql)

        gold_file.write_text(
            f"{normalized_gold_sql}\t{db_id}\n",
            encoding="utf-8",
        )
        pred_file.write_text(
            f"{normalized_predicted_sql}\n",
            encoding="utf-8",
        )

        exec_result = subprocess.run(
            [
                sys.executable,
                str(self.eval_file),
                "--gold",
                str(gold_file),
                "--pred",
                str(pred_file),
                "--etype",
                "exec",
                "--db",
                str(self.db_dir),
                "--table",
                str(self.path / "tables.json"),
            ],
            cwd=SPIDER_REPO,
            capture_output=True,
            text=True,
            check=False,
            env=self._build_nltk_env(),
        )

        report_file.write_text(
            "\n".join(
                [
                    "=== Gold SQL ===",
                    normalized_gold_sql,
                    "",
                    "=== Predicted SQL ===",
                    normalized_predicted_sql,
                    "",
                    "=== Spider exec stdout ===",
                    (exec_result.stdout or "").strip(),
                    "",
                    "=== Spider exec stderr ===",
                    (exec_result.stderr or "").strip(),
                    "",
                ]
            ),
            encoding="utf-8",
        )

        gold_file.unlink(missing_ok=True)
        pred_file.unlink(missing_ok=True)

        return {
            "exec_result": exec_result,
            "execution_accuracy": self._extract_metric(exec_result.stdout, "Execution Accuracy"),
            "report_file": report_file,
        }