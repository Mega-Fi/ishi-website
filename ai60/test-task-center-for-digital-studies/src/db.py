import logging
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .models import Article

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    url        TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

INDEX = "CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);"

INSERT_ARTICLE = "INSERT OR IGNORE INTO articles (title, url) VALUES (?, ?);"


@contextmanager
def connect(db_path: str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(SCHEMA)
    conn.execute(INDEX)


def save_article(conn: sqlite3.Connection, article: Article) -> bool:
    cursor = conn.execute(INSERT_ARTICLE, (article.title, article.url))
    return cursor.rowcount == 1
