# backend/gunicorn.conf.py
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "3"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
