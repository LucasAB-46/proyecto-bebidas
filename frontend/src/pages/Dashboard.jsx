// src/pages/Dashboard.jsx
import { useEffect, useState } from "react";
import { getResumenFinanciero, getTopProductos } from "../services/reportes.js";

export default function Dashboard() {
  // rango de fechas
  const hoyISO = new Date().toISOString().slice(0, 10); // "YYYY-MM-DD"

  const [desde, setDesde] = useState(hoyISO);
  const [hasta, setHasta] = useState(hoyISO);

  // datos resumen financiero
  const [resumen, setResumen] = useState(null);
  const [cargandoResumen, setCargandoResumen] = useState(false);
  const [errorResumen, setErrorResumen] = useState("");

  // top productos
  const [topProductos, setTopProductos] = useState([]);
  const [cargandoTop, setCargandoTop] = useState(false);
  const [errorTop, setErrorTop] = useState("");

  // función para cargar ambos panels
  const fetchData = async () => {
    setCargandoResumen(true);
    setCargandoTop(true);
    setErrorResumen("");
    setErrorTop("");

    const params = { desde, hasta };

    try {
      const rf = await getResumenFinanciero(params);
      setResumen(rf.data);
    } catch (err) {
      console.error("Error resumen financiero", err);
      setErrorResumen(
        err.response?.data?.detail || "No se pudo cargar el resumen financiero."
      );
    } finally {
        setCargandoResumen(false);
    }

    try {
      const tp = await getTopProductos({ ...params, limit: 5 });
      setTopProductos(tp.data || []);
    } catch (err) {
      console.error("Error top productos", err);
      setErrorTop(
        err.response?.data?.detail || "No se pudieron cargar los productos más vendidos."
      );
    } finally {
        setCargandoTop(false);
    }
  };

  // cargar al inicio
  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // una sola vez al montar

  const handleAplicar = () => {
    fetchData();
  };

  return (
    <div className="container mt-4">
      <h1 className="mb-4">Dashboard</h1>

      {/* Filtros de fecha */}
      <div className="card mb-4">
        <div className="card-body">
          <h5 className="card-title fw-bold mb-3">Rango de fechas</h5>
          <div className="row g-3 align-items-end">
            <div className="col-12 col-md-4">
              <label className="form-label">Desde</label>
              <input
                type="date"
                value={desde}
                className="form-control"
                onChange={(e) => setDesde(e.target.value)}
              />
            </div>
            <div className="col-12 col-md-4">
              <label className="form-label">Hasta</label>
              <input
                type="date"
                value={hasta}
                className="form-control"
                onChange={(e) => setHasta(e.target.value)}
              />
            </div>
            <div className="col-12 col-md-4">
              <button
                className="btn btn-primary w-100"
                style={{ backgroundColor: "#4e7cf5", borderColor: "#4e7cf5" }}
                onClick={handleAplicar}
              >
                Aplicar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Resumen financiero */}
      <div className="row">
        <div className="col-12 col-lg-6 mb-4">
          <div className="card h-100 shadow-sm">
            <div className="card-body">
              <h5 className="card-title fw-bold mb-3">
                Resumen financiero
              </h5>

              {cargandoResumen ? (
                <p>Cargando...</p>
              ) : errorResumen ? (
                <div className="alert alert-danger">{errorResumen}</div>
              ) : resumen ? (
                <>
                  <p className="mb-1 text-muted">
                    Desde {resumen.desde} hasta {resumen.hasta}
                  </p>

                  <div className="d-flex justify-content-between mb-2">
                    <span>Ventas ($)</span>
                    <strong>
                      {Number(resumen.total_ventas || 0).toLocaleString(
                        "es-AR",
                        { minimumFractionDigits: 2 }
                      )}
                    </strong>
                  </div>

                  <div className="d-flex justify-content-between mb-2">
                    <span>Compras ($)</span>
                    <strong>
                      {Number(resumen.total_compras || 0).toLocaleString(
                        "es-AR",
                        { minimumFractionDigits: 2 }
                      )}
                    </strong>
                  </div>

                  <div className="d-flex justify-content-between mb-2">
                    <span>Margen bruto ($)</span>
                    <strong>
                      {Number(resumen.margen_bruto || 0).toLocaleString(
                        "es-AR",
                        { minimumFractionDigits: 2 }
                      )}
                    </strong>
                  </div>

                  <hr />

                  <div className="d-flex justify-content-between mb-1">
                    <span># Ventas</span>
                    <strong>{resumen.cantidad_ventas}</strong>
                  </div>

                  <div className="d-flex justify-content-between">
                    <span># Compras</span>
                    <strong>{resumen.cantidad_compras}</strong>
                  </div>
                </>
              ) : (
                <p className="text-muted">Sin datos.</p>
              )}
            </div>
          </div>
        </div>

        {/* Top productos vendidos */}
        <div className="col-12 col-lg-6 mb-4">
          <div className="card h-100 shadow-sm">
            <div className="card-body">
              <h5 className="card-title fw-bold mb-3">
                Top productos vendidos
              </h5>

              {cargandoTop ? (
                <p>Cargando...</p>
              ) : errorTop ? (
                <div className="alert alert-danger">{errorTop}</div>
              ) : topProductos.length === 0 ? (
                <p className="text-muted">No hay ventas en este rango.</p>
              ) : (
                <div className="table-responsive">
                  <table className="table align-middle mb-0">
                    <thead>
                      <tr>
                        <th>Producto</th>
                        <th className="text-end">Cant. vendida</th>
                        <th className="text-end">Facturación $</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topProductos.map((row) => (
                        <tr key={row.producto_id}>
                          <td style={{ minWidth: "140px" }}>
                            {row.producto_nombre}
                          </td>
                          <td className="text-end">
                            {Number(row.cantidad_vendida || 0).toLocaleString(
                              "es-AR",
                              { minimumFractionDigits: 2 }
                            )}
                          </td>
                          <td className="text-end">
                            {Number(row.facturacion || 0).toLocaleString(
                              "es-AR",
                              { minimumFractionDigits: 2 }
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
