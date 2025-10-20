# tests/test_proveedores_api.py
import pytest
from model_bakery import baker
from catalogo.models import Proveedor

pytestmark = pytest.mark.django_db

BASE = "/api/catalogo/proveedores/"


def test_crear_proveedor_201(auth_client):
    data = {
        "nombre": "Distribuidora Norte",
        "cuit": "30-12345678-9",
        "email": "ventas@norte.com",
        "telefono": "1122334455",
        "direccion": "Av. Siempreviva 123",
        "activo": True,
    }
    r = auth_client.post(BASE, data=data, format="json")
    assert r.status_code == 201, r.content
    prov = Proveedor.objects.get(id=r.json()["id"])
    assert prov.local_id == 1


def test_listado_filtra_por_local(auth_client):
    p1 = baker.make(Proveedor, local_id=1, nombre="Local1 Prov", activo=True)
    baker.make(Proveedor, local_id=2, nombre="Local2 Prov", activo=True)

    r = auth_client.get(BASE)
    assert r.status_code == 200, r.content
    nombres = {item["nombre"] for item in r.json()["results"]}
    assert "Local1 Prov" in nombres
    assert "Local2 Prov" not in nombres


def test_patch_proveedor_ok(auth_client):
    p = baker.make(Proveedor, local_id=1, nombre="Viejo", activo=True)
    r = auth_client.patch(f"{BASE}{p.id}/", data={"nombre": "Nuevo"}, format="json")
    assert r.status_code == 200, r.content
    p.refresh_from_db()
    assert p.nombre == "Nuevo"
