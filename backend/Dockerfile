# Usamos una versión de Python para invalidar cualquier caché residual
FROM python:3.11.9-slim-bookworm

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# --- CORRECCIÓN DE RUTA ---
# Copiamos el archivo de requerimientos desde el contexto actual
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CORRECCIÓN DE RUTA ---
# Copiamos todo el código desde el contexto actual
COPY . .

# --- CORRECCIÓN DE RUTA ---
# Copiamos el script de entrada desde el contexto actual
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Punto de entrada
ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:10000"]