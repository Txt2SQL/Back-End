import os, re, subprocess, sys, threading, hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path

from src.classes.domain_states import QuerySession
from src.classes.logger import LoggerManager
from config import TMP_DIR
from .base_dataset import BaseDataset, OfficialEvalReport

# ---------------------------------------------------------
# SHARED DIRECTORY CONFIGURATION
# ---------------------------------------------------------
NLTK_DATA_DIR = TMP_DIR / "nltk_data"
SPIDER_EVAL_DIR = TMP_DIR / "spider_eval"

# ---------------------------------------------------------
# NLTK HANDLING: Isolated utility class
# ---------------------------------------------------------
class NLTKResourceManager:
    _lock = threading.Lock()
    _ready = False

    @classmethod
    def get_env(cls, logger) -> dict[str, str]:
        """Ensures resources exist and returns the modified environment dictionary."""
        if not cls._ready:
            with cls._lock:
                if not cls._ready:
                    cls._setup(logger)
        
        env = os.environ.copy()
        existing = env.get("NLTK_DATA", "").strip()
        search_paths = [str(NLTK_DATA_DIR)] + ([existing] if existing else [])
        env["NLTK_DATA"] = os.pathsep.join(search_paths)
        return env

    @classmethod
    def _setup(cls, logger) -> None:
        logger.info(f"Ensuring NLTK resources in {NLTK_DATA_DIR}")
        NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)

        import nltk
        from nltk.data import find
        
        punkt_tab_path = "tokenizers/punkt_tab/english/"
        try:
            find(punkt_tab_path, paths=[str(NLTK_DATA_DIR)])
        except LookupError:
            try:
                nltk.download("punkt_tab", download_dir=str(NLTK_DATA_DIR), quiet=True, raise_on_error=True)
            except Exception as exc:
                logger.warning(f"Failed to download punkt_tab ({exc}). Using offline fallback.")
                from nltk.tokenize.punkt import PunktParameters, save_punkt_params
                punkt_tab_dir = NLTK_DATA_DIR / "tokenizers" / "punkt_tab" / "english"
                punkt_tab_dir.mkdir(parents=True, exist_ok=True)
                save_punkt_params(PunktParameters(), dir=str(punkt_tab_dir))

        cls._ready = True

class SpiderDataset(BaseDataset):
    
    def __init__(self) -> None:
        super().__init__("spider")

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

        # Unified type map (handles both Spider and BIRD types)
        type_map = {
            "text": "TEXT",
            "integer": "INTEGER",
            "number": "NUMERIC", # Covers both Spider's 'number' and BIRD's 'number'
            "real": "REAL",
            "date": "DATE",
            "datetime": "DATETIME",
            "time": "TIME",
            "boolean": "BOOLEAN",
        }

        tables = {table_name: [] for table_name in table_names}

        # Separate flat vs composite primary keys (BIRD uses composite, Spider uses flat)
        flat_primary_keys: set[int] = set()
        composite_primary_keys: list[tuple[int, ...]] = []
        
        for pk in primary_keys:
            if isinstance(pk, (list, tuple)):
                composite_primary_keys.append(tuple(pk))
            else:
                flat_primary_keys.add(pk)

        # 1. Process all columns
        for idx, ((table_id, col_name), col_type) in enumerate(zip(column_names, column_types)):
            if table_id == -1: # -1 indicates the generic '*' column
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

        # 2. Append composite primary key constraints (Mostly for BIRD)
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
        for index, example in enumerate(self.dev):
            if example["db_id"] == db_id and example["question"] == question:
                return index
        raise ValueError(f"Question not found for db_id={db_id!r} question={question!r}")

    def _get_gold_sql(self, db_id: str, question: str) -> str:
        for example in self.dev:
            if example["db_id"] == db_id and example["question"] == question:
                return example["SQL"]
        raise ValueError(f"Gold SQL not found for db_id={db_id!r} question={question!r}")

    def _build_spider_command(self, gold_file: Path, pred_file: Path) -> list[str]:
        return [
            sys.executable, str(self.eval_file),
            "--gold", str(gold_file),
            "--pred", str(pred_file),
            "--etype", "exec",
            "--db", str(self.db_dir),
            "--table", str(self.path / "tables.json"),
        ]

    def _extract_metric(self, output: str, metric_name: str) -> float:
        for line in output.lower().splitlines():
            if line.startswith(metric_name.lower()) or (metric_name.lower() == "execution accuracy" and line.startswith("execution")):
                numbers = re.findall(r"[0-9]*\.?[0-9]+", line)
                if numbers:
                    return float(numbers[-1])
        return 0.0
    
    def dataset_evaluation(
        self, 
        predicted_query: QuerySession, 
        gold_query: QuerySession, 
        db_id: str, 
        question_index: int,
        model_name: str,
    ) -> OfficialEvalReport:
        
        normalized_gold = gold_query.normalize_sql()
        normalized_pred = predicted_query.normalize_sql()
        nltk_env = NLTKResourceManager.get_env(self.logger)

        self.logger.info(f"Running Spider eval for db_id={db_id} question_index={question_index}")

        # 1. Generate unique hash ID (e.g., "e4d909c290d0")
        hash_input = f"{model_name}_{db_id}_{question_index}"
        hash_id = hashlib.md5(hash_input.encode("utf-8")).hexdigest()[:12]

        # 2. Create the unique evaluation folder inside the shared SPIDER_EVAL_DIR
        eval_folder = SPIDER_EVAL_DIR / hash_id
        eval_folder.mkdir(parents=True, exist_ok=True)

        gold_file = eval_folder / "gold.sql"
        pred_file = eval_folder / "pred.sql"

        try:
            # 3. Write directly to the unique folder
            gold_file.write_text(f"{normalized_gold}\t{db_id}\n", encoding="utf-8")
            pred_file.write_text(f"{normalized_pred}\n", encoding="utf-8")

            command = self._build_spider_command(gold_file, pred_file)

            exec_result = subprocess.run(
                command, capture_output=True, text=True, check=False, env=nltk_env
            )

            execution_accuracy = self._extract_metric(exec_result.stdout, "Execution Accuracy")
            official_match = execution_accuracy == 1.0
            
        finally:
            # 4. Clean up the SQL files and the hash folder to avoid cluttering the disk
            # (Remove these three lines if you want to keep the files for manual debugging)
            gold_file.unlink(missing_ok=True)
            pred_file.unlink(missing_ok=True)
            try:
                eval_folder.rmdir()
            except OSError:
                pass # Folder not empty or OS lock

        # Return the strongly typed Dataclass
        return OfficialEvalReport(
            execution_accuracy=execution_accuracy,
            official_match=official_match,
            returncode=exec_result.returncode,
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
        )