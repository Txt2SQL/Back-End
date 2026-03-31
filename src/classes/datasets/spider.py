import os, re, subprocess, sys, tempfile, threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Optional
from pathlib import Path

from src.classes.logger import LoggerManager
from config import TMP_DIR
from .base_dataset import BaseDataset

NLTK_DATA_DIR = TMP_DIR / "nltk_data"
SPIDER_EVAL_TMP_DIR = TMP_DIR / "spider_eval"


class SpiderDataset(BaseDataset):
    _nltk_setup_lock = threading.Lock()
    _nltk_resources_ready = False
    
    def __init__(self) -> None:
        super().__init__("spider")

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)


    def get_requests(self, db_name: str) -> list[str]:
        return [item["question"] for item in self.dev if item["db_id"] == db_name]

    def get_schema(self, db_name: str) -> dict:
        spider_schema = next(
            (schema for schema in self.tables if schema["db_id"] == db_name),
            None,
        )
        if spider_schema is None:
            raise ValueError(f"Schema not found for db: {db_name}")

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

    def _ensure_local_punkt_tab(self) -> None:
        from nltk.tokenize.punkt import PunktParameters, save_punkt_params

        punkt_tab_dir = NLTK_DATA_DIR / "tokenizers" / "punkt_tab" / "english"
        punkt_tab_dir.mkdir(parents=True, exist_ok=True)
        save_punkt_params(PunktParameters(), dir=str(punkt_tab_dir))
        self.logger.warning(
            "Created offline fallback NLTK punkt_tab resource in %s",
            punkt_tab_dir,
        )

    def _ensure_nltk_resources(self) -> None:
        if self.__class__._nltk_resources_ready:
            return

        with self.__class__._nltk_setup_lock:
            if self.__class__._nltk_resources_ready:
                return

            self.logger.info("Ensuring NLTK resources for Spider evaluation in %s", NLTK_DATA_DIR)
            NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)

            import nltk
            from nltk.data import find

            punkt_tab_path = "tokenizers/punkt_tab/english/"
            try:
                find(punkt_tab_path, paths=[str(NLTK_DATA_DIR)])
                self.logger.debug("NLTK resource already available: punkt_tab")
            except LookupError:
                self.logger.info("Downloading missing NLTK resource: punkt_tab")
                try:
                    nltk.download(
                        "punkt_tab",
                        download_dir=str(NLTK_DATA_DIR),
                        quiet=True,
                        raise_on_error=True,
                    )
                    find(punkt_tab_path, paths=[str(NLTK_DATA_DIR)])
                    self.logger.info("Downloaded NLTK resource: punkt_tab")
                except Exception as exc:
                    self.logger.warning(
                        "Unable to download punkt_tab (%s). Falling back to a local minimal tokenizer dataset.",
                        exc,
                    )
                    self._ensure_local_punkt_tab()
                    find(punkt_tab_path, paths=[str(NLTK_DATA_DIR)])

            self.__class__._nltk_resources_ready = True
            self.logger.info("NLTK resources ready for Spider evaluation")

    def _build_spider_command(self, gold_file: Path, pred_file: Path) -> list[str]:
        return [
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
        ]

    def _extract_metric(self, output: str, metric_name: str) -> Optional[float]:
        metric_name_normalized = metric_name.strip().lower()

        for line in output.splitlines():
            normalized_line = line.strip().lower()
            if normalized_line.startswith(metric_name_normalized):
                numbers = re.findall(r"[0-9]*\.?[0-9]+", line)
                if numbers:
                    return float(numbers[-1])

            if (
                metric_name_normalized == "execution accuracy"
                and normalized_line.startswith("execution")
            ):
                numbers = re.findall(r"[0-9]*\.?[0-9]+", line)
                if numbers:
                    return float(numbers[-1])

        return None

    def _get_spider_evaluations_dir(self) -> Path:
        logger = self.logger
        for handler in logger.handlers:
            base_filename = getattr(handler, "baseFilename", None)
            if base_filename:
                logs_dir = Path(base_filename).resolve().parent
                spider_eval_dir = logs_dir / "spider_evaluations"
                spider_eval_dir.mkdir(parents=True, exist_ok=True)
                return spider_eval_dir

        fallback_dir = TMP_DIR / "spider_eval"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir

    def _get_model_name_for_report(self) -> str:
        logger = self.logger
        for handler in logger.handlers:
            base_filename = getattr(handler, "baseFilename", None)
            if base_filename:
                return Path(base_filename).stem
        return "unknown_model"

    def _get_request_prefix_for_report(self) -> str:
        request_index = LoggerManager.get_request_index()
        if not request_index:
            return "request_unknown"

        match = re.search(r"(\d+)", request_index)
        if match:
            return f"request_{match.group(1)}"

        sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", request_index).strip("_")
        return sanitized or "request_unknown"

    def _build_execution_stem(self) -> str:
        request_prefix = self._get_request_prefix_for_report()
        model_name = self._get_model_name_for_report()
        return f"{request_prefix}_{model_name}"
    
    def dataset_evaluation(
        self,
        predicted_sql: str, 
        gold_sql: str, 
        db_id: str, 
        question: Optional[str] = None
    ) -> dict:
        SPIDER_EVAL_TMP_DIR.mkdir(parents=True, exist_ok=True)

        execution_stem = self._build_execution_stem()
        report_file = self._get_spider_evaluations_dir() / f"{execution_stem}.log"

        normalized_gold_sql = self._normalize_sql(gold_sql)
        normalized_predicted_sql = self._normalize_sql(predicted_sql)
        nltk_env = self._build_nltk_env()

        self.logger.info(
            "Running Spider dataset evaluation for db_id=%s question=%r",
            db_id,
            question,
        )
        self._ensure_nltk_resources()
        self.logger.debug("Spider evaluation NLTK_DATA=%s", nltk_env.get("NLTK_DATA"))
        self.logger.debug("Spider evaluation gold SQL: %s", normalized_gold_sql)
        self.logger.debug("Spider evaluation predicted SQL: %s", normalized_predicted_sql)
        self.logger.debug("Spider evaluation report file: %s", report_file)

        temp_dir_cleaned = False
        with tempfile.TemporaryDirectory(
            dir=SPIDER_EVAL_TMP_DIR,
            prefix=f"{execution_stem}_",
        ) as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            gold_file = temp_dir / "gold.sql"
            pred_file = temp_dir / "pred.sql"

            gold_file.write_text(
                f"{normalized_gold_sql}\t{db_id}\n",
                encoding="utf-8",
            )
            pred_file.write_text(
                f"{normalized_predicted_sql}\n",
                encoding="utf-8",
            )

            command = self._build_spider_command(gold_file, pred_file)
            self.logger.debug("Spider evaluation command: %s", " ".join(command))
            self.logger.debug("Spider evaluation temp dir: %s", temp_dir)

            exec_result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                env=nltk_env,
            )

            execution_accuracy = self._extract_metric(exec_result.stdout, "Execution Accuracy")
            official_match = execution_accuracy == 1.0
            self.logger.info(
                "Spider evaluator finished with returncode=%s execution_accuracy=%s official_match=%s",
                exec_result.returncode,
                execution_accuracy,
                official_match,
            )
            if exec_result.stdout:
                self.logger.debug("Spider evaluator stdout:\n%s", exec_result.stdout.strip())
            if exec_result.stderr:
                self.logger.debug("Spider evaluator stderr:\n%s", exec_result.stderr.strip())

            report_file.write_text(
                "\n".join(
                    [
                        "=== Metadata ===",
                        f"Database: {db_id}",
                        f"Question: {question}",
                        f"Official match: {official_match}",
                        f"Return code: {exec_result.returncode}",
                        f"Execution accuracy: {execution_accuracy}",
                        f"Command: {' '.join(command)}",
                        "",
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
                        "=== Temp Files ===",
                        f"Gold file: {gold_file}",
                        f"Pred file: {pred_file}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            temp_dir_cleaned = True

        self.logger.info(
            "Spider evaluation report written to %s (temp_dir_cleaned=%s)",
            report_file,
            temp_dir_cleaned,
        )

        return {
            "exec_result": exec_result,
            "execution_accuracy": execution_accuracy,
            "official_match": official_match,
            "report_file": report_file,
            "returncode": exec_result.returncode,
            "stdout": exec_result.stdout,
            "stderr": exec_result.stderr,
        }
