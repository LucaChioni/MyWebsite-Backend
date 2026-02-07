import os
import time
import psycopg
from pathlib import Path


LOCK_KEY = 987654321
MIGRATIONS_DIR = Path(__file__).parent / "migrations"
MIG_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def wait_for_db(conninfo: str, attempts: int = 60, delay_s: float = 1.0) -> None:
    last_err = None
    for _ in range(attempts):
        try:
            with psycopg.connect(conninfo) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
            return
        except Exception as e:
            last_err = e
            time.sleep(delay_s)
    raise RuntimeError(f"DB not ready after {attempts} attempts: {last_err}")


def get_conninfo_from_env() -> str:
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    pw = os.getenv("DB_PASSWORD")
    return f"postgresql://{user}:{pw}@{host}:{port}/{name}"


def list_migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return files


def ensure_migrations_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(MIG_TABLE_SQL)


def get_applied_versions(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations;")
        return {row[0] for row in cur.fetchall()}


def apply_migration(conn: psycopg.Connection, version: str, sql: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute("INSERT INTO schema_migrations(version) VALUES (%s);", (version,))


def run_migration() -> None:
    conninfo = get_conninfo_from_env()

    print("Waiting for DB...")
    wait_for_db(conninfo)

    files = list_migration_files()
    if not files:
        print("No migrations found; skipping.")
        return

    with psycopg.connect(conninfo) as conn:
        # lock per evitare che due istanze applichino migrazioni insieme
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(%s);", (LOCK_KEY,))

        try:
            ensure_migrations_table(conn)
            applied = get_applied_versions(conn)

            for path in files:
                version = path.name
                if version in applied:
                    continue

                sql = path.read_text(encoding="utf-8")
                print(f"Applying migration: {version}")
                apply_migration(conn, version, sql)
                conn.commit()

            print("Migrations complete.")
        finally:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s);", (LOCK_KEY,))
            conn.commit()


if __name__ == "__main__":
    run_migration()
