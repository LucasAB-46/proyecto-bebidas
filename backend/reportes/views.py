from datetime import datetime
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
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # leer params
        desde_str = request.GET.get("desde")
        hasta_str = request.GET.get("hasta")

        # rango por defecto = hoy completo
        hoy = datetime.now()
        if not desde_str:
            desde_dt = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            desde_dt = datetime.strptime(desde_str, "%Y-%m-%d")
            desde_dt = desde_dt.replace(hour=0, minute=0, second=0, microsecond=0)

        if not hasta_str:
            hasta_dt = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            hasta_dt = datetime.strptime(hasta_str, "%Y-%m-%d")
            hasta_dt = hasta_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        # timezone aware
        desde_dt = make_aware(desde_dt)
        hasta_dt = make_aware(hasta_dt)

        # ventas confirmadas en rango
        ventas_qs = Venta.objects.filter(
            estado="confirmada",
            fecha__gte=desde_dt,
            fecha__lte=hasta_dt,
        )
        ventas_cant = ventas_qs.aggregate(c=Count("id"))["c"] or 0
        ventas_total = ventas_qs.aggregate(t=Sum("total"))["t"] or Decimal("0")

        # compras confirmadas en rango
        compras_qs = Compra.objects.filter(
            estado="confirmada",
            fecha__gte=desde_dt,
            fecha__lte=hasta_dt,
        )
        compras_cant = compras_qs.aggregate(c=Count("id"))["c"] or 0
        compras_total = compras_qs.aggregate(t=Sum("total"))["t"] or Decimal("0")

        # balance = ventas - compras
        balance = ventas_total - compras_total

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
