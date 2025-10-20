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

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# --- Fase 4: Copiar el código de la aplicación ---
# Copiamos todo el contenido del proyecto al directorio de trabajo /app
COPY . .

# --- Fase 5: Exponer el puerto ---
# Le decimos a Docker que la aplicación dentro del contenedor escuchará en el puerto 8000
EXPOSE 8000

# --- Fase 6: Comando de ejecución ---
# El comando que se ejecutará cuando el contenedor se inicie.
# Usamos 0.0.0.0 para que el servidor sea accesible desde fuera del contenedor.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]