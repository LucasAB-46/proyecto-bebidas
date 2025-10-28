from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Venta, VentaDetalle
from .serializers import (
    VentaWriteSerializer,
    VentaReadSerializer,
    VentaDetalleReadSerializer,
)
from catalogo.models import Producto

import io
import base64
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


class VentaViewSet(viewsets.ModelViewSet):
    """
    /api/ventas/                -> list / create
    /api/ventas/{id}/           -> retrieve
    /api/ventas/{id}/confirmar/ -> POST confirmar
    /api/ventas/{id}/anular/    -> POST anular
    /api/ventas/historial/      -> GET con filtros fecha/estado (para dashboard)
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
        Creamos la venta en estado 'borrador' con sus detalles y totales.
        Le pasamos local_id fijo=1 hasta que soportemos multi-local en el FE.
        """

        local_id = 1  # TODO: luego leer request.META["HTTP_X_LOCAL_ID"]
        usuario = self.request.user

        # DEBUG LOG EN SERVER
        print("💾 perform_create() entrando...")
        print("💾 request.data =", self.request.data)

        try:
            venta = serializer.save(local_id=local_id, usuario=usuario)
        except Exception as e:
            # log para ver bien qué está pasando
            print("💥 perform_create() ERROR:", repr(e))
            raise

        return venta

    # --------- ACCIÓN: confirmar venta ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirmar(self, request, pk=None):
        """
        Cambia la venta a 'confirmada', descuenta stock.
        También genera QR y PDF en memoria.
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

        # control de stock
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

        # descontar stock
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

        venta.estado = "confirmada"
        venta.save(update_fields=["estado", "updated_at"])

        # -------- QR ----------
        qr_info = f"VENTA:{venta.id}|TOTAL:{venta.total}|FECHA:{venta.fecha.isoformat()}"
        qr_img = qrcode.make(qr_info)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_b64 = base64.b64encode(qr_buffer.getvalue()).decode("utf-8")

        # -------- PDF ticket simple ----------
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        y = 800

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"Ticket Venta #{venta.id}")
        y -= 20

        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"Fecha: {venta.fecha.strftime('%Y-%m-%d %H:%M')}")
        y -= 15
        c.drawString(50, y, f"Local: {venta.local.nombre if venta.local else 'N/D'}")
        y -= 15
        c.drawString(50, y, f"Atendió: {venta.usuario.username if venta.usuario else 'N/D'}")
        y -= 30

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Detalle:")
        y -= 15

        c.setFont("Helvetica", 10)
        for det in venta.detalles.all():
            linea = f"{det.cantidad} x {det.producto.nombre} @ ${det.precio_unitario} = ${det.total_renglon}"
            c.drawString(60, y, linea)
            y -= 12
            if y < 100:
                c.showPage()
                y = 800
                c.setFont("Helvetica", 10)

        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"TOTAL: ${venta.total}")
        y -= 40

        # incrustar QR como imagen
        qr_buffer.seek(0)
        c.drawInlineImage(qr_buffer, 50, y - 150, width=150, height=150)
        c.showPage()
        c.save()

        pdf_b64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")

        # respuesta final
        data = VentaReadSerializer(venta).data
        data["qr_base64"] = qr_b64
        data["ticket_pdf_base64"] = pdf_b64

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
            prod.stock_actual = (
                Decimal(prod.stock_actual) + Decimal(det.cantidad)
            )
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

        data = VentaReadSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)
