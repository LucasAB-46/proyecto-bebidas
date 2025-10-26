// src/services/reportes.js
import api from "../api/client.jsx";

// GET /api/reportes/financieros/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
export const getResumenFinanciero = (params) =>
  api.get("/reportes/financieros/", { params });

// GET /api/reportes/top-productos/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD&limit=5
export const getTopProductos = (params) =>
  api.get("/reportes/top-productos/", { params });
