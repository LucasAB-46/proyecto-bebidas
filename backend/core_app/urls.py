# core_app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocalViewSet

# Creamos un router
router = DefaultRouter()

# Registramos nuestro ViewSet de Locales en el router
# Esto creará automáticamente las rutas para /locales/ y /locales/{id}/
router.register(r'locales', LocalViewSet, basename='local')

# Las URLs de la API son generadas automáticamente por el router
urlpatterns = [
    path('', include(router.urls)),
]