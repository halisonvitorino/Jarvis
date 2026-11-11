"""Abertura de conexões SQLite com PRAGMAs padrão do JARVIS."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from jarvis.core.errors import DatabaseError


def open_connection(database_path: Path) -> sqlite3.Connection:
    """Abre uma conexão (WAL, foreign keys, Row factory). O chamador é responsável por fechá-la."""
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
    except (sqlite3.Error, OSError) as exc:
        raise DatabaseError(f"Não foi possível abrir o banco em {database_path}: {exc}") from exc
    return connection


@contextmanager
def connect(database_path: Path) -> Iterator[sqlite3.Connection]:
    """Conexão transacional: commit ao sair, rollback em caso de erro, sempre fecha."""
    connection = open_connection(database_path)
    try:
        yield connection
        connection.commit()
    except sqlite3.Error as exc:
        connection.rollback()
        raise DatabaseError(f"Erro no banco de dados: {exc}") from exc
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
