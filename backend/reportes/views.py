# reportes/views.py
from datetime import datetime, timedelta

from django.db.models import Sum, Q
from django.utils.timezone import make_aware
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from compras.models import Compra
from ventas.models import Venta
from .serializers import ResumenFinancieroSerializer


def _get_local_id_from_header(request):
    """
    Igual lógica que ya venimos usando:
    el front manda X-Local-ID (por ahora hardcode "1"),
    y el backend usa eso para filtrar datos por local.
    """
    raw = request.META.get("HTTP_X_LOCAL_ID") or request.headers.get("X-Local-ID")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


class ResumenFinancieroView(APIView):
    """
    GET /api/reportes/financieros/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD

    Devuelve:
    {
      "periodo": { "desde": "...", "hasta": "..." },
      "ventas": { "cantidad": 12, "total": 12345.67 },
      "compras": { "cantidad": 4, "total": 2345.00 },
      "balance": 9999.67
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # 1. leemos rango de fechas del querystring
        #    si no lo mandan, usamos "hoy"
        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")

        if desde_str:
            # interpretamos como fecha local YYYY-MM-DD a las 00:00
            desde_dt = datetime.strptime(desde_str, "%Y-%m-%d")
        else:
            # default: hoy
            hoy = datetime.utcnow().date()
            desde_dt = datetime.combine(hoy, datetime.min.time())

        if hasta_str:
            # hasta el final del día (23:59:59.999)
            hasta_base = datetime.strptime(hasta_str, "%Y-%m-%d")
        else:
            # default: mismo día que desde
            hasta_base = desde_dt

        hasta_dt = hasta_base + timedelta(days=1) - timedelta(microseconds=1)

        # pasamos a aware (timezone-aware) porque tus modelos usan DateTimeField con USE_TZ=True
        desde_dt = make_aware(desde_dt)
        hasta_dt = make_aware(hasta_dt)

        # 2. local_id desde header
        local_id = _get_local_id_from_header(request)

        # filtro base: confirmadas, en rango fecha, (y si hay local_id filtrar por local)
        venta_filters = Q(estado="confirmada", fecha__range=(desde_dt, hasta_dt))
        compra_filters = Q(estado="confirmada", fecha__range=(desde_dt, hasta_dt))

        if local_id is not None:
            venta_filters &= Q(local_id=local_id)
            compra_filters &= Q(local_id=local_id)

        # 3. agregados
        ventas_qs = Venta.objects.filter(venta_filters)
        compras_qs = Compra.objects.filter(compra_filters)

        ventas_total = ventas_qs.aggregate(s=Sum("total"))["s"] or 0
        ventas_cant = ventas_qs.count()

        compras_total = compras_qs.aggregate(s=Sum("total"))["s"] or 0
        compras_cant = compras_qs.count()

        balance_val = ventas_total - compras_total

        payload = {
            "periodo": {
                "desde": desde_dt.isoformat(),
                "hasta": hasta_dt.isoformat(),
            },
            "ventas": {
                "cantidad": ventas_cant,
                "total": round(ventas_total, 2),
            },
            "compras": {
                "cantidad": compras_cant,
                "total": round(compras_total, 2),
            },
            "balance": round(balance_val, 2),
        }

        # validamos contra el serializer por prolijidad
        serializer = ResumenFinancieroSerializer(payload)
        return Response(serializer.data)
