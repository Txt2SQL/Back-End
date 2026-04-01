import json
import subprocess
import re
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.classes.logger import LoggerManager
from .base_dataset import BaseDataset, OfficialEvalReport

class BirdDataset(BaseDataset):
    BIRD_DELIMITER = "\t----- bird -----\t"
    DEFAULT_TIMEOUT_SECONDS = 30.0

    def __init__(self) -> None:
        super().__init__("bird")

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)

    def _extract_accuracy(self, output: str) -> float:
        """
        Parses BIRD's evaluation.py standard output.
        BIRD prints accuracy as a percentage (e.g., 100.00). 
        We return it as a float from 0.0 to 1.0 to align with BaseDataset expectations.
        """
        for line in output.splitlines():
            if line.strip().lower().startswith("accuracy"):
                numbers = re.findall(r"[0-9]+\.?[0-9]*", line)
                if numbers:
                    return float(numbers[-1]) / 100.0
        return 0.0

    def dataset_evaluation(
        self, 
        predicted_query: QuerySession, 
        gold_query: QuerySession, 
        db_id: str, 
        question_index: int,
        model_name: str,
    ) -> OfficialEvalReport:
        
        # 1. Prepare inputs
        example = self._get_example_by_index(question_index)
        difficulty = example.get("difficulty", "simple") if example else "simple"

        normalized_pred = self._normalize_sql(predicted_sql)
        normalized_gold = self._normalize_sql(gold_sql)

        execution_stem = self._build_execution_stem()
        report_file = self._get_bird_evaluations_dir() / f"{execution_stem}.json"

        self.logger.info(f"Running BIRD eval for db_id={db_id} question_index={question_index}")

        # 2. Use Temporary context manager
        with tempfile.TemporaryDirectory(prefix=f"{execution_stem}_") as tmpdir:
            tmp_path = Path(tmpdir)

            pred_dir = tmp_path / "pred"
            gold_dir = tmp_path / "gold"
            pred_dir.mkdir()
            gold_dir.mkdir()

            # 📄 A. predict_dev.json (FORMATO BIRD)
            pred_file = pred_dir / "predict_dev.json"
            pred_content = {
                "0": f"{normalized_pred}{self.BIRD_DELIMITER}{db_id}"
            }
            with open(pred_file, "w", encoding="utf-8") as f:
                json.dump(pred_content, f)

            # 📄 B. dev_gold.sql
            gold_file = gold_dir / "dev_gold.sql"
            with open(gold_file, "w", encoding="utf-8") as f:
                f.write(f"{normalized_gold}\t{db_id}\n")

            # 📄 C. MOCK dev.json
            # BIRD's compute_acc_by_diff iterates over the JSON provided by diff_json_path synchronously.
            # Passing the full dev.json would cause an IndexError because we are evaluating 1 item.
            mock_dev_file = tmp_path / "mock_dev.json"
            mock_dev_content = [{"difficulty": difficulty}]
            with open(mock_dev_file, "w", encoding="utf-8") as f:
                json.dump(mock_dev_content, f)

            # ⚙️ 3. Subprocess call to BIRD evaluation.py
            cmd = [
                sys.executable,
                str(self.eval_file),
                "--predicted_sql_path", f"{pred_dir}/", # trailing slash required by evaluation.py string concat
                "--ground_truth_path", f"{gold_dir}/",
                "--data_mode", "dev",
                "--db_root_path", f"{self.db_dir}/",
                "--num_cpus", "1",
                "--meta_time_out", str(self.DEFAULT_TIMEOUT_SECONDS),
                "--mode_gt", "gt",
                "--mode_predict", "gpt",
                "--diff_json_path", str(mock_dev_file),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            # 🔍 4. Parsing accuracy
            accuracy_normalized = self._extract_accuracy(result.stdout)
            official_match = accuracy_normalized == 1.0

            # 📝 5. Structured JSON Logging
            report_data = {
                "metadata": {
                    "database": db_id,
                    "question_index": question_index,
                    "difficulty": difficulty,
                    "official_match": official_match,
                    "returncode": result.returncode,
                    "execution_accuracy": accuracy_normalized,
                    "command": " ".join(cmd)
                },
                "sql": {
                    "gold": normalized_gold,
                    "predicted": normalized_pred
                },
                "output": {
                    "stdout": result.stdout.strip() if result.stdout else "",
                    "stderr": result.stderr.strip() if result.stderr else ""
                }
            }
            
            report_file.write_text(json.dumps(report_data, indent=4), encoding="utf-8")

        self.logger.info(f"BIRD evaluation report written to {report_file}")

        # 6. Return OfficialEvalReport
        return OfficialEvalReport(
            execution_accuracy=accuracy_normalized,
            official_match=official_match,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            report_file=str(report_file)
        )
