
import os
import uvicorn
from migrate import run_migration


def main():
    # 1) Migrazioni
    run_migration()

    # 2) Avvio server API
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Se usi reload in dev, mettilo via env (vedi sotto)
    reload = os.getenv("RELOAD", "0") == "1"

    uvicorn.run("api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
