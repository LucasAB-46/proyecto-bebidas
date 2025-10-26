# reportes/views.py
from datetime import datetime
from decimal import Decimal
from django.db.models import Sum, F
from django.utils.timezone import make_aware
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from ventas.models import Venta, VentaDetalle
from compras.models import Compra
from catalogo.models import Producto


def _parse_date(param_name, request, default=None, end_of_day=False):
    """
    Lee una fecha tipo '2025-10-26' del query param.
    Si no viene, usa default.
    Si end_of_day=True, fuerza hora 23:59:59.
    Devuelve datetime aware.
    """
    raw = request.query_params.get(param_name)
    if not raw:
        if default is None:
            return None
        dt = default
    else:
        # esperamos formato YYYY-MM-DD
        dt = datetime.strptime(raw, "%Y-%m-%d")

    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)

    # importante: hacer aware para comparar con DateTimeField
    return make_aware(dt)


class ResumenFinancieroView(APIView):
    """
    GET /api/reportes/financieros/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD

    Devuelve:
    {
      "desde": "2025-10-01",
      "hasta": "2025-10-26",
      "total_ventas": "...",
      "total_compras": "...",
      "margen_bruto": "...",  # ventas - compras
      "cantidad_ventas": 12,
      "cantidad_compras": 4
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # por ahora usamos local_id fijo 1 como en el resto del sistema
        local_id = request.headers.get("X-Local-ID", "1")

        # rango de fechas
        hasta_dt = _parse_date("hasta", request, default=datetime.utcnow(), end_of_day=True)
        desde_dt = _parse_date("desde", request, default=hasta_dt, end_of_day=False)

        # --- Ventas confirmadas en rango ---
        ventas_qs = Venta.objects.filter(
            local_id=local_id,
            estado="confirmada",
            fecha__range=[desde_dt, hasta_dt],
        )

        ventas_total = ventas_qs.aggregate(s=Sum("total"))["s"] or Decimal("0")
        ventas_count = ventas_qs.count()

        # --- Compras confirmadas en rango ---
        compras_qs = Compra.objects.filter(
            local_id=local_id,
            estado="confirmada",
            fecha__range=[desde_dt, hasta_dt],
        )

        compras_total = compras_qs.aggregate(s=Sum("total"))["s"] or Decimal("0")
        compras_count = compras_qs.count()

        margen = ventas_total - compras_total

        data = {
            "desde": desde_dt.date().isoformat(),
            "hasta": hasta_dt.date().isoformat(),
            "total_ventas": str(ventas_total),
            "total_compras": str(compras_total),
            "margen_bruto": str(margen),
            "cantidad_ventas": ventas_count,
            "cantidad_compras": compras_count,
        }
        return Response(data)


class TopProductosView(APIView):
    """
    GET /api/reportes/top-productos/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD&limit=5

    Devuelve array:
    [
      {
        "producto_id": 12,
        "producto_nombre": "Coca Cola 2.25",
        "cantidad_vendida": "18.0000",
        "facturacion": "5400.00"
      },
      ...
    ]
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        local_id = request.headers.get("X-Local-ID", "1")

        hasta_dt = _parse_date("hasta", request, default=datetime.utcnow(), end_of_day=True)
        desde_dt = _parse_date("desde", request, default=hasta_dt, end_of_day=False)

        try:
            limit = int(request.query_params.get("limit", "5"))
        except ValueError:
            limit = 5

        # Filtramos VentaDetalle de ventas confirmadas en rango
        detalles_qs = (
            VentaDetalle.objects
            .filter(
                venta__local_id=local_id,
                venta__estado="confirmada",
                venta__fecha__range=[desde_dt, hasta_dt],
            )
            .values("producto_id", "producto__nombre")
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                facturacion=Sum(F("cantidad") * F("precio_unitario")),
            )
            .order_by("-cantidad_vendida")[:limit]
        )

        data = []
        for row in detalles_qs:
            data.append({
                "producto_id": row["producto_id"],
                "producto_nombre": row["producto__nombre"],
                "cantidad_vendida": str(row["cantidad_vendida"] or 0),
                "facturacion": str(row["facturacion"] or 0),
            })

        return Response(data)
