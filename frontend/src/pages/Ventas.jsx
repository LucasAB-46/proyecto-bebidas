// src/pages/Ventas.jsx
import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProducts } from '../services/products.js';
import { createSale, confirmSale, annulSale } from '../services/sales.js';

export default function Ventas() {
  const nav = useNavigate();

  // carrito y búsqueda
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);

  // estado de venta/errores
  const [processingSale, setProcessingSale] = useState(false);
  const [saleError, setSaleError] = useState(null);

  // última venta confirmada (para poder anular rápido)
  const [lastSale, setLastSale] = useState(null);

  // buscar productos (debounce 300ms)
  useEffect(() => {
    if (searchTerm.length < 3) {
      setSearchResults([]);
      return;
    }

    const t = setTimeout(async () => {
      setLoadingSearch(true);
      try {
        const resp = await listProducts({ search: searchTerm, page_size: 5 });
        setSearchResults(resp.data.results || []);
      } catch (err) {
        console.error("Error al buscar productos:", err);
      } finally {
        setLoadingSearch(false);
      }
    }, 300);

    return () => clearTimeout(t);
  }, [searchTerm]);

  // helpers carrito
  const addToCart = (product) => {
    setCart(prev => {
      const found = prev.find(i => i.id === product.id);
      if (found) {
        return prev.map(i =>
          i.id === product.id ? { ...i, cantidad: i.cantidad + 1 } : i
        );
      }
      return [...prev, { ...product, cantidad: 1 }];
    });
    setSearchTerm('');
    setSearchResults([]);
  };

  const updateQuantity = (id, nuevaCantidad) => {
    setCart(prev => {
      if (nuevaCantidad <= 0) {
        return prev.filter(i => i.id !== id);
      }
      return prev.map(i =>
        i.id === id ? { ...i, cantidad: nuevaCantidad } : i
      );
    });
  };

  // total calculado
  const totalVenta = useMemo(() => {
    return cart.reduce((total, item) => {
      const unit = parseFloat(item.precio_venta || 0);
      return total + unit * item.cantidad;
    }, 0);
  }, [cart]);

  // confirmar venta
  const handleConfirmSale = async () => {
    setProcessingSale(true);
    setSaleError(null);

    try {
      // armo los renglones para el backend
      const detalles = cart.map(item => ({
        producto: item.id,
        cantidad: item.cantidad,
        precio_unitario: item.precio_venta,
      }));

      // 1) crear venta en borrador
      const created = await createSale({ detalles });
      const saleId = created.data.id;

      // 2) confirmar
      const confirmed = await confirmSale(saleId);

      alert("¡Venta confirmada con éxito!");

      // guardo esa venta como "última"
      setLastSale({
        id: confirmed.data.id,
        estado: confirmed.data.estado,
        total: confirmed.data.total,
      });

      // limpio carrito
      setCart([]);

    } catch (err) {
      console.error("Error al confirmar la venta:", err);
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.estado ||
        "Ocurrió un error al procesar la venta.";
      setSaleError(msg);
    } finally {
      setProcessingSale(false);
    }
  };

  // anular última venta
  const handleAnnulLastSale = async () => {
    if (!lastSale || !lastSale.id) {
      alert("No hay venta reciente para anular.");
      return;
    }

    const ok = window.confirm(
      `¿Seguro que querés ANULAR la venta #${lastSale.id} por $${lastSale.total}?`
    );
    if (!ok) return;

    try {
      setProcessingSale(true);
      setSaleError(null);

      const annulResp = await annulSale(lastSale.id);

      alert(`Venta #${lastSale.id} anulada.`);

      // actualizo estado a ANULADA
      setLastSale(prev => ({
        ...prev,
        estado: annulResp.data.estado,
      }));
    } catch (err) {
      console.error("Error al anular la venta:", err);
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.estado ||
        "No se pudo anular la venta.";
      setSaleError(msg);
    } finally {
      setProcessingSale(false);
    }
  };

  return (
    <div className="container py-4">
      <div className="row g-5">
        {/* IZQUIERDA */}
        <div className="col-md-7">
          <h1 className="h4 mb-3">Punto de Venta</h1>

          {/* Buscar */}
          <div className="mb-3">
            <label htmlFor="search-product" className="form-label">
              Buscar Producto
            </label>
            <input
              type="text"
              id="search-product"
              className="form-control"
              placeholder="Escriba código o nombre..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {loadingSearch && (
              <div className="form-text">Buscando...</div>
            )}
          </div>

          {/* Resultados */}
          {searchResults.length > 0 && (
            <ul className="list-group mb-4">
              {searchResults.map(p => (
                <li
                  key={p.id}
                  className="list-group-item d-flex justify-content-between align-items-center"
                >
                  <div>
                    {p.nombre}{" "}
                    <span className="text-muted">
                      (${parseFloat(p.precio_venta).toFixed(2)})
                    </span>
                  </div>
                  <button
                    className="btn btn-sm btn-success"
                    onClick={() => addToCart(p)}
                  >
                    +
                  </button>
                </li>
              ))}
            </ul>
          )}

          {/* Carrito */}
          <h2 className="h5">Carrito</h2>
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th style={{ width: '120px' }}>Cantidad</th>
                  <th>Precio Unit.</th>
                  <th>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {cart.length === 0 && (
                  <tr>
                    <td colSpan="4" className="text-center text-muted">
                      El carrito está vacío
                    </td>
                  </tr>
                )}

                {cart.map(item => (
                  <tr key={item.id}>
                    <td>{item.nombre}</td>
                    <td>
                      <input
                        type="number"
                        className="form-control form-control-sm"
                        min="0"
                        value={item.cantidad}
                        onChange={(e) =>
                          updateQuantity(
                            item.id,
                            parseInt(e.target.value, 10)
                          )
                        }
                      />
                    </td>
                    <td>${parseFloat(item.precio_venta).toFixed(2)}</td>
                    <td>
                      $
                      {(parseFloat(item.precio_venta || 0) *
                        item.cantidad).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* DERECHA */}
        <div className="col-md-5">
          <div className="card shadow-sm">
            <div className="card-body">
              <h2 className="h5 card-title">Resumen de la Venta</h2>

              {/* mensaje error */}
              {saleError && (
                <div className="alert alert-danger">{saleError}</div>
              )}

              <div className="d-flex justify-content-between align-items-center my-4">
                <span className="h3">TOTAL</span>
                <span className="h3">${totalVenta.toFixed(2)}</span>
              </div>

              <div className="d-grid gap-2">
                <button
                  className="btn btn-primary btn-lg"
                  disabled={cart.length === 0 || processingSale}
                  onClick={handleConfirmSale}
                >
                  {processingSale ? "Procesando..." : "Confirmar Venta"}
                </button>

                <button
                  className="btn btn-outline-danger"
                  disabled={cart.length === 0 || processingSale}
                  onClick={() => setCart([])}
                >
                  Cancelar
                </button>

                {/* Info última venta + botón anular */}
                {lastSale && (
                  <div className="alert alert-secondary small mb-0">
                    <div>
                      Última venta: #{lastSale.id} – Estado:{" "}
                      <strong>{lastSale.estado}</strong>
                    </div>
                    <div>
                      Total: $
                      {parseFloat(lastSale.total || 0).toFixed(2)}
                    </div>

                    <button
                      className="btn btn-warning btn-sm mt-2"
                      disabled={
                        processingSale ||
                        lastSale.estado === "ANULADA"
                      }
                      onClick={handleAnnulLastSale}
                    >
                      {lastSale.estado === "ANULADA"
                        ? "Ya anulada"
                        : "Anular Última Venta"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="text-center mt-3">
            <button
              className="btn btn-link text-muted"
              onClick={() => nav("/productos")}
            >
              ↩ Ir a Productos
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
