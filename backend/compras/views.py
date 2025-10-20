# compras/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Compra
from .serializers import CompraReadSerializer, CompraWriteSerializer
from .services import confirmar_compra, anular_compra
# --- 1. IMPORTAMOS EL NUEVO PERMISO ---
from core_app.permissions import IsAdminUser

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
        # Asumimos que el modelo Compra tiene un campo 'local_id'
        return Compra.objects.filter(local_id=self._local_id()).order_by("-id")

class CompraViewSet(LocalScopedMixin, viewsets.ModelViewSet):
    # --- 2. APLICAMOS PERMISO ---
    # Solo los usuarios del grupo 'Admin' pueden acceder a las compras.
    permission_classes = [IsAdminUser]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["id", "proveedor__nombre", "estado"]
    ordering_fields = ["id", "fecha", "total"]

    def get_serializer_class(self):
        return CompraWriteSerializer if self.action in ("create","update","partial_update") else CompraReadSerializer

    def perform_create(self, serializer):
        serializer.save(local_id=self._local_id())

    def perform_update(self, serializer):
        serializer.save(local_id=self._local_id())

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        compra = confirmar_compra(pk, local_id=self._local_id())
        return Response(CompraReadSerializer(compra).data)

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        compra = anular_compra(pk, local_id=self._local_id())
        return Response(CompraReadSerializer(compra).data)