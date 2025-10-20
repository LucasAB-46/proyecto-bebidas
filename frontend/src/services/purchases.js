// src/services/purchases.js
import api from "../api/client.jsx";

export const createPurchase = (payload) => api.post("/compras/", payload);
export const confirmPurchase = (id) => api.post(`/compras/${id}/confirmar/`);
export const annulPurchase = (id) => api.post(`/compras/${id}/anular/`);