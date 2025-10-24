FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Si alguna lib compila, estos paquetes ayudan (para psycopg2-binary no son estrictos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY backend/ .

COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]

# CLAVE: bindear al puerto dinámico de Railway

CMD ["gunicorn", "-c", "gunicorn.conf.py", "core.wsgi:application"]

