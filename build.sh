#!/usr/bin/env bash
# Salir inmediatamente si un comando falla
set -o errexit

# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Recolectar archivos estáticos (importante para el admin de Django)
python manage.py collectstatic --no-input

# 3. Aplicar las migraciones de la base de datos
python manage.py migrate