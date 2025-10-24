#!/usr/bin/env bash
set -e

echo "--- Chequeando variables ---"
: "${DJANGO_SECRET_KEY:?Falta DJANGO_SECRET_KEY}"
# DATABASE_URL es opcional en dev/local (SQLite). En Railway suele existir.

echo "--- Ejecutando migraciones ---"
python manage.py migrate --noinput
python manage.py createsuperuser --noinput || true

echo "--- Recolectando estáticos ---"
python manage.py collectstatic --noinput || true

echo "--- Iniciando servidor ---"
exec "$@"
