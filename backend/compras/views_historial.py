from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Compra
from .serializers_historial import CompraListSerializer, CompraDetailSerializer


def _get_local_id(request):
    return request.headers.get("X-Local-ID") or request.META.get("HTTP_X_LOCAL_ID")


class CompraHistorialView(APIView):
    """
    GET /api/compras/historial/?desde=2025-01-01&hasta=2025-01-31&estado=confirmada
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        local_id = _get_local_id(request)
        qs = Compra.objects.all()

        if local_id:
            qs = qs.filter(local_id=local_id)

        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")

        if desde_str:
            dt_desde = make_aware(datetime.strptime(desde_str, "%Y-%m-%d"))
            qs = qs.filter(fecha__gte=dt_desde)

        if hasta_str:
            dt_hasta = datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)
            dt_hasta = make_aware(dt_hasta)
            qs = qs.filter(fecha__lt=dt_hasta)

        estado = request.query_params.get("estado")
        if estado and estado.lower() != "todos":
            qs = qs.filter(estado__iexact=estado.lower())

        qs = qs.order_by("-fecha")[:200]

        data = CompraListSerializer(qs, many=True).data
        return Response({"results": data})


class CompraDetalleView(APIView):
    """
    GET /api/compras/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        local_id = _get_local_id(request)

        compra_qs = Compra.objects.all()
        if local_id:
            compra_qs = compra_qs.filter(local_id=local_id)

        compra = compra_qs.prefetch_related("detalles__producto").get(pk=pk)

        data = CompraDetailSerializer(compra).data
        return Response(data)
