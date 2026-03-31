"""
Run evaluation of tool-generated SQL queries.

Input format (per .sql file in tests/input/queries/tools):
- First non-empty line: SQL comment containing the user request
  e.g. -- List all customers with more than 3 orders
- Then, repeated blocks:
  -- <tool name>
  <SQL query ...>
  If the first non-empty line after the tool name is "NONE" or "NULL",
  the tool is treated as unable to handle the request.
"""

import os
import sys
import re
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TESTS_DIR
from classes.clients.database.mysql_client import MySQLClient
from src.classes.domain_states import QuerySession, QueryStatus, Schema, SchemaSource
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.logger import LoggerManager
from tests.thread_output import RequestResult


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
        upper_text = sql_text.upper().rstrip(";").strip()
        if upper_text in {"NONE", "NULL"}:
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
) -> Tuple[str, List[RequestResult]]:
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
            return user_request, results
        for idx, res in enumerate(results, start=1):
            if res.query_session is None:
                f.write(f"{idx}. [{res.model_name}]\n\n")
                f.write("status and outcome: the tool wasn't able to handle the request\n\n")
                continue
            f.write(res.format_output_content(idx))
            f.write("\n\n")
    print(f"Evaluation of the file {file_path.name} completed")
    return user_request, results


def _write_statistics(
    results_by_index: Dict[int, List[RequestResult]],
    num_requests: int,
    stats_path: Path,
    requests: List[str],
) -> None:
    """Aggregate statistics and write to final_stats.txt."""
    def print_table(title: str, headers: List[str], rows: List[List[str]], footer: Optional[List[str]] = None) -> List[str]:
        """Build an ASCII table and return it as a list of lines."""
        lines: List[str] = []
        lines.append(f"\n{title}")
        lines.append("-" * 60)

        all_data = [headers] + rows
        if footer:
            all_data.append(footer)

        col_widths = [
            max(len(str(cell)) for cell in [row[i] for row in all_data])
            for i in range(len(headers))
        ]

        def format_row(row: List[str]) -> str:
            return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

        lines.append(format_row(headers))
        separator = "-+-".join("-" * w for w in col_widths)
        lines.append(separator)

        for row in rows:
            lines.append(format_row(row))

        if footer:
            lines.append(separator)
            lines.append(format_row(footer))

        return lines

    total_requests = num_requests
    total_tests = 0
    successful_executions = 0
    correct_queries = 0
    incorrect_queries = 0
    runtime_errors = 0
    syntax_errors = 0
    other_errors = 0

    global_total_time = 0.0

    tool_names = sorted(
        {res.model_name for results in results_by_index.values() for res in results}
    )

    tool_stats = {
        tool: {
            "correct": 0,
            "incorrect": 0,
            "runtime": 0,
            "syntax": 0,
            "executions": 0,
            "total_time": 0.0,
            "count": 0,
        }
        for tool in tool_names
    }

    for _, results in results_by_index.items():
        for res in results:
            total_tests += 1
            tool_stats[res.model_name]["executions"] += 1
            if res.success:
                query_session = res.query_session
                successful_executions += 1

                tool_stats[res.model_name]["total_time"] += res.time_taken
                global_total_time += res.time_taken
                tool_stats[res.model_name]["count"] += 1

                status = query_session.status.value if query_session and query_session.status else None

                if status == QueryStatus.SUCCESS.value:
                    correct_queries += 1
                    tool_stats[res.model_name]["correct"] += 1
                elif status == QueryStatus.INCORRECT.value:
                    incorrect_queries += 1
                    tool_stats[res.model_name]["incorrect"] += 1
                elif status == QueryStatus.RUNTIME_ERROR.value:
                    runtime_errors += 1
                    tool_stats[res.model_name]["runtime"] += 1
                elif status == QueryStatus.SYNTAX_ERROR.value:
                    syntax_errors += 1
                    tool_stats[res.model_name]["syntax"] += 1
                else:
                    other_errors += 1
            else:
                other_errors += 1

    time_avg = sorted(
        tool_stats.items(),
        key=lambda x: x[1]["total_time"] / x[1]["count"] if x[1]["count"] > 0 else float("inf"),
    )
    status_rank = sorted(
        tool_stats.items(),
        key=lambda x: (
            -(
                x[1]["correct"] / x[1]["executions"]
                if x[1]["executions"] > 0 else 0
            ),
            -x[1]["correct"],
            x[1]["runtime"],
            x[1]["syntax"],
        ),
    )

    total_correct_percent = (correct_queries / total_tests * 100) if total_tests > 0 else 0
    global_avg_time = (global_total_time / total_tests) if total_tests > 0 else 0

    lines = []
    lines.append("/°" * 50 + "/\n")
    lines.append("📊 TEST SUMMARY")
    lines.append("\n" + "/°" * 50 + "/")
    lines.extend([
        "",
        f"Total requests tested : {total_requests}",
        f"Total tool executions: {total_tests}",
        f"✅ Correct queries : {correct_queries}",
        f"❌ Incorrect queries  : {incorrect_queries}",
        f"⚠️  Syntax errors     : {syntax_errors}",
        f"❌ Runtime errors    : {runtime_errors}",
        f"🔧 Other errors      : {other_errors}",
        f"🟢 Completed runs    : {successful_executions}",
        f"🎯 Total correct %    : {total_correct_percent:.2f}%",
        "",
    ])

    lines.extend(
        print_table(
            "🏁 Status ranking",
            ["Rank", "Tool", "CORRECT", "RUNTIME", "INCORRECT", "CORRECT %"],
            [
                [
                    str(i + 1),
                    tool,
                    str(int(stats["correct"])),
                    str(int(stats["runtime"])),
                    str(int(stats["incorrect"])),
                    f"{(stats['correct'] / stats['executions'] * 100) if stats['executions'] > 0 else 0:.2f}%",
                ]
                for i, (tool, stats) in enumerate(status_rank)
            ],
            footer=[
                "",
                "TOTAL",
                str(correct_queries),
                str(runtime_errors),
                str(incorrect_queries),
                f"{total_correct_percent:.2f}%"
            ]
        )
    )

    best_tool = status_rank[0][0] if status_rank else "N/A"
    lines.append(f"\n🏆 Best overall tool: {best_tool}")
    lines.append("=" * 60)

    with open(stats_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n" + "\n".join(lines))


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

    results_by_index: Dict[int, List[RequestResult]] = {}
    requests: List[str] = []

    for file_index, file_path in enumerate(sql_files, start=1):
        container: Dict[str, Optional[Tuple[str, List[RequestResult]]]] = {"result": None}

        def _runner() -> None:
            container["result"] = _process_file(file_index, file_path, output_dir, schema_store)

        t = threading.Thread(target=_runner, name=f"tool_eval_{file_index}")
        t.start()
        t.join()

        if container["result"] is None:
            continue
        user_request, results = container["result"]
        requests.append(user_request)
        results_by_index[file_index] = results

    stats_path = output_dir / "final_stats.txt"
    _write_statistics(results_by_index, len(requests), stats_path, requests)

    print(f"Done. Output written to: {output_dir}")


if __name__ == "__main__":
    main()
