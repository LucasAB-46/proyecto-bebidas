# core_app/views.py

from rest_framework import viewsets, permissions
from .models import Local
from .serializers import LocalSerializer

class LocalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Un ViewSet simple para ver los locales disponibles.
    No requiere filtrado por local, ya que queremos que el usuario vea todos.
    """
    queryset = Local.objects.filter(activo=True).order_by('nombre')
    serializer_class = LocalSerializer
    
    # Se cambia el permiso a AllowAny para que cualquier usuario (incluso anónimo)
    # pueda ver la lista de locales. Esto es necesario para que el frontend
    # pueda poblar el selector de sucursales antes de que el usuario inicie sesión
    # o seleccione un local.
    permission_classes = [permissions.AllowAny]
    
    # Desactivamos la paginación para este endpoint, ya que la lista de locales
    # será corta y queremos obtenerla completa en una sola petición.
    pagination_class = None