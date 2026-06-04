import logging
from pathlib import Path
import psycopg
from db_connection import get_db_connection


logger = logging.getLogger(__name__)

LOCK_KEY = 987654321
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

MIG_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def run_migrations() -> None:
    files = _list_migration_files()

    if not files:
        logger.info("No migrations found, skipping.")
        return

    with get_db_connection() as conn:
        _acquire_lock(conn)

        try:
            _ensure_migrations_table(conn)
            applied_versions = _get_applied_versions(conn)

            for path in files:
                version = path.name

                if version in applied_versions:
                    logger.debug("Migration already applied, skipping: %s", version)
                    continue

                sql = path.read_text(encoding="utf-8")

                logger.info("Applying migration: %s", version)
                _apply_migration(conn, version, sql)

                conn.commit()

                logger.info("Migration applied: %s", version)

            logger.info("Migrations complete.")

        except Exception:
            logger.exception("Migration failed.")
            conn.rollback()
            raise

        finally:
            _release_lock(conn)


def _list_migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        logger.warning("Migrations directory does not exist: %s", MIGRATIONS_DIR)
        return []

    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def _acquire_lock(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_lock(%s);", (LOCK_KEY,))


def _release_lock(conn: psycopg.Connection) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s);", (LOCK_KEY,))
        conn.commit()
    except Exception:
        logger.exception("Failed to release migration lock.")
        conn.rollback()
        raise


def _ensure_migrations_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(MIG_TABLE_SQL)


def _get_applied_versions(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations;")
        return {row[0] for row in cur.fetchall()}


def _apply_migration(conn: psycopg.Connection, version: str, sql: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute("INSERT INTO schema_migrations(version) VALUES (%s);", (version,))
