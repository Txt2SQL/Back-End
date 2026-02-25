from datetime import datetime
from src.logging_utils import setup_logger
from langchain_core.documents import Document
from classes.domain_states.query import QuerySession
from .logger_manager import LoggerManager
from src.config import LOGGER_LEVEL

logger = LoggerManager.get_logger(__name__)

class PromptBuilder:
    """
    Responsible only for building LLM prompts.
    No execution logic.
    """

    def __init__(self):
        self.timestamp = datetime.utcnow().isoformat()

    def explanation_prompt(self, sql: str, context: str, execution_output: str):
        template = f"""
    You are an expert SQL debugger.
    Explain why the following SQL query produced this runtime error.
    Be concise and do NOT rewrite the query.

    --- CONTEXT ---
    {context}

    --- SQL QUERY ---
    {sql}

    --- RUNTIME ERROR ---
    {execution_output}

    Provide a clear explanation of the cause.
    """
        self._log_prompt("explanation_prompt", template)
        return template

    def evaluation_prompt(self, sql: str, request: str, context: str, execution_output: list) -> str:
        # Take only the first 20 rows to avoid token explosion
        preview_rows = execution_output[:20]
        logger.debug("Using first %s rows for evaluation", len(preview_rows))

        # Convert rows to a readable string
        rows_text = "\n".join(str(row) for row in preview_rows)

        template = f"""
You are an expert SQL reviewer.

Your task is to evaluate whether the SQL query correctly answers
the user's request, based ONLY on the query results shown.

--- CONTEXT ---
{context}

--- USER REQUEST ---
{request}

--- SQL QUERY ---
{sql}

--- QUERY RESULT (first 20 rows) ---
{rows_text}

--- INSTRUCTIONS ---
Respond in EXACTLY one of the following formats:

1) If the query is correct:
CORRECT_QUERY

2) If the query is incorrect:
INCORRECT_QUERY: <clear explanation of what is wrong and how to fix it>

Rules:
- Do NOT rewrite the full SQL query.
- Be concise and precise.
- Judge correctness, not syntax or performance.
"""
        self._log_prompt("evaluation_prompt", template)
        return template

    def query_generation_prompt(self, 
        user_request: str,
        schema_context: str,
        previous_fail: list[Document] | QuerySession | None, # penalties or error feedback from previous attempts
        join_hints: list[str] | None,
    ) -> str:
        """
        Create prompt for SQL generation.
        """
        logger.info("Creating prompt for request: '%s'", user_request)

        logger.debug("Schema context length: %s characters", len(schema_context))

        template = f""" 
    You are an expert SQL database assistant.
    You will be provided with:
    1. The partial description of the database schema (only the relevant tables)
    2. The user's request in natural language.
    3. Examples of previous successful SQL queries

    Your task is to return a **single SQL query** that satisfies the request,
    using the provided tables and columns.

    === SCHEMA ===
    {schema_context}
    
    """    
        if join_hints:
            penalty_section = self._build_relation_section(join_hints)
            template = template + f"""
    {penalty_section}
    """

        template = template + f"""

    === REQUEST ===
    {user_request}

    IMPORTANT CONSTRAINTS BASED ON PAST FAILURES:
    - Do NOT use columns outside the schema
    - Do NOT invent field or table names that don't exist.
    - Always qualify columns when joining
    - Do NOT use SELECT *
    - Do NOT add WHERE clauses or conditions unless explicitly requested.
    - Do NOT join tables unless necessary for the request.
    - If using aggregates, include GROUP BY  
    """
    
        if previous_fail:
            if isinstance(previous_fail, list):
                fail_content = self._build_penalty_section(previous_fail)
            elif isinstance(previous_fail, QuerySession):
                fail_content = previous_fail.format_error_feedback()

            template = template + f"""
    === PREVIOUS QUERY ERROR TO FIX ===
    {fail_content}

    You must correct the query considering this error.
    Do NOT repeat the same mistake.
    """

        template = template + f"""

    Before writing the SQL query, internally determine:
    - Which tables are required
    - How they are joined
    - Whether aggregation or grouping is required
    - Which columns are selected

    Do NOT output this reasoning.
    Only output the final SQL query.
        
    SQL QUERY (DO NOT ADD COMMENTS OR EXPLANATION TEXT BEFORE AND AFTER THE QUERY):
    """
        self._log_prompt("query_generation_prompt", template)
        return template

    def schema_generation_prompt(self) -> str:
        """
        Create prompt for schema generation.
        """
        template = """
    You are an expert database schema analyzer. Your task is to convert SQL DDL statements into a structured JSON schema.

    IMPORTANT:
    - You MUST return ONLY valid JSON.
    - The JSON must be syntactically correct (no missing commas, braces, or quotes).
    - Every object and array must be properly closed.
    - Do NOT include comments, code blocks, or explanations.

    Required JSON format:
    {{
    "tables": [
        {{
        "name": "table_name",
        "columns": [
            {{"name": "column_name", "type": "SQL_TYPE", "constraints": ["PRIMARY KEY", "NOT NULL", ...]}}
        ]
        }}
    ],
    "semantic_notes": []
    }}

    Rules:
    - Extract table names from CREATE TABLE statements
    - Extract column names, types, and constraints
    - Map SQL types directly (VARCHAR2 → VARCHAR2, NUMBER → NUMBER, etc.)
    - Include constraints like PRIMARY KEY, NOT NULL, UNIQUE, DEFAULT, REFERENCES
    - For foreign keys, use "REFERENCES" constraint

    SQL DDL to process:
    \"\"\"{raw_schema_text}\"\"\"

    Return ONLY the JSON object:
    """
        self._log_prompt("schema_generation_prompt", template)
        return template

    def schema_update_prompt(self, raw_schema_text: str, current_schema: str) -> str:
        """
        Create prompt for schema update.
        """
        template = f"""
    You are an expert database schema analyst.

    You have been provided with:
    1. The CURRENT canonical schema (JSON format)
    2. NEW text describing additional tables or modifications to existing tables

    Your task:
    - Analyze the new text to identify any NEW tables or MODIFIED columns in existing tables
    - Preserve all existing tables and columns from the current schema
    - Add only the NEW tables or merge modifications into existing tables
    - Return a SINGLE, complete JSON schema that includes both the current schema and the updates

    IMPORTANT RULES:
    - Do NOT remove any existing tables or columns
    - If a table already exists, ADD new columns or UPDATE existing ones (don't duplicate)
    - Maintain the same JSON structure: {{"database": "<database_name>", "tables": [...], "semantic_notes": [...]}}
    - Return ONLY the updated JSON schema, no other text or explanations
    - Each table must have: "name", "columns" (array)
    - Each column must have: "name", "type", "constraints" (array)

    === CURRENT SCHEMA ===
    {current_schema}

    === NEW TEXT ===
    {raw_schema_text}

    Return the UPDATED schema JSON:
    """
        self._log_prompt("schema_update_prompt", template)
        return template

    def update_classification_prompt(self, text: str) -> str:
        """
        Create prompt for error classification.
        """
        template = f"""
    System: You are an assistant that classifies schema updates.
    User: Text provided by the user:
    {text}

    Question: is this text
    (A) a structural modification (addition or change of tables/columns/types)?
    (B) a description or semantic note?
    Answer only with "A" or "B".
    """
        self._log_prompt("update_classification_prompt", template)
        return template
    
    def _build_penalty_section(self, failed_queries: list[Document]) -> str:
        if not failed_queries:
            logger.info("ℹ️ No failed queries to build penalties.")
            return ""

        lines = []

        for d in failed_queries:
            error_type = d.metadata.get("error_type")
            content = d.page_content

            lines.append(f"""
    --- FAILURE ---
    {content}

    Error type: {error_type}
    """)

            if error_type == "UNKNOWN_COLUMN":
                lines.append("RULE: Do NOT use columns that are not present in the schema.")
            elif error_type == "UNKNOWN_TABLE":
                lines.append("RULE: Do NOT reference tables not present in the schema.")
            elif error_type == "AMBIGUOUS_COLUMN":
                lines.append("RULE: Always qualify column names with table aliases.")
            elif error_type == "BAD_JOIN":
                lines.append("RULE: Avoid unnecessary joins.")
            else:
                lines.append("RULE: Avoid repeating this query structure.")

        logger.info(f"📋 Penalty section built for {len(failed_queries)} failures.")
        return "\n".join(lines)
    
    def _build_relation_section(self, relations: list[str]) -> str:
        if not relations:
            return ""

        if relations:
            filtered = []
            for relation in relations:
                try:
                    left, right = relation.split("→")
                    left_table = left.strip().split(".", 1)[0].strip()
                    right_table = right.strip().split(".", 1)[0].strip()
                except ValueError:
                    continue

                if left_table in relations and right_table in relations:
                    filtered.append(relation)

            relations = filtered

        if not relations:
            return ""

        lines = ["=== JOIN PATH HINTS ==="]
        for i, r in enumerate(relations, 1):
            lines.append(f"{i:2}. {r}")

        return "\n".join(lines)

    def _log_prompt(self, name: str, prompt: str) -> None:
        """
        Logs the full prompt only if DEBUG level is enabled.
        """
        if logger.isEnabledFor(LOGGER_LEVEL):
            logger.debug(
                "\n\n===== GENERATED PROMPT: %s =====\n%s\n===== END PROMPT =====\n",
                name,
                prompt
            )