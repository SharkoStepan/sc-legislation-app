import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "recommendation_feedback.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# создание табл
def init_feedback_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendation_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            source_topic_addr INTEGER NOT NULL,
            recommended_topic_addr INTEGER NOT NULL,
            useful TEXT NOT NULL CHECK (useful IN ('yes', 'no')),
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_feedback(username: str, source_topic_addr: int, recommended_topic_addr: int, useful: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO recommendation_feedback (
            username,
            source_topic_addr,
            recommended_topic_addr,
            useful,
            created_at
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        username,
        source_topic_addr,
        recommended_topic_addr,
        useful,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def get_feedback_stats(source_topic_addr: int, recommended_topic_addr: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN useful = 'yes' THEN 1 ELSE 0 END), 0) AS yes_count,
            COALESCE(SUM(CASE WHEN useful = 'no' THEN 1 ELSE 0 END), 0) AS no_count,
            COUNT(*) AS total_count
        FROM recommendation_feedback
        WHERE source_topic_addr = ?
          AND recommended_topic_addr = ?
    """, (source_topic_addr, recommended_topic_addr))

    row = cursor.fetchone()
    conn.close()

    return {
        "yes_count": row["yes_count"] if row else 0,
        "no_count": row["no_count"] if row else 0,
        "total_count": row["total_count"] if row else 0,
    }