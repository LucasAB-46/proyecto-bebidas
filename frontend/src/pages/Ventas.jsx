// src/pages/Ventas.jsx

import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProducts } from '../services/products';
import { createSale, confirmSale, annulSale } from '../services/sales';

export default function Ventas() {
  const nav = useNavigate();

  // --- ESTADOS DE LA VENTA ACTUAL ---
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);

  const [processingSale, setProcessingSale] = useState(false);
  const [saleError, setSaleError] = useState(null);

  // Guardamos info de la última venta procesada para permitir "Anular"
  // Estructura que vamos a guardar:
  // { id, estado, total }
  const [lastSale, setLastSale] = useState(null);

  // ---------------- BUSCADOR PRODUCTOS ----------------
  useEffect(() => {
    if (searchTerm.length < 3) {
      setSearchResults([]);
      return;
    }
    const debounceTimeout = setTimeout(async () => {
      setLoadingSearch(true);
      try {
        const response = await listProducts({ search: searchTerm, page_size: 5 });
        setSearchResults(response.data.results);
      } catch (error) {
        console.error("Error al buscar productos:", error);
      } finally {
        setLoadingSearch(false);
      }
    }, 300);
    return () => clearTimeout(debounceTimeout);
  }, [searchTerm]);

  // ---------------- CARRITO ----------------
  const addToCart = (product) => {
    setCart(currentCart => {
      const existingProduct = currentCart.find(item => item.id === product.id);
      if (existingProduct) {
        return currentCart.map(item =>
          item.id === product.id
            ? { ...item, cantidad: item.cantidad + 1 }
            : item
        );
      } else {
        return [
          ...currentCart,
          { ...product, cantidad: 1 }
        ];
      }
    });
    setSearchTerm('');
    setSearchResults([]);
  };

  const updateQuantity = (productId, newQuantity) => {
    setCart(currentCart => {
      if (newQuantity <= 0) {
        return currentCart.filter(item => item.id !== productId);
      }
      return currentCart.map(item =>
        item.id === productId
          ? { ...item, cantidad: newQuantity }
          : item
      );
    });
  };

  const totalVenta = useMemo(() => {
    return cart.reduce((total, item) => {
      const unit = parseFloat(item.precio_venta || 0);
      return total + unit * item.cantidad;
    }, 0);
  }, [cart]);

  // ---------------- CONFIRMAR VENTA ----------------
  const handleConfirmSale = async () => {
    setProcessingSale(true);
    setSaleError(null);

    try {
      // 1) armar payload para crear venta (BORRADOR)
      const saleDetails = cart.map(item => ({
        producto: item.id,
        cantidad: item.cantidad,
        precio_unitario: item.precio_venta,
      }));

      const payload = {
        detalles: saleDetails,
      };

      // 2) crear venta
      const createdSaleResponse = await createSale(payload);
      const saleId = createdSaleResponse.data.id;

      // 3) confirmar venta
      const confirmedSaleResponse = await confirmSale(saleId);

      // respuesta confirmada
      const confirmedData = confirmedSaleResponse.data;

      // 4) éxito
      alert("¡Venta confirmada con éxito!");

      // guardamos la venta confirmada para poder anularla
      setLastSale({
        id: confirmedData.id,
        estado: confirmedData.estado,
        total: confirmedData.total,
      });

      // limpiamos el carrito
      setCart([]);

    } catch (error) {
      console.error("Error al confirmar la venta:", error);
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.estado ||
        "Ocurrió un error al procesar la venta.";
      setSaleError(errorMessage);
    } finally {
      setProcessingSale(false);
    }
  };

  // ---------------- ANULAR ÚLTIMA VENTA ----------------
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

      // update estado en memoria
      setLastSale({
        ...lastSale,
        estado: annulResp.data.estado,
      });
    } catch (error) {
      console.error("Error al anular la venta:", error);
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.estado ||
        "No se pudo anular la venta.";
      setSaleError(errorMessage);
    } finally {
      setProcessingSale(false);
    }
  };

  return (
    <div className="container py-4">
      <div className="row g-5">
        {/* Columna Izquierda: Búsqueda y Carrito */}
        <div className="col-md-7">
          <h1 className="h4 mb-3">Punto de Venta</h1>

          {/* Buscar Producto */}
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
            {loadingSearch && <div className="form-text">Buscando...</div>}
          </div>

          {/* Resultados búsqueda */}
          {searchResults.length > 0 && (
            <ul className="list-group mb-4">
              {searchResults.map(product => (
                <li
                  key={product.id}
                  className="list-group-item d-flex justify-content-between align-items-center"
                >
                  <div>
                    {product.nombre}{" "}
                    <span className="text-muted">
                      (${parseFloat(product.precio_venta).toFixed(2)})
                    </span>
                  </div>
                  <button
                    className="btn btn-sm btn-success"
                    onClick={() => addToCart(product)}
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
                        value={item.cantidad}
                        min="0"
                        onChange={(e) =>
                          updateQuantity(item.id, parseInt(e.target.value, 10))
                        }
                      />
                    </td>
                    <td>${parseFloat(item.precio_venta).toFixed(2)}</td>
                    <td>
                      $
                      {(parseFloat(item.precio_venta || 0) * item.cantidad)
                        .toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Columna Derecha: Resumen y Acciones */}
        <div className="col-md-5">
          <div className="card shadow-sm">
            <div className="card-body">
              <h2 className="h5 card-title">Resumen de la Venta</h2>

              {/* Error visible */}
              {saleError && (
                <div className="alert alert-danger">{saleError}</div>
              )}

              <div className="d-flex justify-content-between align-items-center my-4">
                <span className="h3">TOTAL</span>
                <span className="h3">${totalVenta.toFixed(2)}</span>
              </div>

              <div className="d-grid gap-2">
                {/* Confirmar Venta */}
                <button
                  className="btn btn-primary btn-lg"
                  disabled={cart.length === 0 || processingSale}
                  onClick={handleConfirmSale}
                >
                  {processingSale ? "Procesando..." : "Confirmar Venta"}
                </button>

                {/* Limpiar carrito */}
                <button
                  className="btn btn-outline-danger"
                  disabled={cart.length === 0 || processingSale}
                  onClick={() => setCart([])}
                >
                  Cancelar
                </button>

                {/* Datos venta última operación */}
                {lastSale && (
                  <div className="alert alert-secondary small mb-0">
                    <div>
                      Última venta: #{lastSale.id} – Estado:{" "}
                      <strong>{lastSale.estado}</strong>
                    </div>
                    <div>Total: ${parseFloat(lastSale.total || 0).toFixed(2)}</div>

                    {/* Botón Anular */}
                    <button
                      className="btn btn-warning btn-sm mt-2"
                      disabled={
                        processingSale || lastSale.estado === "ANULADA"
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

          {/* Botón para volver a productos, por si querés ajustar precios rápido */}
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
