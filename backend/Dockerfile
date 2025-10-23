# --- CAMBIO CLAVE: Usamos una versión ligeramente diferente para invalidar la caché de Render ---
FROM python:3.11.9-slim-bookworm

# Variables de entorno recomendadas
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema para compilar psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requerimientos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Copia el script de entrypoint al contenedor y dale permisos de ejecución
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Dile a Docker que este script es el punto de entrada
ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto que ejecutará el entrypoint
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:10000"]