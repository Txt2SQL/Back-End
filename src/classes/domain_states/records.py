from typing import List, Any

class Records:
    def __init__(self, rows: List[Any]):
        self.rows = rows or []
        self.count = len(self.rows)

    def get_preview(self, limit: int = 10, max_col_width: int = 40) -> str:
        sample = self.rows[:limit]
        normalized = [
            list(row) if isinstance(row, tuple) else ([row] if not isinstance(row, list) else row)
            for row in sample
        ]
        num_cols = max(len(row) for row in normalized) if normalized else 0

        headers = [f"col_{idx + 1}" for idx in range(num_cols)]

        def fmt(value: Any) -> str:
            value_str = str(value)
            return value_str if len(value_str) <= max_col_width else value_str[: max_col_width - 3] + "..."

        col_widths = [len(header) for header in headers]
        for row in normalized:
            for idx in range(num_cols):
                cell = fmt(row[idx] if idx < len(row) else "")
                col_widths[idx] = max(col_widths[idx], len(cell))

        border = "┼".join("─" * (width + 2) for width in col_widths)
        top = "┌" + border.replace("┼", "┬") + "┐"
        mid = "├" + border + "┤"
        bottom = "└" + border.replace("┼", "┴") + "┘"

        def render_row(values: List[Any]) -> str:
            cells: List[str] = []
            for idx in range(num_cols):
                value = fmt(values[idx] if idx < len(values) else "")
                cells.append(f" {value:<{col_widths[idx]}} ")
            return "│" + "│".join(cells) + "│"

        lines = [
            f"\n✨ Query preview ({self.count} row(s) fetched, showing up to {limit}):",
            top,
            render_row(headers),
            mid,
        ]
        for row in normalized:
            lines.append(render_row(row))
        lines.append(bottom)

        if self.count > limit:
            lines.append(f"… and {self.count - limit} more row(s).")

        return "\n".join(lines)

    def __len__(self):
        return self.count

    def __repr__(self):
        return f"<Records rows={self.count}>"
    
    def __iter__(self):
        return iter(self.rows)
    
    def __getitem__(self, index):
        return self.rows[index]