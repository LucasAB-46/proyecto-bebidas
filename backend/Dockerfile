# --- Fase 1: Definir la base ---
# Usamos una imagen oficial de Python. 'slim' es una versión ligera, ideal para producción.
FROM python:3.11-slim

# --- Fase 2: Configurar el entorno ---
# Establecemos variables de entorno recomendadas para Python en Docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Creamos y establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# --- Fase 3: Instalar dependencias ---
# Copiamos primero el archivo de requerimientos.
# Gracias al sistema de capas de Docker, este paso solo se volverá a ejecutar si requirements.txt cambia.
COPY requirements.txt .

# --- AÑADIDO: Instalar dependencias del sistema operativo ---
# Actualizamos la lista de paquetes e instalamos las herramientas necesarias ANTES de pip.
# build-essential: para compilar librerías como psycopg2.
# libpq-dev: las librerías cliente de PostgreSQL.
# Al final, limpiamos la caché para mantener la imagen pequeña.
RUN apt-get update \
    && apt-get install -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --- AÑADIDO (Buena práctica): Actualizar pip a su última versión ---
RUN pip install --upgrade pip

# Ahora sí, instalamos las dependencias de Python. Esto ya no debería fallar.
RUN pip install --no-cache-dir -r requirements.txt

# --- Fase 4: Copiar el código de la aplicación ---
# Copiamos todo el contenido del proyecto al directorio de trabajo /app
COPY . .

# --- Fase 5: Exponer el puerto ---
# Le decimos a Docker que la aplicación dentro del contenedor escuchará en el puerto 8000
# Nota: Render ignora este puerto y usa el que se especifica en el comando de inicio.
EXPOSE 8000

# --- Fase 6: Comando de ejecución ---
# El comando que se ejecutará cuando el contenedor se inicie.
# Nota: Este comando será sobreescrito por el 'dockerCommand' en tu render.yaml.
CMD ["gunicorn", "--config", "gunicorn.conf.py", "core.wsgi:application"]