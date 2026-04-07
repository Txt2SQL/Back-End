from typing import List, Any, Optional

class Records:
    def __init__(self, rows: List[Any], columns: Optional[List[str]] = None):
        self.rows = rows or []
        self.columns = columns or []
        self.count = len(self.rows)

    def get_preview(self, limit: int = 10, max_col_width: int = 40) -> str:
        if not self.rows:
            return "No records found."

        sample = self.rows[:limit]
        
        # logic to handle different row types (Dict vs Tuple/List)
        headers = []
        normalized = []

        # Check if explicit column names are available first.
        if self.columns:
            headers = list(self.columns)
            normalized = [
                list(row) if isinstance(row, tuple) else ([row] if not isinstance(row, list) else row)
                for row in sample
            ]
            num_cols = len(headers)
        # Check if the first row is a Dictionary (common with MySQL dictionary=True)
        elif isinstance(sample[0], dict):
            # Use keys as headers
            headers = list(sample[0].keys())
            # Ensure values correspond to headers order
            normalized = [[row.get(h) for h in headers] for row in sample]
            num_cols = len(headers)
        else:
            # Fallback for Tuples/Lists
            normalized = [
                list(row) if isinstance(row, tuple) else ([row] if not isinstance(row, list) else row)
                for row in sample
            ]
            num_cols = max(len(row) for row in normalized) if normalized else 0
            headers = [f"col_{idx + 1}" for idx in range(num_cols)]

        def fmt(value: Any) -> str:
            value_str = str(value)
            # Remove newlines to keep table structure intact
            value_str = value_str.replace('\n', ' ')
            return value_str if len(value_str) <= max_col_width else value_str[: max_col_width - 3] + "..."

        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in normalized:
            for idx in range(num_cols):
                # Handle cases where row might be shorter than headers (rare in SQL)
                val = row[idx] if idx < len(row) else ""
                cell = fmt(val)
                col_widths[idx] = max(col_widths[idx], len(cell))

        # Build Table parts
        border = "┼".join("─" * (width + 2) for width in col_widths)
        top = "┌" + border.replace("┼", "┬") + "┐"
        mid = "├" + border + "┤"
        bottom = "└" + border.replace("┼", "┴") + "┘"

        def render_row(values: List[Any]) -> str:
            cells: List[str] = []
            for idx in range(num_cols):
                val = values[idx] if idx < len(values) else ""
                value = fmt(val)
                cells.append(f" {value:<{col_widths[idx]}} ")
            return "│" + "│".join(cells) + "│"

        lines = [
            f"✨ Query preview:",
            top,
            render_row(headers),
            mid,
        ]
        for row in normalized:
            lines.append(render_row(row))
        lines.append(bottom)

        return "\n".join(lines)

    def __len__(self):
        return self.count

    def __repr__(self):
        return f"<Records rows={self.count}>"
    
    def __iter__(self):
        return iter(self.rows)
    
    def __getitem__(self, index):
        return self.rows[index]
    
    def to_dict(self) -> List[dict[str, Any]]:
        if not self.rows:
            return []

        first = self.rows[0]
        if isinstance(first, dict):
            return self.rows

        if isinstance(first, tuple):
            num_cols = len(first)
            headers = self.columns or [f"col_{idx + 1}" for idx in range(num_cols)]
            return [dict(zip(headers, row)) for row in self.rows]

        if isinstance(first, list):
            num_cols = len(first)
            headers = self.columns or [f"col_{idx + 1}" for idx in range(num_cols)]
            return [dict(zip(headers, row)) for row in self.rows]

        header = self.columns[0] if self.columns else "col_1"
        return [{header: row} for row in self.rows]
