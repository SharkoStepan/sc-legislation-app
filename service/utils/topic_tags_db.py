import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "topic_tags.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
    """, (table_name,))
    return cursor.fetchone() is not None


def _has_new_schema(cursor) -> bool:
    if not _table_exists(cursor, "topic_tags"):
        return False

    cursor.execute("PRAGMA table_info(topic_tags)")
    columns = {row["name"] for row in cursor.fetchall()}

    return {
        "topic_addr",
        "tag_key",
        "tag_label",
        "confidence",
        "matched_terms",
        "is_primary",
        "created_at",
        "updated_at"
    }.issubset(columns)


def init_topic_tags_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Если раньше была старая таблица с одним тегом на тему,
    # пересоздаём её под несколько тегов. Это безопасно: теги вычисляются автоматически.
    if _table_exists(cursor, "topic_tags") and not _has_new_schema(cursor):
        cursor.execute("DROP TABLE topic_tags")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_tags (
            topic_addr INTEGER NOT NULL,
            tag_key TEXT NOT NULL,
            tag_label TEXT NOT NULL,
            confidence REAL NOT NULL,
            matched_terms TEXT,
            is_primary INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (topic_addr, tag_key)
        )
    """)

    conn.commit()
    conn.close()


def get_topic_tags(topic_addr: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            topic_addr,
            tag_key,
            tag_label,
            confidence,
            matched_terms,
            is_primary
        FROM topic_tags
        WHERE topic_addr = ?
        ORDER BY is_primary DESC, confidence DESC, tag_label ASC
    """, (topic_addr,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "topic_addr": row["topic_addr"],
            "key": row["tag_key"],
            "label": row["tag_label"],
            "confidence": row["confidence"],
            "matched_terms": row["matched_terms"] or "",
            "is_primary": bool(row["is_primary"]),
        }
        for row in rows
    ]


def save_topic_tags(topic_addr: int, tags: list[dict]):
    now = datetime.utcnow().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    # Перезаписываем теги темы целиком, потому что классификатор
    # каждый раз возвращает актуальный набор тегов.
    cursor.execute("""
        DELETE FROM topic_tags
        WHERE topic_addr = ?
    """, (topic_addr,))

    for index, tag in enumerate(tags):
        matched_terms = tag.get("matched_terms", [])
        if isinstance(matched_terms, list):
            matched_terms = ", ".join(matched_terms)

        cursor.execute("""
            INSERT INTO topic_tags (
                topic_addr,
                tag_key,
                tag_label,
                confidence,
                matched_terms,
                is_primary,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            topic_addr,
            tag["key"],
            tag["label"],
            float(tag.get("confidence", 0.0)),
            matched_terms,
            1 if index == 0 else 0,
            now,
            now
        ))

    conn.commit()
    conn.close()