# reportes/serializers.py
from rest_framework import serializers


class ResumenFinancieroSerializer(serializers.Serializer):
    periodo = serializers.DictField(
        child=serializers.CharField(),
        help_text="Rango de fechas usado para el cálculo",
    )

    ventas = serializers.DictField(
        child=serializers.DecimalField(max_digits=14, decimal_places=2),
        help_text="Totales de ventas confirmadas",
    )

    compras = serializers.DictField(
        child=serializers.DecimalField(max_digits=14, decimal_places=2),
        help_text="Totales de compras confirmadas",
    )

    balance = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="ventas.total - compras.total",
    )
