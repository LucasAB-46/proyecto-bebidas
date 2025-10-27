from decimal import Decimal
from io import BytesIO
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from django.http import HttpResponse

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Venta, VentaDetalle
from .serializers import (
    VentaWriteSerializer,
    VentaReadSerializer,
)
from catalogo.models import Producto

# libs para PDF + QR
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import qrcode
from PIL import Image


class VentaViewSet(viewsets.ModelViewSet):
    """
    /api/ventas/                -> list / create
    /api/ventas/{id}/           -> retrieve
    /api/ventas/{id}/confirmar/ -> POST confirmar
    /api/ventas/{id}/anular/    -> POST anular
    /api/ventas/{id}/ticket/    -> GET  PDF ticket con QR
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
        Por ahora local_id=1 hasta que el FE mande X-Local-ID real.
        """
        local_id = 1
        return serializer.save(local_id=local_id, usuario=self.request.user)

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

        # control stock disponible
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
        Devuelve ventas en ese rango de fechas (inclusive),
        opcionalmente filtrando por estado.
        """
        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")
        estado = request.query_params.get("estado", "todos").lower()

        hoy = timezone.localdate()
        desde = parse_date(desde_str) or hoy
        hasta = parse_date(hasta_str) or hoy

        # cubrir todo el día 'hasta'
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

    # --------- ACCIÓN: ticket PDF con QR ----------
    @action(detail=True, methods=["get"])
    def ticket(self, request, pk=None):
        """
        GET /api/ventas/{id}/ticket/
        Devuelve un PDF (boleta simple) con:
        - Datos de la venta
        - Detalle de ítems
        - Total final
        - Código QR con la URL pública o el ID de la venta
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

        # armamos info base para el QR
        # Más adelante esto puede ser una URL pública tipo:
        # https://tu-dominio.com/ticket/VENTA_ID
        qr_text = f"VENTA {venta.id} | TOTAL ${venta.total} | ESTADO {venta.estado}"

        # generamos la imagen QR en memoria
        qr_img = qrcode.make(qr_text)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_pil = Image.open(qr_buffer)

        # generamos el PDF en memoria
        pdf_buffer = BytesIO()
        p = canvas.Canvas(pdf_buffer, pagesize=A4)

        # coordenadas base
        width, height = A4
        x_left = 40
        y_top = height - 40

        # Encabezado
        p.setFont("Helvetica-Bold", 14)
        p.drawString(x_left, y_top, "Comprobante de Venta")
        p.setFont("Helvetica", 10)
        p.drawString(x_left, y_top - 15, f"Venta #{venta.id}")
        p.drawString(x_left, y_top - 30, f"Fecha: {venta.fecha.astimezone(timezone.get_current_timezone()).strftime('%d/%m/%Y %H:%M')}")
        p.drawString(x_left, y_top - 45, f"Estado: {venta.estado.upper()}")

        # Datos del local (por ahora local_id fijo)
        if venta.local:
            p.drawString(x_left, y_top - 60, f"Sucursal: {venta.local.nombre} (ID {venta.local_id})")
        else:
            p.drawString(x_left, y_top - 60, f"Sucursal: #{venta.local_id}")

        # Usuario que cargó la venta (si existe)
        if venta.usuario:
            p.drawString(x_left, y_top - 75, f"Operador: {venta.usuario.username}")

        # Tabla de ítems
        y_cursor = y_top - 110
        p.setFont("Helvetica-Bold", 10)
        p.drawString(x_left, y_cursor, "Producto")
        p.drawString(x_left + 200, y_cursor, "Cant.")
        p.drawString(x_left + 250, y_cursor, "P.Unit")
        p.drawString(x_left + 310, y_cursor, "Subtot.")
        p.setFont("Helvetica", 10)

        y_cursor -= 15
        for det in venta.detalles.all():
            nombre_prod = det.producto.nombre if det.producto else f"ID {det.producto_id}"
            p.drawString(x_left, y_cursor, nombre_prod[:28])
            p.drawRightString(x_left + 230, y_cursor, f"{det.cantidad}")
            p.drawRightString(x_left + 300, y_cursor, f"${det.precio_unitario}")
            p.drawRightString(x_left + 360, y_cursor, f"${det.total_renglon}")
            y_cursor -= 12

            # salto de página simple si nos quedamos sin lugar
            if y_cursor < 120:
                p.showPage()
                y_cursor = height - 60
                p.setFont("Helvetica", 10)

        # Totales
        y_cursor -= 20
        p.setFont("Helvetica-Bold", 11)
        p.drawRightString(x_left + 360, y_cursor, f"Subtotal: ${venta.subtotal}")
        y_cursor -= 14
        p.drawRightString(x_left + 360, y_cursor, f"Impuestos: ${venta.impuestos}")
        y_cursor -= 14
        p.drawRightString(x_left + 360, y_cursor, f"Bonif: ${venta.bonificaciones}")
        y_cursor -= 14
        p.setFont("Helvetica-Bold", 13)
        p.drawRightString(x_left + 360, y_cursor, f"TOTAL: ${venta.total}")

        # QR abajo a la izquierda
        # pasamos la imagen PIL al canvas de reportlab
        y_qr = 80
        x_qr = x_left
        qr_size = 100

        qr_tmp = BytesIO()
        qr_pil.save(qr_tmp, format="PNG")
        qr_tmp.seek(0)

        p.drawInlineImage(qr_tmp, x_qr, y_qr, width=qr_size, height=qr_size)
        p.setFont("Helvetica", 8)
        p.drawString(x_qr, y_qr - 12, "Escanear para verificar venta")

        # cerrar PDF
        p.showPage()
        p.save()

        pdf_buffer.seek(0)

        filename = f"venta_{venta.id}.pdf"

        return HttpResponse(
            pdf_buffer.getvalue(),
            content_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"'
            },
        )
