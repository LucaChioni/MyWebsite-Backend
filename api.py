import os
from fastapi import FastAPI
import psycopg
from migrate import run_migration

app = FastAPI()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

run_migration()

def get_conn():
    return psycopg.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

@app.get("/api/access_secrets")
def access_secrets(apiKey: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT api_key FROM api_keys WHERE api_key = %s LIMIT 1;", [apiKey])
            result = cur.fetchone()
    access = result is not None

    return {"success": True, "access": access}
