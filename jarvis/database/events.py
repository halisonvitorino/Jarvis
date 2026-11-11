"""Registro de eventos do sistema (boot, desligamento, falhas) na tabela system_events."""

import sqlite3


def record_event(connection: sqlite3.Connection, level: str, source: str, message: str) -> int:
    cursor = connection.execute(
        "INSERT INTO system_events (level, source, message) VALUES (?, ?, ?)",
        (level, source, message),
    )
    return cursor.lastrowid or 0


def recent_events(connection: sqlite3.Connection, limit: int = 50) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT id, created_at, level, source, message FROM system_events "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
