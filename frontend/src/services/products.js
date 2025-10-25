// src/services/products.js
import api from '../api/client.jsx';

export const listProducts = (params) => api.get('/catalogo/productos/', { params });
export const deleteProduct = (productId) => api.delete(`/catalogo/productos/${productId}/`);
export const listCategories = () => api.get('/catalogo/categorias/');
export const createProduct = (productData) => api.post('/catalogo/productos/', productData);
export const getProduct = (productId) => api.get(`/catalogo/productos/${productId}/`);
export const updateProduct = (productId, productData) => api.patch(`/catalogo/productos/${productId}/`, productData);
export const listSuppliers = () => {
  // Asumimos que la paginación está activada, pedimos una página grande.
  return api.get('/catalogo/proveedores/', { params: { page_size: 100 } });
};
export const fetchProductos = (params) => api.get('/catalogo/productos/', { params });
