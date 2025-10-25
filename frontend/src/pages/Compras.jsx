// src/pages/Compras.jsx

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { listProducts, listSuppliers } from '../services/products';
import { createPurchase, confirmPurchase } from '../services/purchases';

export default function Compras() {
  const nav = useNavigate();

  // --- ESTADOS ---
  const [suppliers, setSuppliers] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState('');
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [error, setError] = useState(null);
  const [processingPurchase, setProcessingPurchase] = useState(false);

  // --- CARGA DE PROVEEDORES ---
  useEffect(() => {
    const fetchSuppliers = async () => {
      try {
        const response = await listSuppliers();
        setSuppliers(response.data.results || response.data);
      } catch (err) {
        console.error("Error al cargar proveedores:", err);
        setError("No se pudieron cargar los proveedores.");
      }
    };
    fetchSuppliers();
  }, []);

  // --- BUSCADOR DE PRODUCTOS ---
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

  // --- CARRITO ---
  const addToCart = (product) => {
    setCart(currentCart => {
      const existing = currentCart.find(item => item.id === product.id);
      if (existing) {
        return currentCart.map(item =>
          item.id === product.id
            ? { ...item, cantidad: item.cantidad + 1 }
            : item
        );
      } else {
        return [...currentCart, { ...product, cantidad: 1, costo_unitario: 0 }];
      }
    });
    setSearchTerm('');
    setSearchResults([]);
  };

  const updateCartItem = (productId, field, value) => {
    setCart(currentCart => {
      const safeValue = value === '' ? 0 : Number(value);
      const newCart = currentCart.map(item =>
        item.id === productId
          ? { ...item, [field]: isNaN(safeValue) ? 0 : safeValue }
          : item
      );
      return newCart;
    });
  };

  const totalCompra = useMemo(() => {
    return cart.reduce(
      (total, item) => total + ((item.costo_unitario || 0) * (item.cantidad || 0)),
      0
    );
  }, [cart]);

  // --- CONFIRMAR COMPRA ---
  const handleConfirmPurchase = async () => {
    setProcessingPurchase(true);
    setError(null);

    if (!selectedSupplier || cart.length === 0) {
      setError("Debe seleccionar un proveedor y añadir al menos un producto.");
      setProcessingPurchase(false);
      return;
    }

    try {
      const purchaseDetails = cart.map(item => ({
        producto: item.id,
        cantidad: Number(item.cantidad) || 0,
        costo_unitario: Number(item.costo_unitario) || 0,
      }));

      // validación manual en frontend
      if (purchaseDetails.some(d => d.cantidad <= 0 || d.costo_unitario <= 0)) {
        setError("Todos los productos deben tener cantidad y costo mayores a 0.");
        setProcessingPurchase(false);
        return;
      }

      const payload = { proveedor: selectedSupplier, detalles: purchaseDetails };

      const createdPurchaseResponse = await createPurchase(payload);
      const purchaseId = createdPurchaseResponse.data.id;

      await confirmPurchase(purchaseId);

      alert("Compra confirmada con éxito. El stock fue actualizado.");
      setCart([]);
      setSelectedSupplier('');
      nav("/productos", {
        replace: true,
        state: { success: "Compra registrada con éxito. Stock actualizado." },
      });
    } catch (err) {
      console.error("Error al confirmar la compra:", err);
      const apiDetail =
        err.response?.data?.detail ||
        JSON.stringify(err.response?.data) ||
        err.message ||
        "Error desconocido";
      setError("Ocurrió un error al procesar la compra: " + apiDetail);
    } finally {
      setProcessingPurchase(false);
    }
  };

  return (
    <div className="container py-4">
      <h1 className="h4 mb-4">Registrar Ingreso de Mercadería</h1>
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card p-4">
        {/* Selección de proveedor */}
        <div className="row mb-3">
          <div className="col-md-6">
            <label htmlFor="supplier-select" className="form-label">Proveedor</label>
            <select
              id="supplier-select"
              className="form-select"
              value={selectedSupplier}
              onChange={(e) => setSelectedSupplier(e.target.value)}
            >
              <option value="">Seleccione un proveedor</option>
              {suppliers.map(s => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Buscar producto */}
        <div className="row mb-3">
          <div className="col-md-6">
            <label htmlFor="search-product" className="form-label">Buscar Producto a Ingresar</label>
            <input
              type="text"
              id="search-product"
              className="form-control"
              placeholder="Escriba código o nombre..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              disabled={!selectedSupplier}
            />
            {loadingSearch && <div className="form-text">Buscando...</div>}
            {!selectedSupplier && (
              <div className="form-text text-warning">
                Debe seleccionar un proveedor primero.
              </div>
            )}
          </div>
        </div>

        {/* Resultados */}
        {searchResults.length > 0 && (
          <ul className="list-group mb-4">
            {searchResults.map(p => (
              <li key={p.id} className="list-group-item d-flex justify-content-between align-items-center">
                {p.nombre}
                <button
                  className="btn btn-sm btn-success"
                  onClick={() => addToCart(p)}
                >+</button>
              </li>
            ))}
          </ul>
        )}

        {/* Carrito */}
        <h2 className="h5 mt-4">Items de la Compra</h2>
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Producto</th>
                <th style={{ width: '120px' }}>Cantidad</th>
                <th style={{ width: '150px' }}>Costo Unit.</th>
                <th>Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {cart.length === 0 && (
                <tr><td colSpan="4" className="text-center text-muted">Añada productos a la compra</td></tr>
              )}
              {cart.map(item => (
                <tr key={item.id}>
                  <td>{item.nombre}</td>
                  <td>
                    <input
                      type="number"
                      className="form-control form-control-sm"
                      min="0"
                      value={isNaN(item.cantidad) ? '' : item.cantidad}
                      onChange={(e) => updateCartItem(item.id, 'cantidad', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.01"
                      className="form-control form-control-sm"
                      min="0"
                      value={isNaN(item.costo_unitario) ? '' : item.costo_unitario}
                      onChange={(e) => updateCartItem(item.id, 'costo_unitario', e.target.value)}
                    />
                  </td>
                  <td>${((item.costo_unitario || 0) * (item.cantidad || 0)).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="fw-bold">
                <td colSpan="3" className="text-end">TOTAL</td>
                <td>${totalCompra.toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div className="d-flex justify-content-end mt-4">
          <button
            className="btn btn-outline-secondary me-2"
            onClick={() => setCart([])}
            disabled={processingPurchase}
          >
            Limpiar
          </button>
          <button
            className="btn btn-primary"
            disabled={cart.length === 0 || !selectedSupplier || processingPurchase}
            onClick={handleConfirmPurchase}
          >
            {processingPurchase ? "Procesando..." : "Confirmar Compra"}
          </button>
        </div>
      </div>
    </div>
  );
}
