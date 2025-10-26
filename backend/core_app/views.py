from rest_framework import viewsets, permissions
from .models import Local
from .serializers import LocalSerializer


class LocalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/core/locales/ -> lista todos los locales activos
    GET /api/core/locales/{id}/ -> detalle
    Esto se usa en el selector de sucursal del frontend.
    """
    serializer_class = LocalSerializer
    permission_classes = [permissions.AllowAny]  # público para que el login pueda armar el combo
    pagination_class = None  # sin paginar porque son pocos locales

    def get_queryset(self):
        # mostrame sólo locales activos ordenados por nombre
        # Ajustá el campo 'activo' si tu modelo lo llama distinto.
        return Local.objects.filter(activo=True).order_by('nombre')
