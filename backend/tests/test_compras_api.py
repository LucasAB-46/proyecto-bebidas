# tests/test_compras_api.py
import pytest
from model_bakery import baker
from compras.models import Compra
from catalogo.models import Proveedor

pytestmark = pytest.mark.django_db

BASE = "/api/compras/"  # ¡con barra final, evita 301!


def test_listado_compras_filtra_por_local(auth_client):
    # Proveedores por local
    prov_l1 = baker.make(Proveedor, local_id=1, nombre="Prov L1", activo=True)
    prov_l2 = baker.make(Proveedor, local_id=2, nombre="Prov L2", activo=True)

    # Compras en distintos locales
    c1 = baker.make(
        Compra, local_id=1, proveedor=prov_l1, estado="borrador",
        subtotal="1000.00", impuestos="0.00", bonificaciones="0.00", total="1000.00"
    )
    baker.make(
        Compra, local_id=2, proveedor=prov_l2, estado="confirmada",
        subtotal="2000.00", impuestos="0.00", bonificaciones="0.00", total="2000.00"
    )

    r = auth_client.get(BASE)
    assert r.status_code == 200, r.content
    ids = {item["id"] for item in r.json()["results"]}
    assert c1.id in ids
    # La del local 2 NO debería aparecer
    assert len(ids) == 1


def test_retrieve_compra_del_mismo_local(auth_client):
    prov = baker.make(Proveedor, local_id=1, nombre="Prov L1", activo=True)
    c = baker.make(
        Compra, local_id=1, proveedor=prov, estado="borrador",
        subtotal="500.00", impuestos="0.00", bonificaciones="0.00", total="500.00"
    )

    r = auth_client.get(f"{BASE}{c.id}/")
    assert r.status_code == 200, r.content
    data = r.json()
    assert data["id"] == c.id
    assert data["local_id"] == 1
