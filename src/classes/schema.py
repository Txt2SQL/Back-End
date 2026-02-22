import json
import re
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class Schema:

    def __init__(
        self,
        database_name: str,
        schema_source: str,  # "mysql" or "text"
    ):
        self.database_name = database_name
        self.schema_source = schema_source
        self.save_path = Path("data/schema")

        self.file_path = self.save_path / f"{self.database_name}.json"

        self.tables: Optional[Dict] = None
        self.json_ready: bool = False
        self.schema_id: Optional[str] = None

        # -------------------------------------------------
        # 1️⃣ If JSON already exists → load it
        # -------------------------------------------------
        if self.file_path.exists():
            self._load_existing()

    # =====================================================
    # LLM RESPONSE PARSING
    # =====================================================

    def parse_llm_response(self, text: str):
        attempts = [
            self._attempt_direct_json,
            self._attempt_fenced_block,
            self._attempt_widest_json,
        ]

        for attempt in attempts:
            parsed = attempt(text)
            if parsed:
                if self._validate_structure(parsed):
                    self.tables = parsed
                    self.json_ready = True
                    self._save_schema()
                    return

        raise ValueError("Failed to extract valid schema JSON from LLM response.")

    # =====================================================
    # LOAD EXISTING
    # =====================================================

    def _load_existing(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.tables = json.load(f)

        if self.tables is not None:
            self.json_ready = True
            self.schema_id = self._compute_hash(self.tables)
        else:
            raise ValueError("Loaded schema is empty, cannot compute hash.")

    # -----------------------------------------------------

    def _attempt_direct_json(self, text: str):
        try:
            return json.loads(text)
        except Exception:
            return None

    def _attempt_fenced_block(self, text: str):
        pattern = r"```(?:json)?\s*(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except Exception:
                continue
        return None

    def _attempt_widest_json(self, text: str):
        json_candidates = re.findall(r"\{.*\}", text, re.DOTALL)
        if not json_candidates:
            return None

        widest = max(json_candidates, key=len)

        try:
            return json.loads(widest)
        except Exception:
            return None

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_structure(self, data: Dict[str, Any]) -> bool:
        if "tables" not in data:
            return False

        if not isinstance(data["tables"], list):
            return False

        for table in data["tables"]:
            if "name" not in table or "columns" not in table:
                return False

            for column in table["columns"]:
                if not all(k in column for k in ["name", "type", "constraints"]):
                    return False

        if "semantic_notes" not in data:
            data["semantic_notes"] = []

        return True

    # =====================================================
    # SAVE
    # =====================================================

    def _save_schema(self):
        if self.tables is None:
            raise ValueError("Cannot save an empty schema.")
            
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.tables, f, indent=2)

        self.schema_id = self._compute_hash(self.tables) if self.tables is not None else None

        print("\nSchema successfully saved:")
        print(json.dumps(self.tables, indent=2))
        print(f"\nSchema ID: {self.schema_id}")

    # =====================================================
    # HASH
    # =====================================================

    def _compute_hash(self, data: Dict) -> str:
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    # =====================================================
    # RAG DOCUMENT
    # =====================================================

    def to_document(self) -> Dict[str, Any]:
        """
        Convert schema into a document for vector store.
        """

        if self.tables is None or "tables" not in self.tables:
            raise ValueError("Schema tables are not loaded or are empty.")

        content = f"Database: {self.database_name}\n\n"

        for table in self.tables["tables"]:
            content += f"Table: {table['name']}\n"
            for column in table["columns"]:
                constraints = ", ".join(column["constraints"])
                content += (
                    f"  - {column['name']} ({column['type']}) [{constraints}]\n"
                )
            content += "\n"

        if self.tables.get("semantic_notes"):
            content += "Semantic Notes:\n"
            for note in self.tables["semantic_notes"]:
                content += f"- {note}\n"

        return {
            "id": self.schema_id,
            "content": content,
            "metadata": {
                "database_name": self.database_name,
                "schema_source": self.schema_source,
                "created_at": datetime.utcnow().isoformat(),
            },
        }