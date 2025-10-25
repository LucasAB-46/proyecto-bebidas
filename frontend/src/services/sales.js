import api from "../api/client.jsx";

export const createSale   = (payload) => api.post("/ventas/", payload);
export const confirmSale  = (id)      => api.post(`/ventas/${id}/confirmar/`);
export const annulSale    = (id)      => api.post(`/ventas/${id}/anular/`);
