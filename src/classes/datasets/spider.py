import os, re, subprocess, sys, tempfile, threading, json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from src.classes.logger import LoggerManager
from config import TMP_DIR
from .base_dataset import BaseDataset, OfficialEvalReport

NLTK_DATA_DIR = TMP_DIR / "nltk_data"

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
    _nltk_setup_lock = threading.Lock()
    _nltk_resources_ready = False
    
    def __init__(self) -> None:
        super().__init__("spider")

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)
    
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

    def _get_spider_evaluations_dir(self) -> Path:
        for handler in self.logger.handlers:
            if base_filename := getattr(handler, "baseFilename", None):
                spider_eval_dir = Path(base_filename).resolve().parent / "spider_evaluations"
                spider_eval_dir.mkdir(parents=True, exist_ok=True)
                return spider_eval_dir
        
        fallback_dir = TMP_DIR / "spider_eval"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir

    def _build_execution_stem(self) -> str:
        # Simplified string generation logic
        request_index = LoggerManager.get_request_index() or "unknown"
        match = re.search(r"(\d+)", request_index)
        req_prefix = f"request_{match.group(1)}" if match else f"request_{re.sub(r'[^A-Za-z0-9_-]+', '_', request_index).strip('_')}"
        
        model_name = next((Path(getattr(h, "baseFilename")).stem for h in self.logger.handlers if getattr(h, "baseFilename", None)), "unknown_model")
        
        return f"{req_prefix}_{model_name}"
    
    def dataset_evaluation(
        self,
        predicted_sql: str, 
        gold_sql: str, 
        db_id: str, 
        question: Optional[str] = None
    ) -> OfficialEvalReport: # 2. Return Type clearly defined
        
        execution_stem = self._build_execution_stem()
        report_file = self._get_spider_evaluations_dir() / f"{execution_stem}.json"

        normalized_gold = self._normalize_sql(gold_sql)
        normalized_pred = self._normalize_sql(predicted_sql)
        nltk_env = NLTKResourceManager.get_env(self.logger) # 1. Cleaned up NLTK call

        self.logger.info(f"Running Spider eval for db_id={db_id}")

        # 3. TMP Folder Management: Clean Context Manager
        with tempfile.TemporaryDirectory(prefix=f"{execution_stem}_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            gold_file, pred_file = temp_dir / "gold.sql", temp_dir / "pred.sql"

            gold_file.write_text(f"{normalized_gold}\t{db_id}\n", encoding="utf-8")
            pred_file.write_text(f"{normalized_pred}\n", encoding="utf-8")

            command = self._build_spider_command(gold_file, pred_file)

            exec_result = subprocess.run(
                command, capture_output=True, text=True, check=False, env=nltk_env
            )

            execution_accuracy = self._extract_metric(exec_result.stdout, "Execution Accuracy")
            official_match = execution_accuracy == 1.0

            # 4. LOG FILE CONTENT: Structured JSON Logging
            report_data = {
                "metadata": {
                    "database": db_id,
                    "question": question,
                    "official_match": official_match,
                    "returncode": exec_result.returncode,
                    "execution_accuracy": execution_accuracy,
                    "command": " ".join(command)
                },
                "sql": {
                    "gold": normalized_gold,
                    "predicted": normalized_pred
                },
                "output": {
                    "stdout": exec_result.stdout.strip() if exec_result.stdout else "",
                    "stderr": exec_result.stderr.strip() if exec_result.stderr else ""
                }
            }
            
            report_file.write_text(json.dumps(report_data, indent=4), encoding="utf-8")

        self.logger.info(f"Spider evaluation report written to {report_file}")

        # Return the strongly typed Dataclass
        return OfficialEvalReport(
            execution_accuracy=execution_accuracy,
            official_match=official_match,
            returncode=exec_result.returncode,
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
            report_file=str(report_file)
        )