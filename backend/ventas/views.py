# ventas/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Venta
from .serializers import VentaReadSerializer, VentaWriteSerializer
from .services import confirmar_venta, anular_venta
# --- 1. IMPORTAMOS LOS NUEVOS PERMISOS ---
from core_app.permissions import IsAdminUser, IsCajeroUser

# Este Mixin no necesita cambios
class LocalScopedMixin:
    local_header = "X-Local-ID"

    def _local_id(self):
        h = self.request.headers.get(self.local_header)
        if not h:
            raise ValidationError({self.local_header: "Header requerido"})
        try:
            return int(h)
        except ValueError:
            raise ValidationError({self.local_header: "Debe ser entero"})

    def get_queryset(self):
        # Asumimos que el modelo Venta tiene un campo 'local_id'
        return Venta.objects.filter(local_id=self._local_id()).order_by("-id")

class VentaViewSet(LocalScopedMixin, viewsets.ModelViewSet):
    # --- 2. APLICAMOS PERMISO ---
    # Se permite el acceso si el usuario es Admin O si es Cajero.
    # El operador '|' (OR) combina los permisos.
    permission_classes = [IsAdminUser | IsCajeroUser]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["id", "cliente__nombre", "estado"]
    ordering_fields = ["id", "fecha", "total"]

    def get_serializer_class(self):
        return VentaWriteSerializer if self.action in ("create","update","partial_update") else VentaReadSerializer

    def perform_create(self, serializer):
        serializer.save(local_id=self._local_id())

    def perform_update(self, serializer):
        serializer.save(local_id=self._local_id())

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        venta = confirmar_venta(pk, local_id=self._local_id())
        return Response(VentaReadSerializer(venta).data)

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        venta = anular_venta(pk, local_id=self._local_id())
        return Response(VentaReadSerializer(venta).data)