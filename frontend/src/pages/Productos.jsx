// src/pages/Productos.jsx

import { useEffect, useMemo, useState } from "react";
// --- ¡IMPORTACIÓN CORREGIDA Y VERIFICADA! ---
import { Link, useSearchParams, useLocation } from "react-router-dom";
import { listProducts, deleteProduct } from "../services/products";
import { useAuth } from "../context/AuthContext";

const headers = [
  { key: "codigo",       label: "Código" },
  { key: "nombre",       label: "Nombre" },
  { key: "categoria_nombre", label: "Categoría" },
  { key: "marca",        label: "Marca" },
  { key: "precio_venta", label: "Precio" },
  { key: "stock_actual", label: "Stock" },
  { key: "acciones",     label: "Acciones", sortable: false },
];

export default function Productos() {
  const { isAdmin } = useAuth();
  const [sp, setSp] = useSearchParams();
  const location = useLocation();
  const [data, setData] = useState({ results: [], count: 0, next: null, previous: null });
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState(null);

  const search    = sp.get("search")   ?? "";
  const page      = parseInt(sp.get("page") ?? "1", 10);
  const ordering  = sp.get("ordering") ?? "nombre";

  useEffect(() => {
    if (location.state?.success && !msg) {
      setMsg({ type: "success", text: location.state.success });
      window.history.replaceState({}, document.title);
    }

    let alive = true;
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await listProducts({ search, page, ordering });
        if (alive) {
          setData(res.data);
          if (msg?.type === 'danger') setMsg(null);
        }
      } catch (e) {
        console.error("Error cargando productos:", e);
        const detail = e?.response?.data?.detail || e?.message || "Error cargando productos";
        if (alive) setMsg({ type: "danger", text: String(detail) });
      } finally {
        if (alive) setLoading(false);
      }
    };

    fetchData();
    return () => { alive = false; };
  }, [search, page, ordering, location.state]); // Añadido location.state para refrescar en navegación

  const handleDelete = async (productId) => {
    if (window.confirm("¿Estás seguro de que quieres eliminar este producto?")) {
      try {
        await deleteProduct(productId);
        // Refrescamos la data para asegurar consistencia
        const res = await listProducts({ search, page, ordering });
        setData(res.data);
        setMsg({ type: "success", text: "Producto eliminado con éxito." });
      } catch (e) {
        console.error("Error eliminando producto:", e);
        setMsg({ type: "danger", text: "Error al eliminar el producto." });
      }
    }
  };

  const pageSize   = 25;
  const totalPages = useMemo(
    () => (data ? Math.max(1, Math.ceil(data.count / pageSize)) : 1),
    [data]
  );

  const onSubmit = (e) => {
    e.preventDefault();
    const q = new FormData(e.currentTarget).get("q") || "";
    setSp({ search: q, page: "1", ordering });
  };

  const toggleOrdering = (key, sortable = true) => {
    if (!sortable) return;
    const next = ordering === `-${key}` ? key : `-${key}`;
    setSp({ search, page: "1", ordering: next });
  };

  if (loading) {
    return (
      <div className="container py-3">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-3">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h4 mb-0">Productos</h1>
        {isAdmin && (
          <Link to="/productos/nuevo" className="btn btn-primary">
            Crear Producto
          </Link>
        )}
      </div>

      {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

      <form className="input-group mb-3" onSubmit={onSubmit}>
        <input
          name="q"
          className="form-control"
          placeholder="Buscar (código, nombre, marca, categoría)…"
          defaultValue={search}
        />
        <button className="btn btn-outline-secondary">Buscar</button>
      </form>

      <div className="table-responsive">
        <table className="table table-sm align-middle">
          <thead>
            <tr>
              {headers.map(h => (
                <th key={h.key} role="button" onClick={() => toggleOrdering(h.key, h.sortable !== false)}>
                  {h.label}{" "}
                  {ordering.replace("-", "") === h.key ? (ordering.startsWith("-") ? "↓" : "↑") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.results?.length === 0 && (
              <tr><td colSpan={headers.length} className="text-muted">Sin productos</td></tr>
            )}
            {data.results?.map(p => (
              <tr key={p.id}>
                <td>{p.codigo}</td>
                <td>{p.nombre}</td>
                <td>{p.categoria_nombre || "-"}</td>
                <td>{p.marca || "-"}</td>
                <td>${parseFloat(p.precio_venta).toFixed(2)}</td>
                <td>{parseInt(p.stock_actual)}</td>
                <td>
                  <div className="btn-group">
                    {isAdmin && (
                      <>
                        <Link to={`/productos/${p.id}/editar`} className="btn btn-outline-secondary btn-sm">
                          Editar
                        </Link>
                        <button onClick={() => handleDelete(p.id)} className="btn btn-outline-danger btn-sm">
                          Eliminar
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="d-flex justify-content-between align-items-center">
        <small className="text-muted">Total: {data.count}</small>
        <div className="btn-group">
          <button
            className="btn btn-outline-secondary btn-sm"
            disabled={!data.previous || page <= 1}
            onClick={() => setSp({ search, ordering, page: String(page - 1) })}
          >
            ← Anterior
          </button>
          <span className="btn btn-outline-secondary btn-sm disabled">
            Página {page} / {totalPages}
          </span>
          <button
            className="btn btn-outline-secondary btn-sm"
            disabled={!data.next || page >= totalPages}
            onClick={() => setSp({ search, ordering, page: String(page + 1) })}
          >
            Siguiente →
          </button>
        </div>
      </div>
    </div>
  );
}