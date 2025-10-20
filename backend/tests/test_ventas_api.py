# tests/test_ventas_api.py
import pytest
from model_bakery import baker
from ventas.models import Venta

pytestmark = pytest.mark.django_db

BASE = "/api/ventas/"  # ¡con barra final, evita 301!


def test_listado_ventas_filtra_por_local(auth_client):
    v1 = baker.make(
        Venta, local_id=1, estado="borrador",
        subtotal="800.00", impuestos="0.00", bonificaciones="0.00", total="800.00"
    )
    baker.make(
        Venta, local_id=2, estado="confirmada",
        subtotal="1200.00", impuestos="0.00", bonificaciones="0.00", total="1200.00"
    )

    r = auth_client.get(BASE)
    assert r.status_code == 200, r.content
    ids = {item["id"] for item in r.json()["results"]}
    assert v1.id in ids
    assert len(ids) == 1


def test_retrieve_venta_del_mismo_local(auth_client):
    v = baker.make(
        Venta, local_id=1, estado="borrador",
        subtotal="300.00", impuestos="0.00", bonificaciones="0.00", total="300.00"
    )

    r = auth_client.get(f"{BASE}{v.id}/")
    assert r.status_code == 200, r.content
    data = r.json()
    assert data["id"] == v.id
    assert data["local_id"] == 1
