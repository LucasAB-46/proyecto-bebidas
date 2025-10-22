from django.apps import AppConfig
import os # Importa el módulo os

class CoreAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_app' # Este es el nombre de tu app, está correcto.

    def ready(self):
        # Solo ejecuta este código si estamos en un entorno de producción
        # La variable 'RENDER' es provista por la plataforma Render.
        if os.environ.get('RENDER'):
            from django.contrib.auth import get_user_model

            User = get_user_model()
            
            
            username = "admin"  
            email = "lucasbejarano@hotmail.com" 
            password = "tu_contraseña_muy_segura" 
            # ---------------------------------

            if not User.objects.filter(username=username).exists():
                print(f"Creando superusuario inicial: {username}")
                User.objects.create_superuser(username, email, password)
                print("Superusuario creado exitosamente.")
            else:
                print(f"El superusuario '{username}' ya existe.")