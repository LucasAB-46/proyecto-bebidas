# backend/core_app/apps.py (versión SEGURA y automática)

from django.apps import AppConfig
import os

class CoreAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_app'

    def ready(self):
        # Solo se ejecuta si las variables de entorno del superusuario existen
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        # Comprobamos que las variables necesarias existan
        if username and password:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Solo crea el usuario si no existe
            if not User.objects.filter(username=username).exists():
                print(f"Creando superusuario inicial desde variables de entorno: {username}")
                email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '') # El email es opcional
                User.objects.create_superuser(username=username, email=email, password=password)
                print("Superusuario creado exitosamente.")
            else:
                print(f"El superusuario '{username}' ya existe, no se toma ninguna acción.")