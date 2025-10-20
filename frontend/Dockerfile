# --- Fase 1: Construcción (Build) ---
# Usamos una imagen oficial de Node.js. 'alpine' es una versión muy ligera.
# Le ponemos un alias 'build' a esta fase.
FROM node:18-alpine AS build

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos de definición de dependencias
COPY package.json package-lock.json ./

# Instalamos las dependencias del proyecto
RUN npm install

# Copiamos todo el código fuente de la aplicación
COPY . .

# Ejecutamos el comando de construcción de Vite.
# Esto compilará nuestro React a archivos estáticos (HTML, CSS, JS) en la carpeta /app/dist
RUN npm run build

# --- Fase 2: Producción (Serve) ---
# Empezamos de nuevo desde una imagen base muy ligera, un servidor web llamado Nginx.
FROM nginx:1.25-alpine

# Copiamos los archivos estáticos construidos en la fase anterior (desde /app/dist)
# a la carpeta que Nginx usa para servir contenido web.
COPY --from=build /app/dist /usr/share/nginx/html

# Exponemos el puerto 80, que es el puerto por defecto de Nginx
EXPOSE 80

# El comando para iniciar Nginx (ya viene preconfigurado en la imagen)
CMD ["nginx", "-g", "daemon off;"]