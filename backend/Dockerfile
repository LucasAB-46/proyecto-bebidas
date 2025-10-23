# Usamos una versión de Python para invalidar cualquier caché residual
FROM python:3.11.9-slim-bookworm

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# --- PRUEBA NUCLEAR: Instalar paquetes críticos DIRECTAMENTE ---
# Esto bypassa por completo el requirements.txt para forzar la instalación.
RUN pip install Django djangorestframework gunicorn dj-database-url psycopg2-binary whitenoise

# Copiar el resto de los requerimientos (aunque los más importantes ya están instalados)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Copiar y dar permisos al script de entrada
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Punto de entrada
ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:10000"]