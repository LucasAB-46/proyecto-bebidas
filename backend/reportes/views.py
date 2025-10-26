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


class ResumenDiaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Devuelve el resumen financiero-operativo del día actual
        para el local mandado en X-Local-ID.
        """
        # 1. Determinar el local actual
        #    Lo mismo que hacés en el resto del backend: usamos el header X-Local-ID
        local_id = request.headers.get("X-Local-ID")
        if not local_id:
            return Response(
                {"detail": "Falta header X-Local-ID"},
                status=400,
            )

        # 2. Rango de hoy (zona horaria del server)
        ahora = timezone.localtime()
        inicio_hoy = timezone.make_aware(
            datetime.combine(ahora.date(), time.min),
            timezone.get_current_timezone(),
        )
        fin_hoy = timezone.make_aware(
            datetime.combine(ahora.date(), time.max),
            timezone.get_current_timezone(),
        )

        # 3. Ventas confirmadas hoy en este local
        ventas_qs = (
            Venta.objects.filter(
                local_id=local_id,
                estado__iexact="confirmada",
                fecha__gte=inicio_hoy,
                fecha__lte=fin_hoy,
            )
        )

        ventas_aggr = ventas_qs.aggregate(
            cantidad=Count("id"),
            total=Sum("total"),
        )
        ventas_cantidad = ventas_aggr["cantidad"] or 0
        ventas_total = ventas_aggr["total"] or Decimal("0.00")

        # última venta confirmada (hoy) para mostrar en dashboard
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

        # 4. Compras confirmadas hoy en este local
        compras_qs = (
            Compra.objects.filter(
                local_id=local_id,
                estado__iexact="confirmada",
                fecha__gte=inicio_hoy,
                fecha__lte=fin_hoy,
            )
        )

        compras_aggr = compras_qs.aggregate(
            cantidad=Count("id"),
            total=Sum("total"),
        )
        compras_cantidad = compras_aggr["cantidad"] or 0
        compras_total = compras_aggr["total"] or Decimal("0.00")

        # última compra confirmada (hoy)
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

        # 5. Balance (ventas - compras)
        balance_decimal = ventas_total - compras_total

        # 6. Stock bajo: productos del local con stock <= 5 (ajustá si querés)
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

        # 7. Respuesta final con el contrato esperado por el frontend
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
