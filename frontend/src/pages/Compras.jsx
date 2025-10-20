// src/pages/Compras.jsx

import React, { useState, useEffect, useMemo } from 'react';
import { listProducts, listSuppliers } from '../services/products';
import { createPurchase, confirmPurchase } from '../services/purchases'; // <-- 1. IMPORTAMOS SERVICIOS DE COMPRAS

export default function Compras() {
  // --- ESTADOS ---
  const [suppliers, setSuppliers] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState('');
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [error, setError] = useState(null);
  const [processingPurchase, setProcessingPurchase] = useState(false); // <-- 2. NUEVO ESTADO

  // --- EFECTOS ---
  useEffect(() => {
    const fetchSuppliers = async () => {
      try {
        const response = await listSuppliers();
        setSuppliers(response.data.results || response.data);
      } catch (error) {
        console.error("Error al cargar proveedores:", error);
        setError("No se pudieron cargar los proveedores.");
      }
    };
    fetchSuppliers();
  }, []);

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

  // --- LÓGICA DEL CARRITO ---
  const addToCart = (product) => {
    setCart(currentCart => {
      const existingProduct = currentCart.find(item => item.id === product.id);
      if (existingProduct) {
        return currentCart.map(item =>
          item.id === product.id ? { ...item, cantidad: item.cantidad + 1 } : item
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
      const rawValue = value === '' ? 0 : value;
      const newValue = field === 'costo_unitario' ? parseFloat(rawValue) : parseInt(rawValue, 10);
      if (field === 'cantidad' && newValue <= 0) {
        return currentCart.filter(item => item.id !== productId);
      }
      return currentCart.map(item =>
        item.id === productId ? { ...item, [field]: newValue } : item
      );
    });
  };

  const totalCompra = useMemo(() => {
    return cart.reduce((total, item) => total + (item.costo_unitario * item.cantidad), 0);
  }, [cart]);

  // --- 3. NUEVA FUNCIÓN PARA CONFIRMAR LA COMPRA ---
  const handleConfirmPurchase = async () => {
    setProcessingPurchase(true);
    setError(null);

    // Validación simple
    if (!selectedSupplier || cart.length === 0) {
      setError("Debe seleccionar un proveedor y añadir al menos un producto.");
      setProcessingPurchase(false);
      return;
    }

    try {
      const purchaseDetails = cart.map(item => ({
        producto: item.id,
        cantidad: item.cantidad,
        costo_unitario: item.costo_unitario,
      }));

      const payload = {
        proveedor: selectedSupplier,
        detalles: purchaseDetails,
      };

      const createdPurchaseResponse = await createPurchase(payload);
      const purchaseId = createdPurchaseResponse.data.id;

      await confirmPurchase(purchaseId);

      alert("¡Compra confirmada con éxito! El stock ha sido actualizado.");
      // Limpiamos el formulario
      setCart([]);
      setSelectedSupplier('');

    } catch (error) {
      console.error("Error al confirmar la compra:", error);
      const errorMessage = error.response?.data?.detail || "Ocurrió un error al procesar la compra.";
      setError(errorMessage);
    } finally {
      setProcessingPurchase(false);
    }
  };

  return (
    <div className="container py-4">
      <h1 className="h4 mb-4">Registrar Ingreso de Mercadería</h1>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card p-4">
        <div className="row mb-3">
          <div className="col-md-6">
            <label htmlFor="supplier-select" className="form-label">Proveedor</label>
            <select id="supplier-select" className="form-select" value={selectedSupplier} onChange={(e) => setSelectedSupplier(e.target.value)}>
              <option value="">Seleccione un proveedor</option>
              {suppliers.map(supplier => (
                <option key={supplier.id} value={supplier.id}>{supplier.nombre}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="row mb-3">
          <div className="col-md-6">
            <label htmlFor="search-product" className="form-label">Buscar Producto a Ingresar</label>
            <input type="text" id="search-product" className="form-control" placeholder="Escriba código o nombre..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} disabled={!selectedSupplier} />
            {loadingSearch && <div className="form-text">Buscando...</div>}
            {!selectedSupplier && <div className="form-text text-warning">Debe seleccionar un proveedor primero.</div>}
          </div>
        </div>

        {searchResults.length > 0 && (
          <ul className="list-group mb-4">
            {searchResults.map(product => (
              <li key={product.id} className="list-group-item d-flex justify-content-between align-items-center">
                {product.nombre}
                <button className="btn btn-sm btn-success" onClick={() => addToCart(product)}>+</button>
              </li>
            ))}
          </ul>
        )}

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
                  <td><input type="number" className="form-control form-control-sm" value={item.cantidad} onChange={(e) => updateCartItem(item.id, 'cantidad', e.target.value)} min="0" /></td>
                  <td><input type="number" step="0.01" className="form-control form-control-sm" value={item.costo_unitario} onChange={(e) => updateCartItem(item.id, 'costo_unitario', e.target.value)} min="0" /></td>
                  <td>${(item.costo_unitario * item.cantidad).toFixed(2)}</td>
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
          <button className="btn btn-outline-secondary me-2" onClick={() => setCart([])} disabled={processingPurchase}>Limpiar</button>
          <button 
            className="btn btn-primary" 
            disabled={cart.length === 0 || !selectedSupplier || processingPurchase}
            onClick={handleConfirmPurchase} // <-- 4. CONECTAMOS LA FUNCIÓN
          >
            {processingPurchase ? "Procesando..." : "Confirmar Compra"}
          </button>
        </div>
      </div>
    </div>
  );
}