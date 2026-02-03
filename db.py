import sqlite3
from pathlib import Path
from config import DB_PATH


def _get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title, link)
        )
    """)
    conn.commit()
    conn.close()


def get_last_offers(limit=10):
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, link, source, created_at
        FROM offers
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def save_offers(offers):
    """
    Сохраняет список предложений в БД.
    Ожидает список словарей с ключами title, link, source.
    Возвращает количество реально добавленных (новых) записей.
    """
    if not offers:
        return 0

    conn = _get_connection()
    cur = conn.cursor()
    inserted = 0
    try:
        for offer in offers:
            cur.execute(
                """
                INSERT OR IGNORE INTO offers (title, link, source)
                VALUES (?, ?, ?)
                """,
                (
                    offer["title"],
                    offer["link"],
                    offer.get("source", "Tez"),
                ),
            )
            if cur.rowcount > 0:
                inserted += 1
        conn.commit()
    finally:
        conn.close()
    return inserted


def get_offers_count():
    """
    Общее количество записей в таблице offers.
    """
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM offers")
    (count,) = cur.fetchone()
    conn.close()
    return count


def get_sources_stats():
    """
    Статистика по источникам:
    возвращает словарь {source: count}.
    """
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(source, 'unknown') AS src, COUNT(*)
        FROM offers
        GROUP BY src
    """)
    rows = cur.fetchall()
    conn.close()
    return {src: cnt for src, cnt in rows}
