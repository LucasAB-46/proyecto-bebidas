# tests/test_productos_validations.py
import pytest
from decimal import Decimal
from model_bakery import baker
from catalogo.models import Categoria, Producto
from catalogo.serializers import ProductoSerializer

pytestmark = pytest.mark.django_db

def test_producto_serializer_precio_venta_debe_ser_mayor_a_cero():
    categoria = baker.make(Categoria, nombre="Cervezas", local_id=1)
    data = {
        "codigo": "B001",
        "nombre": "Cerveza Rubia",
        "marca": "Andes",
        "precio_venta": Decimal("0.00"),  # inválido
        "stock_actual": Decimal("10"),
        "activo": True,
        "categoria": categoria.id,
    }
    s = ProductoSerializer(data=data)
    assert not s.is_valid()
    assert "precio_venta" in s.errors

def test_producto_serializer_stock_actual_no_puede_ser_negativo():
    categoria = baker.make(Categoria, nombre="Aguas", local_id=1)
    data = {
        "codigo": "AG001",
        "nombre": "Agua 500ml",
        "marca": "Glaciar",
        "precio_venta": Decimal("100.00"),
        "stock_actual": Decimal("-1"),  # inválido
        "activo": True,
        "categoria": categoria.id,
    }
    s = ProductoSerializer(data=data)
    assert not s.is_valid()
    assert "stock_actual" in s.errors

def test_producto_serializer_valido_ok():
    categoria = baker.make(Categoria, nombre="Gaseosas", local_id=1)
    data = {
        "codigo": "C001",
        "nombre": "Coca-Cola 500ml",
        "marca": "Coca Cola",
        "precio_venta": Decimal("1200.00"),
        "stock_actual": Decimal("50"),
        "activo": True,
        "categoria": categoria.id,
    }
    s = ProductoSerializer(data=data)
    assert s.is_valid(), s.errors
    instance = s.save(local_id=1)
    assert isinstance(instance, Producto)
    assert instance.local_id == 1
