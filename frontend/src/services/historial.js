// src/services/historial.js
import api from "../api/client.jsx";

// ----- VENTAS -----
export const fetchHistorialVentas = (params) =>
  api.get("/ventas/historial/", { params });

export const fetchVentaDetalle = (id) =>
  api.get(`/ventas/${id}/`);

// ----- COMPRAS -----
export const fetchHistorialCompras = (params) =>
  api.get("/compras/historial/", { params });

export const fetchCompraDetalle = (id) =>
  api.get(`/compras/${id}/`);
