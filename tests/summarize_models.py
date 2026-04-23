import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

def _safe_get(data: Dict[str, Any], *keys: str, default: Optional[str] = "N/A") -> Any:
    """Safely retrieve nested dictionary values."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data

def generate_markdown_report(base_dir: Path, model_name: str) -> str:
    """Iterates through database folders and builds a markdown summary for a specific model."""
    
    rows: List[List[str]] = []

    # Sort directories alphabetically for a cleaner report
    db_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir()])

    for db_dir in db_dirs:
        stats_file = db_dir / "final_stats.json"
        
        if not stats_file.exists():
            print(f"Warning: {stats_file} not found. Skipping {db_dir.name}.")
            continue

        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {stats_file}. Skipping {db_dir.name}.")
            continue

        # Extract top-level stats
        num_tables = _safe_get(data, "num_tables")
        num_requests = _safe_get(data, "num_requests")

        # Extract model-specific stats
        model_data = _safe_get(data, "models", model_name)
        
        # If the model didn't run on this database, skip it
        if model_data == "N/A":
            continue

        # Extract Status & Time metrics
        status = model_data.get("status", {})
        time_stats = model_data.get("time", {})
        attempts = model_data.get("attempts", {})
        csr = model_data.get("csr", {})

        row = [
            db_dir.name,
            str(num_tables),
            str(num_requests),
            f"{_safe_get(status, 'correct_pct')}%",
            str(_safe_get(status, 'n_syntax')),
            str(_safe_get(status, 'n_runtime')),
            str(_safe_get(status, 'n_eval_correct')),
            str(_safe_get(time_stats, 'avg')) + "s",
            str(_safe_get(attempts, 'avg')),
            str(_safe_get(csr, 'low')) + "%",
            str(_safe_get(csr, 'medium')) + "%",
            str(_safe_get(csr, 'high')) + "%",
        ]
        rows.append(row)

    if not rows:
        return f"# Model Summary: {model_name}\n\nNo data found for this model across the tested databases."

    # --- Build the Markdown Table ---
    headers = [
        "Database", "Tables", "Requests", "Success %", "Syntax Err", 
        "Runtime Err", "Eval Correct", "Avg Time", "Avg Attempts",
        "CSR Low", "CSR Med", "CSR High"
    ]

    md_lines = [
        f"# Model Performance Summary: `{model_name}`\n",
        f"**Base Directory:** `{base_dir}`\n",
        "## Core Performance Metrics\n",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]

    for row in rows:
        md_lines.append("| " + " | ".join(row) + " |")

    # --- Add Averages Row ---
    if len(rows) > 1:
        avg_row = ["**AVERAGE**", "", ""]
        # Calculate averages for numeric columns (indices 3 to 11)
        for col_idx in range(3, len(headers)):
            col_values = []
            for r in rows:
                val = r[col_idx].replace('%', '').replace('s', '').replace('N/A', '')
                if val:
                    col_values.append(float(val))
            avg_val = sum(col_values) / len(col_values) if col_values else 0
            
            # Re-append formatting based on column
            if col_idx == 3 or col_idx >= 9:
                avg_row.append(f"**{round(avg_val, 2)}%**")
            elif col_idx == 7:
                avg_row.append(f"**{round(avg_val, 2)}s**")
            else:
                avg_row.append(f"**{round(avg_val, 2)}**")
                
        md_lines.append("| " + " | ".join(avg_row) + " |")

    return "\n".join(md_lines)

def main():
    parser = argparse.ArgumentParser(description="Generate a Markdown summary for a specific LLM model from final_stats.json files.")
    parser.add_argument(
        "--model", 
        type=str, 
        required=True, 
        help="The exact name of the model to summarize (must match the key in QUERY_MODELS)."
    )
    parser.add_argument(
        "--base-dir", 
        type=str, 
        default="tests/output/generations", 
        help="Path to the base directory containing database folders."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=f"model_summary.md", 
        help="Name of the output markdown file."
    )

    args = parser.parse_args()

    base_path = Path(args.base_dir)
    if not base_path.exists():
        print(f"Error: The base directory '{base_path}' does not exist.")
        return

    print(f"Generating summary for model '{args.model}'...")
    markdown_content = generate_markdown_report(base_path, args.model)

    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Success! Summary written to '{output_path}'.")

if __name__ == "__main__":
    main()