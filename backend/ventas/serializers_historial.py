from rest_framework import serializers
from .models import Venta, VentaDetalle
from catalogo.models import Producto


class VentaDetalleInlineSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = VentaDetalle
        fields = (
            "renglon",
            "producto",
            "producto_nombre",
            "cantidad",
            "precio_unitario",
            "bonif",
            "impuestos",
            "total_renglon",
        )


class VentaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = (
            "id",
            "fecha",
            "estado",
            "total",
        )


class VentaDetailSerializer(serializers.ModelSerializer):
    detalles = VentaDetalleInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = (
            "id",
            "fecha",
            "estado",
            "subtotal",
            "impuestos",
            "bonificaciones",
            "total",
            "detalles",
        )
