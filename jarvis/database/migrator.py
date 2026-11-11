"""Executor de migrações SQL versionadas (arquivos NNNN_nome.sql)."""

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from jarvis.core.errors import DatabaseError
from jarvis.core.logger import get_logger
from jarvis.database.connection import open_connection

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_MIGRATION_FILE_PATTERN = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")

_logger = get_logger("database.migrator")

_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    applied_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
)
"""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    path: Path


def discover_migrations(migrations_dir: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Lista migrações ordenadas por versão. Arquivos fora do padrão ou versões duplicadas são erro."""
    migrations: dict[int, Migration] = {}
    for path in sorted(migrations_dir.glob("*.sql")):
        match = _MIGRATION_FILE_PATTERN.match(path.name)
        if match is None:
            raise DatabaseError(f"Nome de migração inválido: {path.name} (esperado NNNN_nome.sql)")
        version = int(match.group(1))
        if version in migrations:
            raise DatabaseError(f"Versão de migração duplicada: {version}")
        migrations[version] = Migration(version, match.group(2), path)
    return [migrations[version] for version in sorted(migrations)]


def applied_versions(connection: sqlite3.Connection) -> set[int]:
    connection.execute(_CREATE_MIGRATIONS_TABLE)
    connection.commit()
    return {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}


def _apply(connection: sqlite3.Connection, migration: Migration) -> None:
    sql = migration.path.read_text(encoding="utf-8")
    # executescript faz commit implícito, então a transação é delimitada dentro do próprio script.
    # version e name vêm do regex do nome do arquivo ([0-9] e [a-z0-9_]), seguros para interpolar.
    script = (
        "BEGIN;\n"
        f"{sql}\n;\n"
        "INSERT INTO schema_migrations (version, name) "
        f"VALUES ({migration.version}, '{migration.name}');\n"
        "COMMIT;"
    )
    try:
        connection.executescript(script)
    except sqlite3.Error as exc:
        if connection.in_transaction:
            connection.rollback()
        raise DatabaseError(
            f"Falha ao aplicar migração {migration.version:04d}_{migration.name}: {exc}"
        ) from exc


def run_migrations(database_path: Path, migrations_dir: Path = MIGRATIONS_DIR) -> list[int]:
    """Aplica migrações pendentes e retorna as versões aplicadas nesta execução."""
    migrations = discover_migrations(migrations_dir)
    connection = open_connection(database_path)
    try:
        done = applied_versions(connection)
        pending = [migration for migration in migrations if migration.version not in done]
        for migration in pending:
            _logger.info("Aplicando migração %04d_%s", migration.version, migration.name)
            _apply(connection, migration)
    except sqlite3.Error as exc:
        raise DatabaseError(f"Erro ao executar migrações: {exc}") from exc
    finally:
        connection.close()

    if not pending:
        _logger.debug("Banco de dados já está atualizado")
    return [migration.version for migration in pending]
