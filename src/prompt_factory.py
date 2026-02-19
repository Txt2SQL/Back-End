from src.logging_utils import setup_logger

logger = setup_logger(__name__)


def explanation_prompt(sql: str, context: str, execution_output: list | None | str):
    return f"""
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

def evaluation_prompt(sql: str, request: str, context: str, execution_output: str) -> str:

        # Take only the first 20 rows to avoid token explosion
        preview_rows = execution_output[:20]
        logger.debug("Using first %s rows for evaluation", len(preview_rows))

        # Convert rows to a readable string
        rows_text = "\n".join(str(row) for row in preview_rows)

        return f"""
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

def query_generation_prompt(
    user_request: str,
    source: str,
    schema_context: str,
    previous_fail: str | None, # penalties or error feedback from previous attempts
    join_hints: str | None,
) -> str:
    """
    Create prompt for SQL generation.
    """
    logger.info("Creating prompt for request: '%s', source: %s", user_request, source)

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
        template = template + f"""
{join_hints}
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
        template = template + f"""
=== PREVIOUS QUERY ERROR TO FIX ===
{previous_fail}

You must correct the query considering this error.
Do NOT repeat the same mistake.
"""

    return template + f"""

Before writing the SQL query, internally determine:
- Which tables are required
- How they are joined
- Whether aggregation or grouping is required
- Which columns are selected

Do NOT output this reasoning.
Only output the final SQL query.
    
SQL QUERY (DO NOT ADD COMMENTS OR EXPLANATION TEXT BEFORE AND AFTER THE QUERY):
"""

def schema_generation_prompt(raw_schema_text: str) -> str:
    """
    Create prompt for schema generation.
    """
    return f"""
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

def schema_update_prompt(raw_schema_text: str, current_schema: str) -> str:
    """
    Create prompt for schema update.
    """
    return f"""
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