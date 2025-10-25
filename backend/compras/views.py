from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Compra
from .serializers import CompraReadSerializer, CompraWriteSerializer
from .services import confirmar_compra, anular_compra
# si tenés permisos custom reales, usalos; mientras tanto dejamos IsAuthenticated
from rest_framework.permissions import IsAuthenticated


class LocalScopedMixin:
    """
    Mixin para:
    - leer el header X-Local-ID
    - filtrar queryset por ese local
    """
    local_header = "X-Local-ID"

    def _local_id(self) -> int:
        raw = self.request.headers.get(self.local_header)
        if not raw:
            raise ValidationError({self.local_header: "Header requerido"})
        try:
            return int(raw)
        except ValueError:
            raise ValidationError({self.local_header: "Debe ser entero"})

    def get_queryset(self):
        return (
            Compra.objects
            .filter(local_id=self._local_id())
            .order_by("-id")
        )


class CompraViewSet(LocalScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["id", "proveedor__nombre", "estado"]
    ordering_fields = ["id", "fecha", "total"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CompraWriteSerializer
        return CompraReadSerializer

    def perform_create(self, serializer):
        # Le pasamos el local_id que el serializer espera
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
