from pathlib import Path

import pytest

from jarvis.core.errors import DatabaseError
from jarvis.database.connection import connect, open_connection
from jarvis.database.events import recent_events, record_event
from jarvis.database.migrator import discover_migrations, run_migrations


def _tables(database_path: Path) -> set[str]:
    with connect(database_path) as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        return {row["name"] for row in rows}


def test_connection_pragmas(tmp_path: Path) -> None:
    connection = open_connection(tmp_path / "nested" / "jarvis.db")
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    finally:
        connection.close()


def test_connect_rolls_back_on_error(tmp_path: Path) -> None:
    database_path = tmp_path / "jarvis.db"
    with connect(database_path) as connection:
        connection.execute("CREATE TABLE items (value TEXT)")

    with pytest.raises(RuntimeError):
        with connect(database_path) as connection:
            connection.execute("INSERT INTO items VALUES ('x')")
            raise RuntimeError("abortar")

    with connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0


def test_connect_wraps_sqlite_errors(tmp_path: Path) -> None:
    with pytest.raises(DatabaseError):
        with connect(tmp_path / "jarvis.db") as connection:
            connection.execute("SELECT * FROM tabela_inexistente")


def test_run_migrations_creates_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "jarvis.db"

    applied = run_migrations(database_path)

    assert applied == [migration.version for migration in discover_migrations()]
    assert {"schema_migrations", "system_events"} <= _tables(database_path)


def test_run_migrations_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "jarvis.db"

    run_migrations(database_path)
    assert run_migrations(database_path) == []


def test_failed_migration_is_rolled_back(tmp_path: Path) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "0001_ok.sql").write_text("CREATE TABLE a (id INTEGER);", encoding="utf-8")
    (migrations_dir / "0002_broken.sql").write_text(
        "CREATE TABLE b (id INTEGER);\nTHIS IS NOT SQL;", encoding="utf-8"
    )
    database_path = tmp_path / "jarvis.db"

    with pytest.raises(DatabaseError):
        run_migrations(database_path, migrations_dir)

    tables = _tables(database_path)
    assert "a" in tables
    assert "b" not in tables
    with connect(database_path) as connection:
        versions = [row[0] for row in connection.execute("SELECT version FROM schema_migrations")]
    assert versions == [1]


def test_invalid_migration_name_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "initial.sql").write_text("SELECT 1;", encoding="utf-8")

    with pytest.raises(DatabaseError):
        discover_migrations(tmp_path)


def test_record_and_read_events(tmp_path: Path) -> None:
    database_path = tmp_path / "jarvis.db"
    run_migrations(database_path)

    with connect(database_path) as connection:
        record_event(connection, "INFO", "test", "primeiro")
        record_event(connection, "INFO", "test", "segundo")

    with connect(database_path) as connection:
        events = recent_events(connection)

    assert [event["message"] for event in events] == ["segundo", "primeiro"]
