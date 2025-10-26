from rest_framework import serializers
from .models import Compra, CompraDetalle


class CompraDetalleInlineSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = CompraDetalle
        fields = (
            "renglon",
            "producto",
            "producto_nombre",
            "cantidad",
            "costo_unitario",
            "bonif",
            "impuestos",
            "total_renglon",
        )


class CompraListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compra
        fields = (
            "id",
            "fecha",
            "estado",
            "total",
        )


class CompraDetailSerializer(serializers.ModelSerializer):
    detalles = CompraDetalleInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
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
