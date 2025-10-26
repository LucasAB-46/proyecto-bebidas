from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Venta
from .serializers_historial import VentaListSerializer, VentaDetailSerializer


def _get_local_id(request):
    # mismo concepto que venimos usando
    return request.headers.get("X-Local-ID") or request.META.get("HTTP_X_LOCAL_ID")


class VentaHistorialView(APIView):
    """
    GET /api/ventas/historial/?desde=2025-01-01&hasta=2025-01-31&estado=confirmada
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        local_id = _get_local_id(request)
        qs = Venta.objects.all()

        if local_id:
            qs = qs.filter(local_id=local_id)

        # filtros fecha
        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")

        if desde_str:
            # interpretamos como yyyy-mm-dd 00:00
            dt_desde = make_aware(datetime.strptime(desde_str, "%Y-%m-%d"))
            qs = qs.filter(fecha__gte=dt_desde)

        if hasta_str:
            # interpretamos inclusive el día completo (23:59:59)
            dt_hasta = datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)
            dt_hasta = make_aware(dt_hasta)
            qs = qs.filter(fecha__lt=dt_hasta)

        estado = request.query_params.get("estado")
        if estado and estado.lower() != "todos":
            qs = qs.filter(estado__iexact=estado.lower())

        qs = qs.order_by("-fecha")[:200]  # cap de seguridad

        data = VentaListSerializer(qs, many=True).data
        return Response({"results": data})


class VentaDetalleView(APIView):
    """
    GET /api/ventas/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        local_id = _get_local_id(request)

        venta_qs = Venta.objects.all()
        if local_id:
            venta_qs = venta_qs.filter(local_id=local_id)

        venta = venta_qs.prefetch_related("detalles__producto").get(pk=pk)

        data = VentaDetailSerializer(venta).data
        return Response(data)
