from datetime import datetime, time
from decimal import Decimal

from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ventas.models import Venta
from compras.models import Compra
from catalogo.models import Producto


def _inicio_fin_de_fecha(date_obj):
    """
    Helper: dado un date (YYYY-MM-DD) devuelve (inicio, fin)
    del día en esa timezone.
    """
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(
        datetime.combine(date_obj, time.min),
        tz,
    )
    end_dt = timezone.make_aware(
        datetime.combine(date_obj, time.max),
        tz,
    )
    return start_dt, end_dt


class ResumenFinancieroView(APIView):
    """
    GET /api/reportes/financieros/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    Devuelve totales de ventas/compras en el rango y el balance.
    Este endpoint ya existía (lo usás en Swagger), lo mantenemos vivo.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # 1. local desde header
        local_id = request.headers.get("X-Local-ID")
        if not local_id:
            return Response(
                {"detail": "Falta header X-Local-ID"},
                status=400,
            )

        # 2. leer query params
        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")

        # si no vienen fechas, usamos HOY como rango
        hoy_local = timezone.localtime().date()

        try:
            if desde_str:
                desde_date = datetime.strptime(desde_str, "%Y-%m-%d").date()
            else:
                desde_date = hoy_local

            if hasta_str:
                hasta_date = datetime.strptime(hasta_str, "%Y-%m-%d").date()
            else:
                hasta_date = hoy_local
        except ValueError:
            return Response(
                {"detail": "Formato inválido. Use YYYY-MM-DD"},
                status=400,
            )

        # normalizamos para incluir todos los días desde...hasta...
        # ejemplo: si desde=2025-10-20 y hasta=2025-10-26
        # queremos rango [20 00:00 ... 26 23:59:59]
        tz = timezone.get_current_timezone()
        inicio = timezone.make_aware(
            datetime.combine(desde_date, time.min),
            tz,
        )
        fin = timezone.make_aware(
            datetime.combine(hasta_date, time.max),
            tz,
        )

        # 3. Ventas confirmadas dentro del rango para ese local
        ventas_qs = Venta.objects.filter(
            local_id=local_id,
            estado__iexact="confirmada",
            fecha__gte=inicio,
            fecha__lte=fin,
        )

        ventas_aggr = ventas_qs.aggregate(
            cantidad=Count("id"),
            total=Sum("total"),
        )
        ventas_cantidad = ventas_aggr["cantidad"] or 0
        ventas_total = ventas_aggr["total"] or Decimal("0.00")

        # 4. Compras confirmadas en el rango
        compras_qs = Compra.objects.filter(
            local_id=local_id,
            estado__iexact="confirmada",
            fecha__gte=inicio,
            fecha__lte=fin,
        )

        compras_aggr = compras_qs.aggregate(
            cantidad=Count("id"),
            total=Sum("total"),
        )
        compras_cantidad = compras_aggr["cantidad"] or 0
        compras_total = compras_aggr["total"] or Decimal("0.00")

        # 5. Balance = ventas - compras
        balance = ventas_total - compras_total

        data = {
            "periodo": {
                "desde": inicio.isoformat(),
                "hasta": fin.isoformat(),
            },
            "ventas": {
                "cantidad": str(ventas_cantidad),
                "total": str(ventas_total),
            },
            "compras": {
                "cantidad": str(compras_cantidad),
                "total": str(compras_total),
            },
            "balance": str(balance),
        }

        return Response(data, status=200)


class ResumenDiaView(APIView):
    """
    GET /api/reportes/resumen-dia/
    Devuelve:
    - ventas de hoy
    - compras de hoy
    - balance
    - stock bajo
    - últimos movimientos
    Este endpoint lo consume el Dashboard del frontend.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # 1. Local
        local_id = request.headers.get("X-Local-ID")
        if not local_id:
            return Response(
                {"detail": "Falta header X-Local-ID"},
                status=400,
            )

        # 2. Rango del día actual
        ahora = timezone.localtime()
        inicio_hoy, fin_hoy = _inicio_fin_de_fecha(ahora.date())

        # 3. Ventas confirmadas hoy
        ventas_qs = Venta.objects.filter(
            local_id=local_id,
            estado__iexact="confirmada",
            fecha__gte=inicio_hoy,
            fecha__lte=fin_hoy,
        )

        ventas_aggr = ventas_qs.aggregate(
            cantidad=Count("id"),
            total=Sum("total"),
        )
        ventas_cantidad = ventas_aggr["cantidad"] or 0
        ventas_total = ventas_aggr["total"] or Decimal("0.00")

        ultima_venta = (
            ventas_qs.order_by("-fecha")
            .values("id", "estado", "total", "fecha")
            .first()
        )
        venta_dict = None
        if ultima_venta:
            venta_dict = {
                "id": ultima_venta["id"],
                "estado": ultima_venta["estado"],
                "total": str(ultima_venta["total"] or "0.00"),
                "hora": timezone.localtime(ultima_venta["fecha"]).strftime("%H:%M"),
            }

        # 4. Compras confirmadas hoy
        compras_qs = Compra.objects.filter(
            local_id=local_id,
            estado__iexact="confirmada",
            fecha__gte=inicio_hoy,
            fecha__lte=fin_hoy,
        )

        compras_aggr = compras_qs.aggregate(
            cantidad=Count("id"),
            total=Sum("total"),
        )
        compras_cantidad = compras_aggr["cantidad"] or 0
        compras_total = compras_aggr["total"] or Decimal("0.00")

        ultima_compra = (
            compras_qs.order_by("-fecha")
            .values("id", "estado", "total", "fecha")
            .first()
        )
        compra_dict = None
        if ultima_compra:
            compra_dict = {
                "id": ultima_compra["id"],
                "estado": ultima_compra["estado"],
                "total": str(ultima_compra["total"] or "0.00"),
                "hora": timezone.localtime(ultima_compra["fecha"]).strftime("%H:%M"),
            }

        # 5. Balance hoy
        balance_decimal = ventas_total - compras_total

        # 6. Stock bajo (<= 5 unidades)
        stock_bajo_qs = (
            Producto.objects.filter(local_id=local_id)
            .values("id", "nombre", "stock_actual")
            .order_by("stock_actual")[:10]
        )

        stock_bajo_list = []
        for row in stock_bajo_qs:
            stock = row.get("stock_actual") or 0
            if stock <= 5:
                stock_bajo_list.append(
                    {
                        "id": row["id"],
                        "nombre": row["nombre"],
                        "stock": stock,
                    }
                )

        data = {
            "fecha": ahora.date().isoformat(),
            "ventas": {
                "cantidad": str(ventas_cantidad),
                "total": str(ventas_total),
            },
            "compras": {
                "cantidad": str(compras_cantidad),
                "total": str(compras_total),
            },
            "balance": str(balance_decimal),
            "stock_bajo": stock_bajo_list,
            "ultimos_movimientos": {
                "venta": venta_dict,
                "compra": compra_dict,
            },
        }

        return Response(data, status=200)
