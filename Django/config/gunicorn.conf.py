import os
import environ
from pathlib import Path
from core.settings import BASE_DIR

env = environ.Env()
env.read_env( BASE_DIR / ".env")


if not Path(BASE_DIR / "logs").exists():
    Path(BASE_DIR / "logs").mkdir()


bind = os.environ.get("GUNICORN_BIND")
workers = os.environ.get("GUNICORN_WORKERS")
threads = os.environ.get("GUNICORN_THREADS")
accesslog =env.str("GUNICORN_ACCESS_LOGS", "logs/gunicorn.access.log")
errorlog =env.str("GUNICORN_ERROR_LOGS", "logs/gunicorn.error.log") 