#!/bin/sh

# Salir inmediatamente si un comando falla
set -e

echo "----------------------------------------------------"
echo "--- INICIANDO SCRIPT DE DIAGNÓSTICO FINAL ---"
echo "----------------------------------------------------"
echo ""

echo "--- PASO 1: Verificando contenido de requirements.txt DENTRO del contenedor ---"
cat /app/requirements.txt
echo "--- FIN DE requirements.txt ---"
echo ""

echo "--- PASO 2: Verificando paquetes instalados con pip freeze ---"
pip freeze
echo "--- FIN DE pip freeze ---"
echo ""

echo "--- PASO 3: Intentando ejecutar las migraciones... ---"
python manage.py migrate

echo "--- Migraciones completadas. Iniciando servidor... ---"

# Ejecuta el comando principal (gunicorn)
exec "$@"