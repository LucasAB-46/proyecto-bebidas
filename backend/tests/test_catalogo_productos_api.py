# tests/test_catalogo_productos_api.py
import pytest
from decimal import Decimal
from model_bakery import baker
from catalogo.models import Categoria, Producto

pytestmark = pytest.mark.django_db

CATALOGO_BASE = "/api/catalogo"
PROD_URL = f"{CATALOGO_BASE}/productos/"
CAT_URL = f"{CATALOGO_BASE}/categorias/"


def test_crear_producto_201(auth_client):
    categoria = baker.make(Categoria, nombre="Cervezas", local_id=1)

    payload = {
        "codigo": "B710",
        "nombre": "Cerveza Rubia 710",
        "marca": "Corona",
        "precio_venta": "4500.00",
        "stock_actual": "25",
        "activo": True,
        "categoria": categoria.id,
    }

    r = auth_client.post(PROD_URL, data=payload, format="json")
    assert r.status_code == 201, r.content
    data = r.json()
    assert data["codigo"] == payload["codigo"]
    assert Producto.objects.filter(id=data["id"], local_id=1).exists()


def test_listar_productos_filtra_por_local(auth_client):
    categoria_l1 = baker.make(Categoria, nombre="Vinos", local_id=1)
    categoria_l2 = baker.make(Categoria, nombre="Aperitivos", local_id=2)

    p1 = baker.make(
        Producto,
        local_id=1,
        categoria=categoria_l1,
        codigo="MALB001",
        nombre="Vino Malbec",
        marca="Trapiche",
        precio_venta=Decimal("4600.00"),
        stock_actual=Decimal("10"),
        activo=True,
    )
    baker.make(
        Producto,
        local_id=2,
        categoria=categoria_l2,
        codigo="FER001",
        nombre="Fernet",
        marca="Branca",
        precio_venta=Decimal("5500.00"),
        stock_actual=Decimal("5"),
        activo=True,
    )

    r = auth_client.get(PROD_URL)
    assert r.status_code == 200, r.content
    items = r.json()["results"]
    ids = {item["id"] for item in items}
    assert p1.id in ids
    assert not any(item["codigo"] == "FER001" for item in items)


def test_validaciones_de_negocio_400(auth_client):
    categoria = baker.make(Categoria, nombre="Aguas", local_id=1)

    payload_bad_price = {
        "codigo": "AG001",
        "nombre": "Agua 500",
        "marca": "Glaciar",
        "precio_venta": "0.00",
        "stock_actual": "10",
        "activo": True,
        "categoria": categoria.id,
    }
    r1 = auth_client.post(PROD_URL, data=payload_bad_price, format="json")
    assert r1.status_code == 400
    assert "precio_venta" in r1.json()

    payload_bad_stock = {
        "codigo": "AG002",
        "nombre": "Agua 2L",
        "marca": "Glaciar",
        "precio_venta": "1500.00",
        "stock_actual": "-1",
        "activo": True,
        "categoria": categoria.id,
    }
    r2 = auth_client.post(PROD_URL, data=payload_bad_stock, format="json")
    assert r2.status_code == 400
    assert "stock_actual" in r2.json()


def test_patch_producto_ok_y_no_cambia_local(auth_client):
    categoria = baker.make(Categoria, nombre="Gaseosas", local_id=1)
    p = baker.make(
        Producto,
        local_id=1,
        categoria=categoria,
        codigo="C001",
        nombre="Coca-Cola 500ml",
        marca="Coca Cola",
        precio_venta=Decimal("1400.00"),
        stock_actual=Decimal("20"),
        activo=True,
    )

    patch_data = {"precio_venta": "1600.00", "stock_actual": "25", "local_id": 999}
    r = auth_client.patch(f"{PROD_URL}{p.id}/", data=patch_data, format="json")
    assert r.status_code == 200, r.content

    p.refresh_from_db()
    assert p.precio_venta == Decimal("1600.00")
    assert p.stock_actual == Decimal("25")
    assert p.local_id == 1
