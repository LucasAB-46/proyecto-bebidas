from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Compra, CompraDetalle
from .serializers import (
    CompraWriteSerializer,
    CompraReadSerializer,
)
from catalogo.models import Producto


class CompraViewSet(viewsets.ModelViewSet):
    """
    /api/compras/                -> list / create
    /api/compras/{id}/           -> retrieve
    /api/compras/{id}/confirmar/ -> POST confirmar
    /api/compras/{id}/anular/    -> POST anular
    /api/compras/historial/      -> GET con filtros fecha/estado (para dashboard)
    """
    queryset = (
        Compra.objects
        .select_related("local", "proveedor")
        .prefetch_related("detalles", "detalles__producto")
        .all()
        .order_by("-fecha", "-id")
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CompraWriteSerializer
        return CompraReadSerializer

    def perform_create(self, serializer):
        """
        Creamos la compra en estado 'borrador' con sus detalles y totales.
        local_id = 1 hasta que tengamos multilocal en FE.
        """
        local_id = 1
        return serializer.save(local_id=local_id)

    # --------- ACCIÓN: confirmar compra ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirmar(self, request, pk=None):
        """
        Cambia la compra a 'confirmada', aumenta stock.
        Sólo borrador puede confirmarse.
        """
        try:
            compra = (
                Compra.objects
                .select_for_update()
                .prefetch_related("detalles")
                .get(pk=pk)
            )
        except Compra.DoesNotExist:
            return Response(
                {"detail": "Compra no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if compra.estado.lower() != "borrador":
            return Response(
                {"estado": "Sólo BORRADOR puede confirmarse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # sumamos stock
        for det in compra.detalles.all():
            prod = (
                Producto.objects
                .select_for_update()
                .get(pk=det.producto_id)
            )
            prod.stock_actual = (
                Decimal(prod.stock_actual) + Decimal(det.cantidad)
            )
            prod.save(update_fields=["stock_actual"])

        compra.estado = "confirmada"
        compra.save(update_fields=["estado", "updated_at"])

        data = CompraReadSerializer(compra).data
        return Response(data, status=status.HTTP_200_OK)

    # --------- ACCIÓN: anular compra ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def anular(self, request, pk=None):
        """
        Cambia la compra a 'anulada', resta el stock que había sumado.
        Sólo confirmada puede anularse.
        """
        try:
            compra = (
                Compra.objects
                .select_for_update()
                .prefetch_related("detalles")
                .get(pk=pk)
            )
        except Compra.DoesNotExist:
            return Response(
                {"detail": "Compra no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if compra.estado.lower() != "confirmada":
            return Response(
                {"estado": "Sólo CONFIRMADA puede anularse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for det in compra.detalles.all():
            prod = (
                Producto.objects
                .select_for_update()
                .get(pk=det.producto_id)
            )
            prod.stock_actual = (
                Decimal(prod.stock_actual) - Decimal(det.cantidad)
            )
            prod.save(update_fields=["stock_actual"])

        compra.estado = "anulada"
        compra.save(update_fields=["estado", "updated_at"])

        data = CompraReadSerializer(compra).data
        return Response(data, status=status.HTTP_200_OK)

    # --------- ACCIÓN: historial (para Dashboard) ----------
    @action(detail=False, methods=["get"])
    def historial(self, request):
        """
        /api/compras/historial/?desde=2025-10-26&hasta=2025-10-26&estado=todos

        Devuelve compras en ese rango de fechas (inclusive),
        opcionalmente filtrando por estado.
        """
        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")
        estado = request.query_params.get("estado", "todos").lower()

        hoy = timezone.localdate()
        desde = parse_date(desde_str) or hoy
        hasta = parse_date(hasta_str) or hoy

        desde_dt = timezone.make_aware(
            timezone.datetime.combine(
                desde, timezone.datetime.min.time()
            )
        )
        hasta_dt = timezone.make_aware(
            timezone.datetime.combine(
                hasta, timezone.datetime.max.time()
            )
        )

        qs = (
            self.get_queryset()
            .filter(fecha__range=(desde_dt, hasta_dt))
            .prefetch_related("detalles", "detalles__producto")
        )

        if estado != "todos":
            qs = qs.filter(estado__iexact=estado)

        data = CompraReadSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)
