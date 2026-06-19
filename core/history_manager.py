import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "history.db")


class HistoryManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT NOT NULL,
                        date TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        output_path TEXT,
                        input_path TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"DB init error: {e}")

    def add_record(self, file_name, operation, output_path="", input_path=""):
        try:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO history (file_name, date, operation, output_path, input_path) VALUES (?, ?, ?, ?, ?)",
                    (file_name, date, operation, output_path, input_path)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"History insert error: {e}")

    def get_all(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.execute(
                    "SELECT id, file_name, date, operation, output_path FROM history ORDER BY id DESC LIMIT 100"
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"History fetch error: {e}")
            return []

    def clear_history(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("DELETE FROM history")
                conn.commit()
        except Exception as e:
            logger.error(f"History clear error: {e}")
