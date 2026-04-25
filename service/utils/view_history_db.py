import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "view_history.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_view_history_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_view_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            topic_addr INTEGER NOT NULL,
            viewed_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_topic_view(username: str, topic_addr: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO topic_view_history (
            username,
            topic_addr,
            viewed_at
        ) VALUES (?, ?, ?)
    """, (
        username,
        topic_addr,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_recent_viewed_topic_ids(username: str, limit: int = 7) -> list[int]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT topic_addr, MAX(viewed_at) AS last_view
        FROM topic_view_history
        WHERE username = ?
        GROUP BY topic_addr
        ORDER BY last_view DESC
        LIMIT ?
    """, (username, limit))

    rows = cursor.fetchall()
    conn.close()

    return [row["topic_addr"] for row in rows]