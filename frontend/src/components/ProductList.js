// src/components/ProductList.js
import React, { useState, useEffect } from 'react';
import apiClient from '../services/api'; // Importamos nuestro cliente de API

const ProductList = () => {
  const [products, setProducts] = useState([]); // Estado para guardar los productos
  const [loading, setLoading] = useState(true); // Estado para mostrar un mensaje de carga
  const [error, setError] = useState(null);     // Estado para manejar errores

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        // Hacemos la petición GET a nuestro endpoint de productos
        const response = await apiClient.get('/catalogo/productos/');
        
        // La API paginada de Django devuelve los datos en la propiedad "results"
        setProducts(response.data.results);
        setError(null);
      } catch (err) {
        setError("Hubo un error al cargar los productos. Revisa la consola para más detalles.");
        console.error("Error al obtener los productos:", err);
      } finally {
        setLoading(false); // La carga ha terminado (con o sin error)
      }
    };

    fetchProducts();
  }, []); // El array vacío [] asegura que esto se ejecute solo una vez

  if (loading) {
    return <p>Cargando productos...</p>;
  }

  if (error) {
    return <p style={{ color: 'red' }}>{error}</p>;
  }

  return (
    <div>
      <h1>Catálogo de Bebidas</h1>
      <div className="product-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            <h2>{product.nombre}</h2>
            <p>Marca: {product.marca}</p>
            <p>Categoría: {product.categoria_nombre || 'Sin categoría'}</p>
            <h3>${parseFloat(product.precio_venta).toFixed(2)}</h3>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductList;