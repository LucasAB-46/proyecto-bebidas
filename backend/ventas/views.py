from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Venta, VentaDetalle
from .serializers import (
    VentaWriteSerializer,
    VentaReadSerializer,
)
from catalogo.models import Producto

from .utils_pdf import build_ticket_pdf  # ⬅ nuevo


def _get_local_id_from_header(request):
    """
    Lee el header X-Local-ID. Devuelve int.
    Si no viene, por ahora fallback a 1.
    """
    raw = request.META.get("HTTP_X_LOCAL_ID") or "1"
    try:
        return int(raw)
    except ValueError:
        return 1


class VentaViewSet(viewsets.ModelViewSet):
    """
    /api/ventas/                -> list / create
    /api/ventas/{id}/           -> retrieve
    /api/ventas/{id}/confirmar/ -> POST confirmar
    /api/ventas/{id}/anular/    -> POST anular
    /api/ventas/{id}/ticket/    -> GET ticket PDF + QR
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

    # ---------- CREATE ----------
    def perform_create(self, serializer):
        """
        Creamos la venta en estado 'borrador' con sus detalles y totales.
        local_id ahora viene del header X-Local-ID (multi-sucursal).
        """
        local_id = _get_local_id_from_header(self.request)
        return serializer.save(local_id=local_id, usuario=self.request.user)

    # ---------- HELPERS DE ACCESO ----------
    def _get_venta_for_local(self, pk, request, for_update=False):
        """
        Trae la venta y valida que pertenezca al local actual.
        if for_update=True -> select_for_update()
        """
        local_id = _get_local_id_from_header(request)

        base_qs = Venta.objects.prefetch_related("detalles", "detalles__producto")

        if for_update:
            base_qs = base_qs.select_for_update()

        try:
            venta = base_qs.get(pk=pk)
        except Venta.DoesNotExist:
            raise PermissionDenied("Venta no encontrada")

        if venta.local_id != local_id:
            # Intento acceder/anular/confirmar una venta de otra sucursal.
            raise PermissionDenied("No tenés acceso a esta venta.")

        return venta

    # ---------- ACCIÓN: confirmar ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def confirmar(self, request, pk=None):
        """
        Cambia la venta a 'confirmada', descuenta stock.
        """
        try:
            venta = self._get_venta_for_local(pk, request, for_update=True)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response(
                {"detail": "Venta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if venta.estado.lower() != "borrador":
            return Response(
                {"estado": "Sólo BORRADOR puede confirmarse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # control stock
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

    # ---------- ACCIÓN: anular ----------
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def anular(self, request, pk=None):
        """
        Cambia la venta a 'anulada', repone stock.
        Sólo se puede anular si está confirmada.
        """
        try:
            venta = self._get_venta_for_local(pk, request, for_update=True)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
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

    # ---------- ACCIÓN: ticket (PDF con QR) ----------
    @action(detail=True, methods=["get"])
    def ticket(self, request, pk=None):
        """
        /api/ventas/{id}/ticket/
        Devuelve un PDF con el comprobante (incluye QR).
        """
        try:
            venta = self._get_venta_for_local(pk, request, for_update=False)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response(
                {"detail": "Venta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # opcionalmente podríamos bloquear ticket si está anulada
        # si querés eso, descomentá:
        # if venta.estado.lower() == "anulada":
        #     return Response(
        #         {"detail": "Venta anulada. No se emite ticket."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        # URL pública base del front para el QR.
        # Podrías meterlo en settings (env var). Por ahora hardcode lindo:
        PUBLIC_FRONT_BASE = "https://proyecto-bebidas.vercel.app"

        pdf_bytes = build_ticket_pdf(venta, PUBLIC_FRONT_BASE)

        # armamos la Response "a mano", no DRF Response
        # porque necesitamos headers binarios puros
        from django.http import HttpResponse

        resp = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )
        resp["Content-Disposition"] = f'inline; filename="ticket_venta_{venta.id}.pdf"'
        return resp

    # ---------- ACCIÓN: historial ----------
    @action(detail=False, methods=["get"])
    def historial(self, request):
        """
        /api/ventas/historial/?desde=2025-10-26&hasta=2025-10-26&estado=todos

        Devuelve ventas en ese rango de fechas (inclusive),
        opcionalmente filtrando por estado.
        Sólo del local actual.
        """
        local_id = _get_local_id_from_header(request)

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
            .filter(local_id=local_id, fecha__range=(desde_dt, hasta_dt))
            .prefetch_related("detalles", "detalles__producto")
        )

        if estado != "todos":
            qs = qs.filter(estado__iexact=estado)

        data = VentaReadSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)
