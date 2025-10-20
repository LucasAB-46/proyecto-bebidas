# ventas/serializers.py
from rest_framework import serializers
from .models import Venta

class VentaReadSerializer(serializers.ModelSerializer):
    # Exponer el FK como entero en la salida
    local_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Venta
        fields = "__all__"

class VentaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = "__all__"
        # El local lo seteamos desde la vista con el header, que sea de solo lectura
        extra_kwargs = {
            "local": {"read_only": True},
        }
