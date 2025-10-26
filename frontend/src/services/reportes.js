import api from "../api/client.jsx";

export const fetchResumenDia = () =>
  api.get("/reportes/resumen-dia/");
