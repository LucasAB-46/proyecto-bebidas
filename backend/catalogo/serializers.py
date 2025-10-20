# catalogo/serializers.py
from rest_framework import serializers
from .models import Categoria, Producto, Cliente, Proveedor, PrecioHistorico

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre"]  # local lo setea el servidor
        read_only_fields = ["id"]

class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True, default=None)

    class Meta:
        model = Producto
        fields = [
            "id", "codigo", "nombre", "marca", "precio_venta", "stock_actual",
            "activo", "categoria", "categoria_nombre", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "categoria": {"write_only": True, "required": False, "allow_null": True},
        }

    def validate(self, attrs):
        if "precio_venta" in attrs and attrs["precio_venta"] <= 0:
            raise serializers.ValidationError({"precio_venta": "Debe ser > 0"})
        if "stock_actual" in attrs and attrs["stock_actual"] < 0:
            raise serializers.ValidationError({"stock_actual": "No puede ser negativo"})
        return attrs

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ["id", "nombre", "cuit", "email", "telefono", "direccion", "activo", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

class PrecioHistoricoSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source="producto.codigo", read_only=True)
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)

    class Meta:
        model = PrecioHistorico
        fields = (
            "id", "producto", "producto_codigo", "fecha",
            "costo_unitario", "proveedor", "proveedor_nombre", "moneda"
        )
        read_only_fields = ("id", "fecha")
