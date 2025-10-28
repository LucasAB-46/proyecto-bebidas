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


class VentaViewSet(viewsets.ModelViewSet):
    """
    Endpoints principales:
    - GET    /api/ventas/
    - POST   /api/ventas/
    - GET    /api/ventas/{id}/
    - POST   /api/ventas/{id}/confirmar/
    - POST   /api/ventas/{id}/anular/
    - GET    /api/ventas/historial/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD&estado=todos
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
        Crea la venta inicial en estado 'borrador'.
        Lee el local desde X-Local-ID, si no viene usa 1.
        Además inyecta self.request.user.
        """
        raw_local = self.request.META.get("HTTP_X_LOCAL_ID")
        try:
            local_id = int(raw_local)
        except (TypeError, ValueError):
            local_id = 1  # fallback seguro

        try:
            serializer.save(
                local_id=local_id,
                usuario=self.request.user,
            )
        except Exception as e:
            # Log fuerte en server y devolvemos 400 en vez de 500
            print("⚠️ ERROR en perform_create / POST /api/ventas/:", repr(e))
            raise

    # --------- ACCIÓN: confirmar venta ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirmar(self, request, pk=None):
        """
        Cambia la venta a 'confirmada', descuenta stock,
        devuelve la venta + QR base64.
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

        # validar stock
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

        # marcar confirmada
        venta.estado = "confirmada"
        venta.save(update_fields=["estado", "updated_at"])

        # serializar venta confirmada
        venta_data = VentaReadSerializer(venta).data

        # generar QR base64 con {id,total,fecha}
        qr_payload = {
            "venta_id": venta.id,
            "total": str(venta.total),
            "fecha": venta.fecha.isoformat(),
        }
        qr_img = qrcode.make(qr_payload)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return Response(
            {
                "venta": venta_data,
                "qr_base64": qr_b64,
            },
            status=status.HTTP_200_OK,
        )

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

        # default: hoy
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
