// src/pages/Productos.jsx

import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { listProducts, deleteProduct } from "../services/products";

export default function Productos() {
  const location = useLocation();
  const successMsg = location.state?.success;

  const [productos, setProductos] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);

  // cargar productos
  const fetchProductos = async (opts = {}) => {
    setLoading(true);
    setError("");

    try {
      const params = {
        search: opts.search ?? search,
        page: opts.page ?? page,
        ordering: "nombre",
        page_size: 25,
      };

      const resp = await listProducts(params);

      // DRF paginado: results y count
      setProductos(resp.data.results || []);
      setCount(resp.data.count || 0);
    } catch (err) {
      console.error("Error al cargar productos:", err);
      setError("No se pudieron cargar los productos.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProductos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const handleBuscar = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProductos({ page: 1, search });
  };

  const handleEliminar = async (id) => {
    if (!window.confirm("¿Seguro que desea eliminar este producto?")) return;
    try {
      await deleteProduct(id);
      fetchProductos();
    } catch (err) {
      console.error("Error al eliminar:", err);
      alert("No se pudo eliminar el producto.");
    }
  };

  const totalPaginas = Math.max(1, Math.ceil(count / 25));

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h4 m-0">Productos</h1>
        <Link to="/productos/nuevo" className="btn btn-primary">
          Crear Producto
        </Link>
      </div>

      {/* Mensaje de éxito después de venta o compra */}
      {successMsg && (
        <div className="alert alert-success">{successMsg}</div>
      )}

      {error && (
        <div className="alert alert-danger">{error}</div>
      )}

      <form className="row g-2 align-items-center mb-3" onSubmit={handleBuscar}>
        <div className="col-sm-10">
          <input
            className="form-control"
            placeholder="Buscar (código, nombre, marca, categoría)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="col-sm-2 d-grid">
          <button className="btn btn-outline-secondary" type="submit">
            Buscar
          </button>
        </div>
      </form>

      <div className="table-responsive">
        <table className="table align-middle">
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre ↑</th>
              <th>Categoría</th>
              <th>Marca</th>
              <th>Precio</th>
              <th>Stock</th>
              <th>Acciones</th>
            </tr>
          </thead>

          <tbody>
            {loading && (
              <tr>
                <td colSpan="7" className="text-center text-muted">
                  Cargando...
                </td>
              </tr>
            )}

            {!loading && productos.length === 0 && (
              <tr>
                <td colSpan="7" className="text-center text-muted">
                  Sin productos
                </td>
              </tr>
            )}

            {!loading &&
              productos.map((p) => (
                <tr key={p.id}>
                  <td>{p.codigo}</td>
                  <td>{p.nombre}</td>
                  <td>{p.categoria_nombre || p.categoria}</td>
                  <td>{p.marca}</td>
                  <td>${parseFloat(p.precio_venta).toFixed(2)}</td>
                  <td>{p.stock_actual}</td>
                  <td className="d-flex flex-wrap gap-2">
                    <Link
                      to={`/productos/${p.id}/editar`}
                      className="btn btn-sm btn-outline-secondary"
                    >
                      Editar
                    </Link>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => handleEliminar(p.id)}
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Paginación simple */}
      <div className="d-flex justify-content-end align-items-center gap-2">
        <button
          className="btn btn-outline-secondary btn-sm"
          disabled={page <= 1}
          onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
        >
          ← Anterior
        </button>

        <span className="text-muted">
          Página {page} / {totalPaginas}
        </span>

        <button
          className="btn btn-outline-secondary btn-sm"
          disabled={page >= totalPaginas}
          onClick={() =>
            setPage((prev) => Math.min(prev + 1, totalPaginas))
          }
        >
          Siguiente →
        </button>
      </div>

      <div className="mt-3 text-muted small">
        Total: {count}
      </div>
    </div>
  );
}
