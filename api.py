import logging
from fastapi import FastAPI
from db_connection import get_db_connection
from migrate import run_migrations


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

run_migrations()

app = FastAPI()

@app.get("/api/access_secrets")
def access_secrets(apiKey: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT api_key FROM api_keys WHERE api_key = %s LIMIT 1;", [apiKey])
            result = cur.fetchone()
    access = result is not None

    return {"success": True, "access": access}
