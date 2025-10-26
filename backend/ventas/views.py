# backend/ventas/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from catalogo.models import Producto
from .models import Venta
from .serializers import VentaWriteSerializer, VentaReadSerializer


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all().select_related("local", "usuario")
    serializer_class = VentaWriteSerializer

    def get_serializer_class(self):
        # Cuando pedimos data (GET list/retrieve) devolvemos el serializer de lectura.
        if self.action in ["list", "retrieve"]:
            return VentaReadSerializer
        # Cuando creamos/actualizamos usamos el serializer de escritura.
        return VentaWriteSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Por ahora local fijo = 1 y usuario null/anon
        data["local_id"] = 1

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        venta = serializer.save(local_id=1, usuario=request.user if request.user.is_authenticated else None)

        return Response(
            VentaReadSerializer(venta).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        venta = self.get_object()

        if venta.estado != "borrador":
            return Response(
                {"estado": "Sólo BORRADOR puede confirmarse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            venta.estado = "confirmada"
            venta.save(update_fields=["estado"])

            # bajar stock y registrar precio de venta
            for det in venta.detalles.select_related("producto").all():
                prod = det.producto
                # restar stock
                prod.stock_actual = (prod.stock_actual or 0) - det.cantidad
                # opcional: podríamos guardar último precio_venta
                prod.precio_venta = det.precio_unitario
                prod.save(update_fields=["stock_actual", "precio_venta"])

        return Response(VentaReadSerializer(venta).data)

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        venta = self.get_object()

        if venta.estado != "confirmada":
            return Response(
                {"estado": "Sólo CONFIRMADA puede anularse"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            venta.estado = "anulada"
            venta.save(update_fields=["estado"])

            # devolver stock
            for det in venta.detalles.select_related("producto").all():
                prod = det.producto
                prod.stock_actual = (prod.stock_actual or 0) + det.cantidad
                prod.save(update_fields=["stock_actual"])

        return Response(VentaReadSerializer(venta).data)
