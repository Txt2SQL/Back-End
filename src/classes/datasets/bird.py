import json, subprocess, re, os, sys, hashlib

from tests.test_sql_generation import TMP_DIR

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.classes.logger import LoggerManager
from .base_dataset import BaseDataset, OfficialEvalReport
from src.classes.domain_states import QuerySession

# ---------------------------------------------------------
# SHARED DIRECTORY CONFIGURATION
# ---------------------------------------------------------

BIRD_EVAL_DIR = TMP_DIR / "bird_eval"

class BirdDataset(BaseDataset):
    BIRD_DELIMITER = "\t----- bird -----\t"
    DEFAULT_TIMEOUT_SECONDS = 30.0
    REQUIRED_DIFFICULTIES = ("simple", "moderate", "challenging")

    def __init__(self) -> None:
        super().__init__("bird")

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)

    def get_dbs(self) -> list[tuple[str, int]]:
            """Get a list of unique databases and their table counts, preserving order."""
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

    def get_schema(self, db_name: str) -> dict:
        """Parse and return the schema for a given database."""
        schema_data = next(
            (schema for schema in self.tables if schema["db_id"] == db_name), 
            None
        )
        if schema_data is None:
            raise ValueError(f"Schema not found for db: {db_name}")

        table_names = schema_data["table_names_original"]
        column_names = schema_data["column_names_original"]
        column_types = schema_data["column_types"]
        primary_keys = schema_data.get("primary_keys", [])
        foreign_keys = schema_data.get("foreign_keys", [])

        # BIRD type mapping
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

        # BIRD mixes flat primary keys (int) and composite primary keys (list[int])
        flat_primary_keys: set[int] = set()
        composite_primary_keys: list[list[int]] = []
        
        for pk in primary_keys:
            if isinstance(pk, list):
                composite_primary_keys.append(pk)
            else:
                flat_primary_keys.add(pk)

        # 1. Process all columns and assign flat primary keys
        for idx, ((table_id, col_name), col_type) in enumerate(zip(column_names, column_types)):
            if table_id == -1: # -1 indicates the generic '*' column, skip it
                continue

            constraints: list[str] = []
            if idx in flat_primary_keys:
                constraints.append("PRIMARY KEY")

            # Resolve type: use map, fallback to UPPERCASE of original, or default to TEXT
            resolved_type = type_map.get(
                col_type.lower(), 
                col_type.upper() if col_type else "TEXT"
            )

            tables[table_names[table_id]].append({
                "name": col_name,
                "type": resolved_type,
                "constraints": constraints,
            })

        # 2. Append composite primary key constraints
        for composite_key in composite_primary_keys:
            for column_idx in composite_key:
                table_id, column_name = column_names[column_idx]
                if table_id == -1:
                    continue

                # Find the column in the table and append the constraint
                for column in tables[table_names[table_id]]:
                    if column["name"] == column_name:
                        if "PRIMARY KEY" not in column["constraints"]:
                            column["constraints"].append("PRIMARY KEY")
                        break

        # 3. Append foreign key constraints
        for source_idx, target_idx in foreign_keys:
            source_table_id, source_column_name = column_names[source_idx]
            target_table_id, target_column_name = column_names[target_idx]

            if source_table_id == -1 or target_table_id == -1:
                continue

            reference = (
                f"FOREIGN KEY REFERENCES "
                f"{table_names[target_table_id]}({target_column_name})"
            )

            # Find the source column and append the reference constraint
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
        
    def _get_question_index(self, db_id: str, question: str) -> int:
            """
            Locates the question in the dev dataset and returns its unique index.
            Prefers BIRD's native 'question_id' field, falling back to the list index.
            """
            for idx, item in enumerate(self.dev):
                if item["db_id"] == db_id and item["question"] == question:
                    # BIRD JSON has a "question_id" key
                    return item.get("question_id", idx)
                    
            raise ValueError(f"Question not found for db_id: '{db_id}' and question: '{question}'")
    
    def _get_gold_sql(self, db_id: str, question: str) -> str:
        """
        Retrieves the gold SQL query for a given database and question.
        If question is None, returns the first matching SQL for the db_id.
        """
        for item in self.dev:
            if item["db_id"] == db_id and (question is None or item["question"] == question):
                return item["SQL"]
        
        raise ValueError(f"Gold SQL not found for db_id: '{db_id}' and question: '{question}'")

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

    def _build_eval_payloads(
        self,
        normalized_pred: str,
        normalized_gold: str,
        db_id: str,
    ) -> tuple[dict[str, str], list[str], list[dict[str, str]]]:
        """
        BIRD's official evaluator assumes every difficulty bucket is present and
        crashes on singleton inputs. Replicating the same query across the three
        required difficulty labels preserves total accuracy while satisfying the
        script's internal expectations.
        """
        pred_payload = {
            str(idx): f"{normalized_pred}{self.BIRD_DELIMITER}{db_id}"
            for idx, _ in enumerate(self.REQUIRED_DIFFICULTIES)
        }
        gold_payload = [
            f"{normalized_gold}\t{db_id}\n"
            for _ in self.REQUIRED_DIFFICULTIES
        ]
        diff_payload = [
            {"difficulty": difficulty}
            for difficulty in self.REQUIRED_DIFFICULTIES
        ]
        return pred_payload, gold_payload, diff_payload
    
    def dataset_evaluation(
        self, 
        predicted_query: QuerySession, 
        gold_query: QuerySession, 
        db_id: str, 
        question_index: int,
        model_name: str,
    ) -> OfficialEvalReport:
        
        normalized_pred = predicted_query.normalize_sql()
        normalized_gold = gold_query.normalize_sql()

        self.logger.info(f"Running BIRD eval for db_id={db_id} question_index={question_index}")

        # 1. Generate unique hash ID for safe parallel execution
        hash_input = f"{model_name}_{db_id}_{question_index}"
        hash_id = hashlib.md5(hash_input.encode("utf-8")).hexdigest()[:12]

        # 2. Create unique folder structure required by BIRD
        eval_folder = BIRD_EVAL_DIR / hash_id
        pred_dir = eval_folder / "pred"
        gold_dir = eval_folder / "gold"
        
        pred_dir.mkdir(parents=True, exist_ok=True)
        gold_dir.mkdir(parents=True, exist_ok=True)

        pred_file = pred_dir / "predict_dev.json"
        gold_file = gold_dir / "dev_gold.sql"
        mock_dev_file = eval_folder / "mock_dev.json"

        try:
            # 3. Write BIRD-specific files
            pred_payload, gold_payload, diff_payload = self._build_eval_payloads(
                normalized_pred=normalized_pred,
                normalized_gold=normalized_gold,
                db_id=db_id,
            )

            # A. predict_dev.json (Requires specific BIRD delimiter)
            with open(pred_file, "w", encoding="utf-8") as f:
                json.dump(pred_payload, f)

            # B. dev_gold.sql (Requires standard tab delimiter)
            with open(gold_file, "w", encoding="utf-8") as f:
                f.writelines(gold_payload)

            # C. mock_dev.json must include all difficulty buckets to prevent
            #    ZeroDivisionError inside the official evaluator.
            with open(mock_dev_file, "w", encoding="utf-8") as f:
                json.dump(diff_payload, f)

            # 4. Build and run command
            # Note: trailing slashes "/" are strictly required because BIRD's
            # evaluation script builds paths using raw string concatenation!
            cmd = [
                sys.executable,
                str(self.eval_file),
                "--predicted_sql_path", f"{pred_dir}/", 
                "--ground_truth_path", f"{gold_dir}/",
                "--data_mode", "dev",
                "--db_root_path", f"{self.db_dir}/",
                "--num_cpus", "1",
                "--meta_time_out", str(self.DEFAULT_TIMEOUT_SECONDS),
                "--mode_gt", "gt",
                "--mode_predict", "gpt",
                "--diff_json_path", str(mock_dev_file),
            ]

            exec_result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            # Extract metric (divides by 100 inside the helper method)
            execution_accuracy = self._extract_accuracy(exec_result.stdout)
            official_match = execution_accuracy == 1.0

        finally:
            # 5. Clean up files and folders to keep disk usage near zero
            # Files must be deleted before directories
            pred_file.unlink(missing_ok=True)
            gold_file.unlink(missing_ok=True)
            mock_dev_file.unlink(missing_ok=True)
            try:
                pred_dir.rmdir()
                gold_dir.rmdir()
                eval_folder.rmdir()
            except OSError:
                pass # Folder lock / not empty

        return OfficialEvalReport(
            execution_accuracy=execution_accuracy,
            official_match=official_match,
            returncode=exec_result.returncode,
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
        )
