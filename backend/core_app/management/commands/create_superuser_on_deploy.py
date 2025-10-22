# backend/core_app/management/commands/create_superuser_on_deploy.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Crea un superusuario a partir de variables de entorno si no existe.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not username or not password:
            self.stdout.write(self.style.WARNING('No se encontraron las variables de entorno para el superusuario. Omitiendo.'))
            return

        if not User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f"Creando superusuario inicial: {username}"))
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS("Superusuario creado exitosamente."))
        else:
            self.stdout.write(self.style.WARNING(f"El superusuario '{username}' ya existe."))