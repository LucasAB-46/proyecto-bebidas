import json
import pytest
from typing import Any, Dict, List

API_BASE = "/api"         # Cambiá si usás otro prefijo (p.ej. "/v1")
CATALOGO = f"{API_BASE}/catalogo/productos/"
COMPRAS  = f"{API_BASE}/compras/"
VENTAS   = f"{API_BASE}/ventas/"

def _parse_json(resp) -> Any:
    """
    Intenta parsear JSON tanto con .json() como decodificando contenido crudo.
    Devuelve None si no es posible (útil para mensajes de error).
    """
    try:
        return resp.json()
    except Exception:
        try:
            return json.loads(resp.content.decode("utf-8"))
        except Exception:
            return None

# ------------------------------------------------------------------------------
# Smoke: Catálogo
# ------------------------------------------------------------------------------
@pytest.mark.smoke
def test_catalogo_productos_list_ok(auth_client):
    r = auth_client.get(CATALOGO)
    assert r.status_code == 200, f"Esperado 200, obtuve {r.status_code}. Body: {r.content[:500]}"
    data = _parse_json(r)
    # Soporta DRF paginado o lista simple
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    assert isinstance(items, list), "El endpoint de catálogo no devolvió una lista"
    if items:
        sample = items[0]
        for key in ("id", "nombre", "precio_venta"):
            assert key in sample, f"Falta clave '{key}' en producto: {sample}"

# ------------------------------------------------------------------------------
# Smoke: Compras
# ------------------------------------------------------------------------------
@pytest.mark.smoke
def test_compras_list_ok(auth_client):
    r = auth_client.get(COMPRAS)
    assert r.status_code == 200, f"Esperado 200 en compras list, obtuve {r.status_code}. Body: {r.content[:500]}"
    data = _parse_json(r)
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    assert isinstance(items, list), "El endpoint de compras no devolvió una lista"

@pytest.mark.smoke
def test_compras_confirmar_si_hay_borrador(auth_client):
    r = auth_client.get(COMPRAS)
    assert r.status_code == 200, f"Compras list falló ({r.status_code})"
    data = _parse_json(r)
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    if not isinstance(items, list):
        pytest.skip("Formato inesperado en compras list; se omite smoke de confirmación.")
    borradores = [c for c in items if isinstance(c, dict) and c.get("estado") == "borrador"]
    if not borradores:
        pytest.skip("No hay compras en estado 'borrador'; se omite confirmación en smoke.")
    compra_id = borradores[0]["id"]
    r2 = auth_client.post(f"{COMPRAS}{compra_id}/confirmar/")
    assert r2.status_code == 200, (
        f"Esperado 200 al confirmar compra {compra_id}, obtuve {r2.status_code}. Body: {r2.content[:500]}"
    )

# ------------------------------------------------------------------------------
# Smoke: Ventas
# ------------------------------------------------------------------------------
@pytest.mark.smoke
def test_ventas_list_ok(auth_client):
    r = auth_client.get(VENTAS)
    assert r.status_code == 200, f"Esperado 200 en ventas list, obtuve {r.status_code}. Body: {r.content[:500]}"
    data = _parse_json(r)
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    assert isinstance(items, list), "El endpoint de ventas no devolvió una lista"

@pytest.mark.smoke
def test_ventas_anular_si_hay_confirmada(auth_client):
    r = auth_client.get(VENTAS)
    assert r.status_code == 200, f"Ventas list falló ({r.status_code})"
    data = _parse_json(r)
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    if not isinstance(items, list):
        pytest.skip("Formato inesperado en ventas list; se omite smoke de anulación.")
    confirmadas = [v for v in items if isinstance(v, dict) and v.get("estado") == "confirmada"]
    if not confirmadas:
        pytest.skip("No hay ventas 'confirmada'; se omite anulación en smoke.")
    venta_id = confirmadas[0]["id"]
    r2 = auth_client.post(f"{VENTAS}{venta_id}/anular/")
    assert r2.status_code == 200, (
        f"Esperado 200 al anular venta {venta_id}, obtuve {r2.status_code}. Body: {r2.content[:500]}"
    )
