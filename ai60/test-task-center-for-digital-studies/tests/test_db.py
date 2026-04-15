import sqlite3
from pathlib import Path

import pytest

from src import db
from src.models import Article


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.db")


class TestConnect:
    def test_yields_sqlite_connection(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            assert isinstance(conn, sqlite3.Connection)

    def test_commits_on_clean_exit(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            conn.execute(
                "INSERT INTO articles (title, url) VALUES (?, ?);",
                ("Persist me", "https://example.com/persist"),
            )

        with db.connect(db_path) as conn:
            rows = conn.execute("SELECT title, url FROM articles;").fetchall()
        assert rows == [("Persist me", "https://example.com/persist")]

    def test_rolls_back_on_exception(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            db.init_schema(conn)

        with pytest.raises(RuntimeError, match="boom"):
            with db.connect(db_path) as conn:
                conn.execute(
                    "INSERT INTO articles (title, url) VALUES (?, ?);",
                    ("Doomed", "https://example.com/doomed"),
                )
                raise RuntimeError("boom")

        with db.connect(db_path) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM articles;").fetchone()
        assert rows[0] == 0

    def test_closes_connection_on_clean_exit(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            pass
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1;")

    def test_closes_connection_on_exception(self, db_path: str) -> None:
        leaked: sqlite3.Connection | None = None
        with pytest.raises(RuntimeError):
            with db.connect(db_path) as conn:
                leaked = conn
                raise RuntimeError("boom")
        assert leaked is not None
        with pytest.raises(sqlite3.ProgrammingError):
            leaked.execute("SELECT 1;")


class TestInitSchema:
    def test_creates_articles_table(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='articles';"
            ).fetchone()
        assert row == ("articles",)

    def test_creates_url_index(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_articles_url';"
            ).fetchone()
        assert row == ("idx_articles_url",)

    def test_enforces_unique_url_at_schema_level(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            conn.execute(
                "INSERT INTO articles (title, url) VALUES (?, ?);",
                ("First", "https://example.com/same"),
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO articles (title, url) VALUES (?, ?);",
                    ("Second", "https://example.com/same"),
                )

    def test_is_idempotent(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            db.init_schema(conn)
            conn.execute(
                "INSERT INTO articles (title, url) VALUES (?, ?);",
                ("Hello", "https://example.com/"),
            )

    def test_created_at_defaults_to_now(self, db_path: str) -> None:
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            conn.execute(
                "INSERT INTO articles (title, url) VALUES (?, ?);",
                ("Timed", "https://example.com/timed"),
            )
            row = conn.execute(
                "SELECT created_at FROM articles WHERE url = ?;",
                ("https://example.com/timed",),
            ).fetchone()
        assert row[0] is not None
        assert len(row[0]) > 0


class TestSaveArticle:
    def test_returns_true_on_first_insert(self, db_path: str) -> None:
        article = Article(title="New", url="https://example.com/new")
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            assert db.save_article(conn, article) is True

    def test_returns_false_on_duplicate_url(self, db_path: str) -> None:
        article = Article(title="New", url="https://example.com/new")
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            db.save_article(conn, article)
            assert db.save_article(conn, article) is False

    def test_duplicate_does_not_overwrite_existing_row(self, db_path: str) -> None:
        original = Article(title="Original", url="https://example.com/same")
        replacement = Article(title="Replacement", url="https://example.com/same")
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            db.save_article(conn, original)
            db.save_article(conn, replacement)
            row = conn.execute(
                "SELECT title FROM articles WHERE url = ?;",
                ("https://example.com/same",),
            ).fetchone()
        assert row == ("Original",)

    def test_persists_title_and_url(self, db_path: str) -> None:
        article = Article(title="Persisted", url="https://example.com/persisted")
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            db.save_article(conn, article)
            row = conn.execute(
                "SELECT title, url FROM articles WHERE url = ?;",
                (article.url,),
            ).fetchone()
        assert row == (article.title, article.url)

    def test_resists_sql_injection_via_parameterized_queries(self, db_path: str) -> None:
        malicious = Article(
            title="Bobby Tables",
            url="https://example.com/'); DROP TABLE articles;--",
        )
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            assert db.save_article(conn, malicious) is True
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='articles';"
            ).fetchone()
            assert row == (1,)
            stored = conn.execute(
                "SELECT url FROM articles WHERE title = ?;",
                ("Bobby Tables",),
            ).fetchone()
            assert stored == (malicious.url,)

    def test_preserves_insertion_order_via_autoincrement_id(self, db_path: str) -> None:
        first = Article(title="First", url="https://example.com/1")
        second = Article(title="Second", url="https://example.com/2")
        with db.connect(db_path) as conn:
            db.init_schema(conn)
            db.save_article(conn, first)
            db.save_article(conn, second)
            rows = conn.execute("SELECT title FROM articles ORDER BY id;").fetchall()
        assert rows == [("First",), ("Second",)]
