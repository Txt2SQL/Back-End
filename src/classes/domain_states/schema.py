import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json, re, hashlib, time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from .enums import SchemaSource
from src.classes.logger import LoggerManager


class Schema:

    def __init__(
        self,
        database_name: str,
        schema_source: SchemaSource,  # "mysql" or "text"
        path: Path,
        save_json: bool = True,
    ):
        self.database_name = database_name
        self.source = schema_source
        self.save_json = save_json

        self.file_path = path / f"{self.database_name}_schema.json"

        self.tables: Optional[Dict] = None
        self.semantic_notes: list[str] = []
        self.json_ready: bool = False
        self.schema_id: Optional[str] = None

        # -------------------------------------------------
        # 1️⃣ If JSON already exists → load it
        # -------------------------------------------------
        if self.file_path.exists():
            self._load_existing()
    
    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)
            
    # =====================================================
    # LOADING
    # =====================================================
    
    @classmethod
    def from_json_file(cls, path: Path) -> "Schema":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        schema = cls.__new__(cls)
        schema.database_name = data.get("database_name")
        schema.source = data.get("source", "text")
        schema.file_path = path
        schema.tables = data
        schema.json_ready = True
        schema.schema_id = data.get("schema_id")

        return schema
    
    def _load_existing(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.tables = json.load(f)

        if self.tables is not None:
            self.json_ready = True
            self.schema_id = self.tables.get("schema_id") or self._compute_hash(self.tables)
        else:
            raise ValueError("Loaded schema is empty, cannot compute hash.")

    # =====================================================
    # PARSING
    # =====================================================

    def parse_response(self, text: Any):
        self.logger.info("📝 Starting parsing LLM response...")
        
        if isinstance(text, Dict):
            self.tables = text
            self.json_ready = True
            self._save_schema()
            return

        attempts = [
            self._attempt_direct_json,
            self._attempt_curly_braces,
            self._attempt_fenced_block,
            self._attempt_widest_json,
        ]

        for attempt in attempts:
            self.logger.info("📝 Attempting to parse LLM response with attempts: %s", attempt)
            parsed = attempt(text)
            if parsed:
                self.logger.info("✅ LLM response parsed successfully")
                if self._validate_structure(parsed):
                    self.tables = parsed
                    self.json_ready = True
                    self._save_schema()
                    return
            else:
                self.logger.info("❌ LLM response parsing failed")

        raise ValueError("Failed to extract valid schema JSON from LLM response.")

    def _attempt_direct_json(self, text: str):
        try:
            return json.loads(text)
        except Exception:
            return None
    
    def _attempt_curly_braces(self, text: str):
        try:
            # Find the first { and last }
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = text[start:end]
                # Clean up common issues
                json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass

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
    # SAVING
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

    def _save_schema(self):
        if self.tables is None:
            raise ValueError("Cannot save an empty schema.")
        if not self.save_json:
            return

        final_schema = {
            "database_name": self.database_name,
            "source": self.source,
            "tables": self.tables.get("tables"),
            "semantic_notes": self.semantic_notes,
            "timestamp": time.time(),
        }
        self.schema_id = self._compute_hash(final_schema)
        final_schema["schema_id"] = self.schema_id
        self.tables = final_schema

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(final_schema, f, indent=2)

        self.logger.info("\nSchema successfully saved:\n\n")
        self.logger.info(json.dumps(final_schema, indent=2))

    def add_semantic_note(self, note: str):
        if not isinstance(note, str):
            raise ValueError("Semantic note must be a string.")

        normalized_note = note.strip()
        if not normalized_note:
            raise ValueError("Semantic note cannot be empty.")

        self.semantic_notes.append(normalized_note)

    def _compute_hash(self, data: Dict) -> str:
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    # =====================================================
    # UPDATE
    # =====================================================
    def classify_update(self, text: str) -> str:
        """Recognizes if the text describes a structural or semantic modification."""

        sql_keywords = ["CREATE TABLE", "ALTER TABLE", "ADD COLUMN", "DROP TABLE", "FOREIGN KEY", "REFERENCES"]
        desc_keywords = ["means", "can assume", "contains", "represents", "describes", "equivalent to"]

        if any(k.lower() in text.lower() for k in sql_keywords):
            return "structural"
        if any(k.lower() in text.lower() for k in desc_keywords):
            return "semantic"

        return "unknown"

    # =====================================================
    # OUTPUT
    # =====================================================

    def to_documents(self) -> List[Dict[str, Any]]:
        """
        Convert schema into per-table documents for the vector store.
        """

        if self.tables is None or "tables" not in self.tables:
            raise ValueError("Schema tables are not loaded or are empty.")

        schema_id = self.schema_id or self._compute_hash(self.tables)
        created_at = datetime.utcnow().isoformat()
        semantic_notes = self.tables.get("semantic_notes") or []

        documents: List[Dict[str, Any]] = []

        for idx, table in enumerate(self.tables["tables"]):
            table_name = table.get("name", f"table_{idx}")

            content = f"Schema: {self.database_name}\n"
            content += f"Table: {table_name}\n"

            for column in table.get("columns", []):
                constraints = ", ".join(column.get("constraints", []))
                content += f"  - {column.get('name', 'unknown')} ({column.get('type', 'unknown')}) [{constraints}]\n"

            if semantic_notes:
                content += "\nSemantic Notes:\n"
                for note in semantic_notes:
                    content += f"- {note}\n"

            documents.append(
                {
                    "id": f"{schema_id}:{table_name}",
                    "content": content,
                    "metadata": {
                        "database_name": self.database_name,
                        "schema_source": self.source,
                        "schema_id": schema_id,
                        "table": table_name,
                        "created_at": created_at,
                    },
                }
            )

        return documents
        
    def to_string(self):
        return json.dumps(self.tables, indent=2)
        
    def print_schema_preview(self):
        """Prints a readable preview of the canonical schema"""
        print("\n\nCanonical schema preview:\n\n")
        
        if self.tables is None:
            print("No schema loaded")
            return
        
        # Print tables
        if "tables" in self.tables and self.tables["tables"]:
            print(f"\nFound {len(self.tables['tables'])} tables:")
            for i, table in enumerate(self.tables["tables"], 1):
                print(f"\n  Table #{i}: {table.get('name', 'N/A')}")
                
                # Print columns
                if "columns" in table and table["columns"]:
                    print("  Columns:")
                    for col in table["columns"]:
                        constraints = col.get("constraints", [])
                        constraints_str = ", ".join(constraints) if constraints else "no constraints"
                        print(f"    • {col.get('name', 'N/A')} ({col.get('type', 'N/A')}) - {constraints_str}")
                else:
                    print("  No columns defined")
        else:
            print("\nNo tables defined")
        
        # Print semantic notes
        if len(self.semantic_notes) > 0:
            print(f"\nFound {len(self.semantic_notes)} semantic notes:")
            for i, note in self.semantic_notes:
                # Show only first 100 characters for brevity
                preview = note[:100] + "..." if len(note) > 100 else note
                print(f"  {i}. {preview}")
        else:
            print("\nNo semantic notes")