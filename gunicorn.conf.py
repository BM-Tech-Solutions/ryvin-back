import os

import dotenv

dotenv.load_dotenv()

wsgi_app = "app.main:app"
bind = "0.0.0.0:8000"
reload = os.environ.get("GUNICORN_RELOAD", "false").lower() == "true"

# workers
worker_class = "uvicorn.workers.UvicornWorker"
workers = int((os.environ.get("GUNICORN_WORKERS", 2)))
threads = int((os.environ.get("GUNICORN_THREADS", 10)))

# Optional: Name the process for easy identification in 'ps'
proc_name = "fastapi-prod"

# --- Timeouts and Reliability ---
timeout = 60
keepalive = 2

# Max requests: Auto-restart workers after this many requests to prevent
# memory leaks (important for long-running processes)
max_requests = 1000
max_requests_jitter = 50

# --- Logging ---
# Log to stdout/stderr, which Docker/systemd/supervisor will capture
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")
capture_output = True
enable_stdio_inheritance = True
