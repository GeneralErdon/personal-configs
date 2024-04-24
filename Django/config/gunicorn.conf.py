import os
import environ
from core.settings import BASE_DIR

env = environ.Env()
env.read_env( BASE_DIR / ".env")


bind = os.environ.get("GUNICORN_BIND")
workers = os.environ.get("GUNICORN_WORKERS")
threads = os.environ.get("GUNICORN_THREADS")
accesslog = os.environ.get("GUNICORN_ACCESS_LOGS")
errorlog = os.environ.get("GUNICORN_ERROR_LOGS")