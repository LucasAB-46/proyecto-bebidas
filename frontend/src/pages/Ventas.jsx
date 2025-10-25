// src/pages/Ventas.jsx

import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProducts } from '../services/products';
import { createSale, confirmSale } from '../services/sales';

export default function Ventas() {
  const nav = useNavigate();

  // --- ESTADOS ---
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);

  const [processingSale, setProcessingSale] = useState(false);
  const [saleError, setSaleError] = useState(null);

  // --- BUSCADOR DE PRODUCTOS (con debounce) ---
  useEffect(() => {
    if (searchTerm.length < 3) {
      setSearchResults([]);
      return;
    }

    const debounceTimeout = setTimeout(async () => {
      setLoadingSearch(true);
      try {
        const response = await listProducts({
          search: searchTerm,
          page_size: 5,
        });
        setSearchResults(response.data.results);
      } catch (error) {
        console.error("Error al buscar productos:", error);
      } finally {
        setLoadingSearch(false);
      }
    }, 300);

    return () => clearTimeout(debounceTimeout);
  }, [searchTerm]);

  // --- CARRITO ---
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
        return [...currentCart, { ...product, cantidad: 1 }];
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
    return cart.reduce(
      (total, item) => total + (item.precio_venta * item.cantidad),
      0
    );
  }, [cart]);

  // --- CONFIRMAR VENTA ---
  const handleConfirmSale = async () => {
    setProcessingSale(true);
    setSaleError(null);

    try {
      // Paso 1: armar detalles como los espera el backend
      const saleDetails = cart.map(item => ({
        producto: item.id,
        cantidad: item.cantidad,
        precio_unitario: item.precio_venta,
      }));

      const payload = {
        detalles: saleDetails,
      };

      // Paso 2: crear venta en estado BORRADOR
      const createdSaleResponse = await createSale(payload);
      const saleId = createdSaleResponse.data.id;

      // Paso 3: confirmar venta en backend (esto descuenta stock)
      await confirmSale(saleId);

      // Paso 4: limpiar UI
      setCart([]);

      // Paso 5: mandar al listado de productos para ver stock actualizado
      nav("/productos", {
        replace: true,
        state: { success: "Venta confirmada con éxito." },
      });

    } catch (error) {
      console.error("Error al confirmar la venta:", error);
      const errorMessage =
        error.response?.data?.detail ||
        JSON.stringify(error.response?.data) ||
        error.message ||
        "Ocurrió un error al procesar la venta.";
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
                          updateQuantity(
                            item.id,
                            parseInt(e.target.value, 10)
                          )
                        }
                      />
                    </td>
                    <td>${parseFloat(item.precio_venta).toFixed(2)}</td>
                    <td>${(item.precio_venta * item.cantidad).toFixed(2)}</td>
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

              {saleError && (
                <div className="alert alert-danger">
                  {saleError}
                </div>
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
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
