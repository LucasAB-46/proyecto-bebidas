import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/client.jsx";

const LocalContext = createContext(null);

export function LocalProvider({ children }) {
  const [locales, setLocales] = useState([]);        // [{id, nombre, ...}]
  const [localActual, setLocalActual] = useState(null); // {id, nombre,...}
  const [cargandoLocales, setCargandoLocales] = useState(true);

  // cargar locales al montar
  useEffect(() => {
    const fetchLocales = async () => {
      try {
        const resp = await api.get("/core/locales/");
        const data = resp.data?.results ?? resp.data; // DRF puede paginar
        setLocales(data);

        // preferencia guardada?
        const guardado = localStorage.getItem("localActualId");
        if (guardado) {
          const found = data.find(l => String(l.id) === String(guardado));
          if (found) {
            setLocalActual(found);
            setCargandoLocales(false);
            return;
          }
        }

        // si no hay guardado, elegimos el primero
        if (data.length > 0) {
          setLocalActual(data[0]);
          localStorage.setItem("localActualId", data[0].id);
        }
      } catch (err) {
        console.error("Error cargando locales", err);
      } finally {
        setCargandoLocales(false);
      }
    };

    fetchLocales();
  }, []);

  // cambiar local actual
  const cambiarLocal = (nuevoId) => {
    const elegido = locales.find(l => String(l.id) === String(nuevoId));
    if (elegido) {
      setLocalActual(elegido);
      localStorage.setItem("localActualId", elegido.id);
    }
  };

  return (
    <LocalContext.Provider
      value={{
        locales,
        localActual,
        cargandoLocales,
        cambiarLocal,
      }}
    >
      {children}
    </LocalContext.Provider>
  );
}

export function useLocal() {
  return useContext(LocalContext);
}
