from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db import transaction

from .models import Venta
from .serializers import VentaWriteSerializer, VentaReadSerializer
from .services import confirmar_venta, anular_venta


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all().order_by("-id")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return VentaWriteSerializer
        return VentaReadSerializer

    def _local_id(self):
        # el mismo truco que usamos en Compras
        hdr = self.request.headers.get("X-Local-ID") or self.request.META.get("HTTP_X_LOCAL_ID")
        try:
            return int(hdr)
        except (TypeError, ValueError):
            return 1  # fallback por ahora

    def perform_create(self, serializer):
        serializer.save(local_id=self._local_id(), usuario=self.request.user)

    def perform_update(self, serializer):
        serializer.save(local_id=self._local_id(), usuario=self.request.user)

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        venta = confirmar_venta(pk, local_id=self._local_id())
        return Response(VentaReadSerializer(venta).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        venta = anular_venta(pk, local_id=self._local_id())
        return Response(VentaReadSerializer(venta).data, status=status.HTTP_200_OK)
