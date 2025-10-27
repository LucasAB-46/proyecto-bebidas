from decimal import Decimal
from io import BytesIO
import base64
import qrcode

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Venta, VentaDetalle
from .serializers import (
    VentaWriteSerializer,
    VentaReadSerializer,
)
from catalogo.models import Producto


class VentaViewSet(viewsets.ModelViewSet):
    """
    /api/ventas/                -> list / create
    /api/ventas/{id}/           -> retrieve
    /api/ventas/{id}/confirmar/ -> POST confirmar
    /api/ventas/{id}/anular/    -> POST anular
    /api/ventas/{id}/ticket/    -> GET ticket PDF base64 (+ QR)
    /api/ventas/historial/      -> GET filtro fecha/estado (dashboard)
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

    def perform_create(self, serializer):
        """
        Crea la venta en estado 'borrador' con sus detalles.
        local_id viene del header X-Local-ID (multi-sucursal). Fallback = 1.
        """
        raw_local = self.request.META.get("HTTP_X_LOCAL_ID")
        try:
            local_id = int(raw_local)
        except (TypeError, ValueError):
            local_id = 1  # fallback seguro

        serializer.save(
            local_id=local_id,
            usuario=self.request.user,
        )

    # --------- ACCIÓN: confirmar venta ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirmar(self, request, pk=None):
        """
        Cambia la venta a 'confirmada', descuenta stock.
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

        if venta.estado.lower() != "borrador":
            return Response(
                {"estado": "Sólo BORRADOR puede confirmarse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1) CONTROL STOCK
        for det in venta.detalles.all():
            prod = (
                Producto.objects
                .select_for_update()
                .get(pk=det.producto_id)
            )

            # si el producto nunca tuvo stock cargado, tratamos como 0
            actual = Decimal(prod.stock_actual or 0)
            cant = Decimal(det.cantidad or 0)

            if actual < cant:
                return Response(
                    {
                        "detail": (
                            f"Stock insuficiente para {prod.nombre}: "
                            f"{actual} < {cant}"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 2) DESCONTAR STOCK
        for det in venta.detalles.all():
            prod = (
                Producto.objects
                .select_for_update()
                .get(pk=det.producto_id)
            )

            actual = Decimal(prod.stock_actual or 0)
            cant = Decimal(det.cantidad or 0)

            prod.stock_actual = actual - cant
            prod.save(update_fields=["stock_actual"])

        # 3) MARCAR CONFIRMADA
        venta.estado = "confirmada"
        venta.save(update_fields=["estado", "updated_at"])

        data = VentaReadSerializer(venta).data
        return Response(data, status=status.HTTP_200_OK)

    # --------- ACCIÓN: anular venta ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def anular(self, request, pk=None):
        """
        Cambia la venta a 'anulada', repone stock.
        Sólo se puede anular si está confirmada.
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

            actual = Decimal(prod.stock_actual or 0)
            cant = Decimal(det.cantidad or 0)

            prod.stock_actual = actual + cant
            prod.save(update_fields=["stock_actual"])

        venta.estado = "anulada"
        venta.save(update_fields=["estado", "updated_at"])

        data = VentaReadSerializer(venta).data
        return Response(data, status=status.HTTP_200_OK)

    # --------- ACCIÓN: historial (para Dashboard) ----------
    @action(detail=False, methods=["get"])
    def historial(self, request):
        """
        /api/ventas/historial/?desde=2025-10-26&hasta=2025-10-26&estado=todos

        Devuelve ventas en ese rango de fechas (inclusive),
        opcionalmente filtrando por estado.
        """
        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")
        estado = request.query_params.get("estado", "todos").lower()

        hoy = timezone.localdate()
        desde = parse_date(desde_str) or hoy
        hasta = parse_date(hasta_str) or hoy

        # datetimes con todo el día
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

        data = VentaReadSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    # --------- ACCIÓN: ticket con QR ----------
    @action(detail=True, methods=["get"])
    def ticket(self, request, pk=None):
        """
        Devuelve el ticket de la venta en PDF (base64) y además
        un PNG QR (base64) separado.

        {
          "pdf_base64": "...",
          "qr_base64": "..."
        }
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

        qr_payload = f"VENTA:{venta.id}|TOTAL:{venta.total}|ESTADO:{venta.estado}"
        qr_img = qrcode.make(qr_payload)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_bytes = qr_buffer.getvalue()
        qr_b64 = base64.b64encode(qr_bytes).decode("utf-8")

        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)

        y = 750
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Venta #{venta.id} - Estado: {venta.estado.upper()}")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Fecha: {venta.fecha.strftime('%Y-%m-%d %H:%M')}")
        y -= 30

        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Item")
        c.drawString(200, y, "Cant")
        c.drawString(250, y, "P.Unit")
        c.drawString(320, y, "Total")
        y -= 15
        c.line(50, y, 400, y)
        y -= 15

        c.setFont("Helvetica", 10)
        for det in venta.detalles.all():
            nombre = det.producto.nombre if det.producto else "Producto"
            c.drawString(50, y, nombre[:18])
            c.drawString(200, y, str(det.cantidad))
            c.drawString(250, y, f"${det.precio_unitario}")
            c.drawString(320, y, f"${det.total_renglon}")
            y -= 15
            if y < 100:
                c.showPage()
                y = 750

        y -= 20
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, f"TOTAL: ${venta.total}")
        y -= 40

        qr_tmp = BytesIO(qr_bytes)
        c.drawInlineImage(qr_tmp, 50, y, width=100, height=100)

        c.showPage()
        c.save()

        pdf_bytes = pdf_buffer.getvalue()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return Response(
            {
                "pdf_base64": pdf_b64,
                "qr_base64": qr_b64,
            },
            status=status.HTTP_200_OK,
        )
