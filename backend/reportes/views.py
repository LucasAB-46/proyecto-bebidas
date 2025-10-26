from datetime import datetime, timedelta
from decimal import Decimal

from django.utils.timezone import make_aware
from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ventas.models import Venta
from compras.models import Compra


class ReporteFinancieroView(APIView):
    """
    GET /api/reportes/financieros/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD

    Respuesta:
    {
      "periodo": { "desde": "...", "hasta": "..." },
      "ventas":  { "cantidad": "12", "total": "12345.67" },
      "compras": { "cantidad": "4",  "total": "2345.00"  },
      "balance": "9999.67"
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # 1) leer query params
        desde_str = request.GET.get("desde")
        hasta_str = request.GET.get("hasta")

        # 2) si no mandaron nada, usamos HOY como rango [00:00, 23:59:59]
        hoy = datetime.now()
        if not desde_str:
            desde_dt = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # parse YYYY-MM-DD
            desde_dt = datetime.strptime(desde_str, "%Y-%m-%d")
            desde_dt = desde_dt.replace(hour=0, minute=0, second=0, microsecond=0)

        if not hasta_str:
            hasta_dt = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            hasta_dt = datetime.strptime(hasta_str, "%Y-%m-%d")
            # hacemos hasta final del día indicado
            hasta_dt = hasta_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 3) asegurarnos que sean "aware" (timezone-aware)
        desde_dt = make_aware(desde_dt)
        hasta_dt = make_aware(hasta_dt)

        # 4) filtrar ventas confirmadas en ese rango
        ventas_qs = Venta.objects.filter(
            estado="confirmada",
            fecha__gte=desde_dt,
            fecha__lte=hasta_dt,
        )
        ventas_cant = ventas_qs.aggregate(c=Count("id"))["c"] or 0
        ventas_total = ventas_qs.aggregate(t=Sum("total"))["t"] or Decimal("0")

        # 5) filtrar compras confirmadas en ese rango
        compras_qs = Compra.objects.filter(
            estado="confirmada",
            fecha__gte=desde_dt,
            fecha__lte=hasta_dt,
        )
        compras_cant = compras_qs.aggregate(c=Count("id"))["c"] or 0
        compras_total = compras_qs.aggregate(t=Sum("total"))["t"] or Decimal("0")

        # 6) balance
        balance = ventas_total - compras_total

        # 7) armar respuesta
        data = {
            "periodo": {
                "desde": desde_dt.isoformat(),
                "hasta": hasta_dt.isoformat(),
            },
            "ventas": {
                "cantidad": str(ventas_cant),
                "total": str(ventas_total),
            },
            "compras": {
                "cantidad": str(compras_cant),
                "total": str(compras_total),
            },
            "balance": str(balance),
        }

        return Response(data)
