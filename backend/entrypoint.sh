#!/bin/sh

# Salir inmediatamente si un comando falla
set -e

echo "--- Ejecutando migraciones de la base de datos... ---"
python manage.py migrate

echo "--- Migraciones completadas. Iniciando servidor... ---"

# Ejecuta el comando principal que se le pase al script (será gunicorn)
exec "$@"