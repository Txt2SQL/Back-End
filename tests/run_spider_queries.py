import argparse, sqlite3, sys, os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import DATASET_DATA
from src.classes.datasets import SpiderDataset
from src.classes.logger import LoggerManager


def main():
    LoggerManager.setup_project_logger()
    logger = LoggerManager.get_logger(__name__)

    parser = argparse.ArgumentParser(description="Execute Spider dev queries against SQLite databases")
    parser.add_argument("--db", help="Filter by database name (db_id)")
    parser.add_argument("--limit", type=int, help="Max number of queries to execute")
    parser.add_argument("--index", type=int, help="Run a single query by index in dev.json")
    args = parser.parse_args()

    dataset = SpiderDataset()
    entries = dataset.dev

    if args.db:
        entries = [e for e in entries if e["db_id"] == args.db]
    if args.index is not None:
        entries = [entries[args.index]]
    if args.limit:
        entries = entries[:args.limit]

    total = len(entries)
    passed = 0

    for i, entry in enumerate(entries):
        db_id = entry["db_id"]
        query = entry["query"]
        question = entry["question"]
        db_path = DATASET_DATA / db_id / f"{db_id}.sqlite"

        if not db_path.exists():
            logger.info("[%d/%d] SKIP  %s – database file not found: %s", i + 1, total, db_id, db_path)
            continue

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            conn.close()

            row_count = len(rows)
            passed += 1
            logger.info(
                "[%d/%d] OK  %s  rows=%d  query=%s",
                i + 1, total, db_id, row_count, query,
            )
            logger.info("       question=%s", question)
            if rows:
                logger.info("       headers=%s", [d[0] for d in cursor.description])
                for r in rows[:5]:
                    logger.info("       row=%s", r)
                if len(rows) > 5:
                    logger.info("       ... (%d more rows)", len(rows) - 5)
        except sqlite3.Error as e:
            logger.info("[%d/%d] ERROR %s  %s  query=%s", i + 1, total, db_id, e, query)

    logger.info("=" * 60)
    logger.info("Total: %d  |  Passed: %d  |  Failed: %d", total, passed, total - passed)


if __name__ == "__main__":
    main()
