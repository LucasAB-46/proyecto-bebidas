# backend/ventas/views.py

from decimal import Decimal
from io import BytesIO

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

import qrcode

from .models import Venta, VentaDetalle
from .serializers import VentaWriteSerializer, VentaReadSerializer
from catalogo.models import Producto


class VentaViewSet(viewsets.ModelViewSet):
    """
    /api/ventas/                -> list / create
    /api/ventas/{id}/           -> retrieve
    /api/ventas/{id}/confirmar/ -> POST confirmar
    /api/ventas/{id}/anular/    -> POST anular
    /api/ventas/{id}/ticket/    -> GET ticket PDF
    /api/ventas/historial/      -> GET (dashboard)
    """
    queryset = (
        Venta.objects
        .select_related("local", "usuario")
        .prefetch_related("detalles", "detalles__producto")
        .all()
        .order_by("-fecha", "-id")
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VentaWriteSerializer
        return VentaReadSerializer

    # =========================
    # CREAR VENTA BORRADOR
    # =========================
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Crea la venta en estado 'borrador' con sus detalles.
        RESPUESTA -> {id, estado, total}
        (esto es lo que el front necesita para después confirmar)
        """
        print("💾 perform_create() entrando...")
        print("💾 request.data =", request.data)

        serializer = VentaWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # por ahora local fijo=1, más adelante vendrá del header X-Local-ID
        venta = serializer.save(
            local_id=1,
            usuario=request.user,
        )

        # calculamos total, por si el serializer todavía no lo setea
        total_sum = Decimal("0")
        for det in venta.detalles.all():
            total_sum += Decimal(det.cantidad) * Decimal(det.precio_unitario)
        venta.total = total_sum
        venta.save(update_fields=["total"])

        # armamos respuesta cortita y clara
        data_resp = {
            "id": venta.id,
            "estado": venta.estado,
            "total": str(venta.total),
        }
        return Response(data_resp, status=status.HTTP_201_CREATED)

    # =========================
    # CONFIRMAR
    # =========================
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirmar(self, request, pk=None):
        """
        Cambia la venta a 'confirmada', descuenta stock y devuelve
        la venta final serializada.
        """
        try:
            venta = (
                Venta.objects
                .select_for_update()
                .prefetch_related("detalles", "detalles__producto")
                .get(pk=pk)
            )
        except Venta.DoesNotExist:
            return Response(
                {"detail": "Venta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if venta.estado.lower() != "borrador":
            return Response(
                {"estado": "Sólo BORRADOR puede confirmarse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1) validar stock
        for det in venta.detalles.all():
            prod = (
                Producto.objects
                .select_for_update()
                .get(pk=det.producto_id)
            )

            if prod.stock_actual < det.cantidad:
                return Response(
                    {
                        "detail": (
                            f"Stock insuficiente para {prod.nombre}: "
                            f"{prod.stock_actual} < {det.cantidad}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 2) descontar stock
        for det in venta.detalles.all():
            prod = (
                Producto.objects
                .select_for_update()
                .get(pk=det.producto_id)
            )
            prod.stock_actual = (
                Decimal(prod.stock_actual) - Decimal(det.cantidad)
            )
            prod.save(update_fields=["stock_actual"])

        # 3) marcar confirmada
        venta.estado = "confirmada"
        venta.save(update_fields=["estado", "updated_at"])

        # respuesta linda al front
        data = {
            "id": venta.id,
            "estado": venta.estado,
            "total": str(venta.total),
        }
        return Response(data, status=status.HTTP_200_OK)

    # =========================
    # ANULAR
    # =========================
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def anular(self, request, pk=None):
        """
        Cambia la venta a 'anulada', repone stock.
        Sólo si antes estaba confirmada.
        """
        try:
            venta = (
                Venta.objects
                .select_for_update()
                .prefetch_related("detalles")
                .get(pk=pk)
            )
        except Venta.DoesNotExist:
            return Response(
                {"detail": "Venta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if venta.estado.lower() != "confirmada":
            return Response(
                {"estado": "Sólo CONFIRMADA puede anularse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # reponer stock
        for det in venta.detalles.all():
            prod = (
                Producto.objects
                .select_for_update()
                .get(pk=det.producto_id)
            )
            prod.stock_actual = (
                Decimal(prod.stock_actual) + Decimal(det.cantidad)
            )
            prod.save(update_fields=["stock_actual"])

        venta.estado = "anulada"
        venta.save(update_fields=["estado", "updated_at"])

        data = {
            "id": venta.id,
            "estado": venta.estado,
            "total": str(venta.total),
        }
        return Response(data, status=status.HTTP_200_OK)

    # =========================
    # HISTORIAL (dashboard)
    # =========================
    @action(detail=False, methods=["get"])
    def historial(self, request):
        """
        /api/ventas/historial/?desde=2025-10-26&hasta=2025-10-26&estado=todos
        Devuelve ventas en ese rango de fechas (inclusive),
        filtrando opcionalmente por estado.
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

        # devolvemos lista resumida (no hace falta cada detalle ahora)
        data = [
            {
                "id": v.id,
                "fecha": v.fecha,
                "estado": v.estado,
                "total": str(v.total),
            }
            for v in qs
        ]
        return Response(data, status=status.HTTP_200_OK)

    # =========================
    # TICKET (PDF + QR)
    # =========================
    @action(detail=True, methods=["get"])
    def ticket(self, request, pk=None):
        """
        TODO: genera un PDF en memoria con los datos de la venta + QR.
        De momento devolvemos stub JSON para no romper nada.
        """
        try:
            venta = (
                Venta.objects
                .prefetch_related("detalles", "detalles__producto")
                .get(pk=pk)
            )
        except Venta.DoesNotExist:
            return Response(
                {"detail": "Venta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # más adelante: armar el PDF con reportlab + qrcode,
        # generar BytesIO, devolver como FileResponse.
        # Por ahora:
        return Response(
            {
                "ticket": f"PDF virtual de venta {venta.id} listo (stub)",
                "qr_info": f"VENTA-{venta.id}",
            },
            status=status.HTTP_200_OK,
        )
