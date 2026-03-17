"""
Run evaluation of tool-generated SQL queries.

Input format (per .sql file in tests/input/queries/tools):
- First non-empty line: SQL comment containing the user request
  e.g. -- List all customers with more than 3 orders
- Then, repeated blocks:
  -- <tool name>
  <SQL query ...>
  If the first non-empty line after the tool name is "NONE",
  the tool is treated as unable to handle the request.
"""

import os
import sys
import re
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TESTS_DIR
from src.classes.clients.mysql_client import MySQLClient
from src.classes.domain_states import QuerySession, QueryStatus, Schema, SchemaSource
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.logger import LoggerManager
from tests.output_object import RequestResult


INPUT_DIR = TESTS_DIR / "input" / "queries" / "tools"
OUTPUT_BASE_DIR = TESTS_DIR / "output" / "runs"
DATABASE_NAME = "supermarket"
DEFAULT_MODEL_NAME = "gpt-4o"
REQUEST_FILENAME_MAX_LEN = 60


def _safe_filename(text: str, max_len: int = REQUEST_FILENAME_MAX_LEN) -> str:
    text = text.strip()
    if not text:
        return "request"
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^\w\-]+", "_", text)
    text = text.strip("_")
    if len(text) > max_len:
        text = text[:max_len].rstrip("_")
    return text or "request"


def _parse_tool_queries(path: Path) -> Tuple[str, List[Tuple[str, Optional[str]]]]:
    """
    Returns:
      user_request: str
      queries: list of (tool_name, sql_query)
    """
    lines = path.read_text(encoding="utf-8").splitlines()

    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    if idx >= len(lines):
        raise ValueError(f"Empty SQL file: {path}")

    first_line = lines[idx].strip()
    if not first_line.startswith("--"):
        raise ValueError(
            f"First line must be a SQL comment with the user request: {path}"
        )
    user_request = first_line[2:].strip()
    idx += 1

    queries: List[Tuple[str, Optional[str]]] = []
    current_tool = None
    current_sql: List[str] = []

    def _finalize_block(tool: Optional[str], sql_lines: List[str]) -> None:
        if not tool:
            return
        sql_text = "\n".join(sql_lines).strip()
        if not sql_text:
            queries.append((tool, None))
            return
        if sql_text.upper() == "NONE":
            queries.append((tool, None))
            return
        queries.append((tool, sql_text))

    for line in lines[idx:]:
        stripped = line.strip()
        if stripped.startswith("--"):
            _finalize_block(current_tool, current_sql)
            current_tool = stripped[2:].strip()
            current_sql = []
            continue

        if current_tool is None:
            continue

        current_sql.append(line)

    _finalize_block(current_tool, current_sql)

    return user_request, queries


def _build_schema_store(tmp_dir: Path) -> SchemaStore:
    schema_dir = tmp_dir / "schema"
    vector_dir = tmp_dir / "vector_stores"

    schema = Schema(
        database_name=DATABASE_NAME,
        schema_source=SchemaSource.MYSQL,
        path=schema_dir,
    )

    db_client = MySQLClient(database=DATABASE_NAME)
    schema_dict = db_client.extract_schema()
    schema.parse_response(schema_dict)
    db_client.close_connection()

    schema_store = SchemaStore(vector_dir)
    schema_store.add_schema(schema)
    return schema_store


def _process_file(
    file_index: int,
    file_path: Path,
    output_dir: Path,
    schema_store: SchemaStore,
) -> None:
    user_request, tool_queries = _parse_tool_queries(file_path)

    db_client = MySQLClient(database=DATABASE_NAME)
    orch = QueryOrchestrator(
        database_name=DATABASE_NAME,
        schema_store=schema_store,
        model_name=DEFAULT_MODEL_NAME,
        database_client=db_client,
        query_store=None,
        max_attempts=1,
        instance_path=TESTS_DIR / "tmp",
        testing=True,
    )

    # Initialize schema context once for this request
    orch._init_generation_context(user_request)

    results: List[RequestResult] = []

    for idx, (tool_name, sql) in enumerate(tool_queries, start=1):
        if sql is None:
            results.append(
                RequestResult(
                    request_index=idx,
                    model_name=tool_name,
                    query_session=None,
                    time_taken=0.0,
                    success=False,
                )
            )
            continue
        start_time = time.time()
        try:
            session = QuerySession(user_request=user_request, sql_query=sql)
            result_session = orch.evaluation(session, 0)
            elapsed = time.time() - start_time
            results.append(
                RequestResult(
                    request_index=idx,
                    model_name=tool_name,
                    query_session=result_session,
                    time_taken=elapsed,
                    success=True,
                )
            )
        except Exception as exc:
            elapsed = time.time() - start_time
            failed_session = QuerySession(user_request=user_request, sql_query=sql)
            failed_session.execution_result = str(exc)
            failed_session.status = QueryStatus.RUNTIME_ERROR
            results.append(
                RequestResult(
                    request_index=idx,
                    model_name=tool_name,
                    query_session=failed_session,
                    time_taken=elapsed,
                    success=False,
                )
            )

    db_client.close_connection()

    safe_req = _safe_filename(user_request)
    output_name = f"{file_index}_{safe_req}.txt"
    output_path = output_dir / output_name

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"[Request]\n{user_request}\n\n")
        f.write(f"Source file: {file_path.name}\n\n")
        if not results:
            f.write("No tool queries found in this file.\n")
            return
        for idx, res in enumerate(results, start=1):
            if res.query_session is None:
                f.write(f"{idx}. [{res.model_name}]\n\n")
                f.write("the tool wasn't able to handle the request\n\n")
                continue
            f.write(res.format_output_content(idx))
            f.write("\n\n")


def main() -> None:
    LoggerManager.setup_project_logger()

    if not INPUT_DIR.exists():
        print(f"Input folder not found: {INPUT_DIR}")
        return

    sql_files = sorted(INPUT_DIR.glob("*.sql"))
    if not sql_files:
        print(f"No .sql files found in: {INPUT_DIR}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_BASE_DIR / f"runs_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir = TESTS_DIR / "tmp" / f"tools_eval_{timestamp}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    schema_store = _build_schema_store(tmp_dir)

    for file_index, file_path in enumerate(sql_files, start=1):
        t = threading.Thread(
            target=_process_file,
            args=(file_index, file_path, output_dir, schema_store),
            name=f"tool_eval_{file_index}",
        )
        t.start()
        t.join()

    print(f"Done. Output written to: {output_dir}")


if __name__ == "__main__":
    main()
