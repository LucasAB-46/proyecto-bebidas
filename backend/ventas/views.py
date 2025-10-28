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

from .models import Venta, VentaDetalle
from .serializers import (
    VentaWriteSerializer,
    VentaReadSerializer,
)
from catalogo.models import Producto

# --- helpers internos -------------------------------------------------

def build_qr_base64(venta_id: int) -> str:
    """
    Genera un QR simple (PNG) con la URL pública de la venta
    y lo devuelve como base64 string.
    """
    # esto podría ser un link al comprobante público o al admin
    qr_text = f"https://proyecto-bebidas-75q3.vercel.app/ticket/{venta_id}"

    qr_img = qrcode.make(qr_text)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    b64 = base64.b64encode(buffer.read()).decode("utf-8")
    return b64


def build_pdf_ticket_base64(venta: Venta) -> str:
    """
    Genera un PDF básico con datos de la venta
    y lo devuelve como base64 string.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    y = 750
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Ticket Venta #{venta.id}")
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Fecha: {venta.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 15
    c.drawString(50, y, f"Local: {venta.local.nombre if venta.local else '-'}")
    y -= 15
    c.drawString(50, y, f"Estado: {venta.estado}")
    y -= 15
    c.drawString(50, y, f"Total: ${venta.total}")
    y -= 30

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Detalle:")
    y -= 20

    c.setFont("Helvetica", 9)
    for det in venta.detalles.all():
        linea = (
            f"{det.renglon}. {det.producto.nombre}  x{det.cantidad} "
            f"@ ${det.precio_unitario}  -> ${det.total_renglon}"
        )
        c.drawString(50, y, linea)
        y -= 12
        if y < 80:
            c.showPage()
            y = 750
            c.setFont("Helvetica", 9)

    c.showPage()
    c.save()

    buffer.seek(0)
    pdf_bytes = buffer.read()
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    return b64


# --- ViewSet principal ------------------------------------------------

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

    # ⚠️ OJO: este override es CLAVE para que el frontend reciba {id,...}
    def create(self, request, *args, **kwargs):
        """
        Creamos venta en estado 'borrador', con detalles,
        y devolvemos al frontend al menos {id, estado, total}.
        """
        print("💾 perform_create() entrando...")
        print("💾 request.data =", request.data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        venta = self.perform_create(serializer)

        data_res = {
            "id": venta.id,
            "estado": venta.estado,
            "total": str(venta.total),
        }

        headers = self.get_success_headers(serializer.data)
        return Response(data_res, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        Creamos la venta en estado 'borrador' con sus detalles y totales.
        Le pasamos local_id fijo=1 hasta que soportemos multi-local en el FE.
        """
        # en el futuro local_id vendrá del header X-Local-ID
        # local_id = int(self.request.META.get("HTTP_X_LOCAL_ID", "1"))
        local_id = 1

        # guardamos la venta usando el serializer.write
        venta = serializer.save(local_id=local_id, usuario=self.request.user)

        # IMPORTANTE: recalcular totales básicos acá si el serializer no lo hizo
        subtotal = Decimal("0")
        impuestos = Decimal("0")
        bonif = Decimal("0")
        total = Decimal("0")

        # ahora garantizamos que cada detalle tiene total_renglon correcto
        for det in venta.detalles.all():
            linea_total = (
                Decimal(det.cantidad) * Decimal(det.precio_unitario)
                - Decimal(det.bonif or 0)
                + Decimal(det.impuestos or 0)
            )
            det.total_renglon = linea_total
            det.save(update_fields=["total_renglon"])

            subtotal += Decimal(det.cantidad) * Decimal(det.precio_unitario)
            impuestos += Decimal(det.impuestos or 0)
            bonif += Decimal(det.bonif or 0)
            total += linea_total

        venta.subtotal = subtotal
        venta.impuestos = impuestos
        venta.bonificaciones = bonif
        venta.total = total
        venta.save(update_fields=["subtotal", "impuestos", "bonificaciones", "total"])

        return venta

    # --------- ACCIÓN: confirmar venta ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirmar(self, request, pk=None):
        """
        Cambia la venta a 'confirmada', descuenta stock,
        y devuelve datos de la venta + QR + ticket PDF en base64.
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
            prod = Producto.objects.select_for_update().get(pk=det.producto_id)
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
            prod = Producto.objects.select_for_update().get(pk=det.producto_id)
            prod.stock_actual = (
                Decimal(prod.stock_actual) - Decimal(det.cantidad)
            )
            prod.save(update_fields=["stock_actual"])

        # marcar confirmada
        venta.estado = "confirmada"
        venta.save(update_fields=["estado", "updated_at"])

        # serializamos venta completa (lectura)
        data_venta = VentaReadSerializer(venta).data

        # generamos QR y PDF
        qr_b64 = build_qr_base64(venta.id)
        pdf_b64 = build_pdf_ticket_base64(venta)

        respuesta = {
            "venta": data_venta,
            "qr_base64": qr_b64,
            "ticket_pdf_base64": pdf_b64,
        }

        return Response(respuesta, status=status.HTTP_200_OK)

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
                .prefetch_related("detalles", "detalles__producto")
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
            prod = Producto.objects.select_for_update().get(pk=det.producto_id)
            prod.stock_actual = (
                Decimal(prod.stock_actual) + Decimal(det.cantidad)
            )
            prod.save(update_fields=["stock_actual"])

        venta.estado = "anulada"
        venta.save(update_fields=["estado", "updated_at"])

        data_venta = VentaReadSerializer(venta).data
        return Response(data_venta, status=status.HTTP_200_OK)

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
