import { useEffect, useState } from "react";
import api from "../api/client.jsx";

export default function Dashboard() {
  // estado de carga / error
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // data del backend
  const [data, setData] = useState({
    // valores iniciales dummy para que la pantalla no truene antes de cargar
    fecha: "",
    ventas: { cantidad: 0, total: "0.00" },
    compras: { cantidad: 0, total: "0.00" },
    balance: "0.00",
    stock_bajo: [],
    ultimos_movimientos: {
      venta: null,
      compra: null,
    },
  });

  // cargar datos al montar
  useEffect(() => {
    const fetchResumen = async () => {
      try {
        setLoading(true);
        setError("");

        // GET /api/reportes/resumen-dia/
        const resp = await api.get("/reportes/resumen-dia/");
        setData(resp.data);
      } catch (err) {
        console.error("Error cargando resumen del día", err);
        setError(
          err.response?.data?.detail ||
            "No se pudo cargar el resumen del día."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchResumen();
  }, []);

  // helpers de formato
  const fmtMoney = (valor) => {
    const n = Number(valor || 0);
    return n.toLocaleString("es-AR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  return (
    <div className="container mt-4">
      <h1 className="mb-4">Dashboard</h1>

      {loading && (
        <div className="alert alert-info">Cargando información del día...</div>
      )}

      {error && (
        <div className="alert alert-danger">
          {error}
          <br />
          <small className="text-muted">
            Probá refrescar la página o iniciar sesión de nuevo.
          </small>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* ---- FILA 1: RESUMEN NÚMEROS ---- */}
          <div className="row g-3 mb-4">
            {/* Ventas Hoy */}
            <div className="col-12 col-md-4">
              <div className="card shadow-sm h-100">
                <div className="card-body">
                  <h5 className="card-title text-muted text-uppercase mb-2">
                    Ventas de Hoy
                  </h5>
                  <div className="d-flex justify-content-between align-items-end">
                    <div>
                      <div className="fw-bold" style={{ fontSize: "1.8rem" }}>
                        ${fmtMoney(data.ventas.total)}
                      </div>
                      <div className="text-muted" style={{ fontSize: "0.9rem" }}>
                        {data.ventas.cantidad} venta
                        {Number(data.ventas.cantidad) === 1 ? "" : "s"}
                      </div>
                    </div>
                    <span
                      className="badge bg-success-subtle border border-success text-success"
                      style={{ fontSize: "0.8rem" }}
                    >
                      HOY
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Compras Hoy */}
            <div className="col-12 col-md-4">
              <div className="card shadow-sm h-100">
                <div className="card-body">
                  <h5 className="card-title text-muted text-uppercase mb-2">
                    Compras de Hoy
                  </h5>
                  <div className="d-flex justify-content-between align-items-end">
                    <div>
                      <div className="fw-bold" style={{ fontSize: "1.8rem" }}>
                        ${fmtMoney(data.compras.total)}
                      </div>
                      <div className="text-muted" style={{ fontSize: "0.9rem" }}>
                        {data.compras.cantidad} compra
                        {Number(data.compras.cantidad) === 1 ? "" : "s"}
                      </div>
                    </div>
                    <span
                      className="badge bg-primary-subtle border border-primary text-primary"
                      style={{ fontSize: "0.8rem" }}
                    >
                      HOY
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Balance */}
            <div className="col-12 col-md-4">
              <div className="card shadow-sm h-100">
                <div className="card-body">
                  <h5 className="card-title text-muted text-uppercase mb-2">
                    Balance del Día
                  </h5>
                  <div className="d-flex justify-content-between align-items-end">
                    <div>
                      <div
                        className="fw-bold"
                        style={{ fontSize: "1.8rem" }}
                      >
                        ${fmtMoney(data.balance)}
                      </div>
                      <div className="text-muted" style={{ fontSize: "0.9rem" }}>
                        ventas - compras
                      </div>
                    </div>
                    <span
                      className={
                        Number(data.balance) >= 0
                          ? "badge bg-success text-light"
                          : "badge bg-danger text-light"
                      }
                      style={{ fontSize: "0.8rem" }}
                    >
                      {Number(data.balance) >= 0 ? "Positivo" : "Negativo"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ---- FILA 2: STOCK BAJO + ÚLTIMOS MOVIMIENTOS ---- */}
          <div className="row g-3">
            {/* Stock Bajo */}
            <div className="col-12 col-lg-6">
              <div className="card shadow-sm h-100">
                <div className="card-body">
                  <h5 className="card-title fw-bold mb-3">
                    Stock Bajo / Crítico
                  </h5>

                  {(!data.stock_bajo || data.stock_bajo.length === 0) && (
                    <p className="text-muted mb-0">
                      No hay productos en nivel crítico 👌
                    </p>
                  )}

                  {data.stock_bajo && data.stock_bajo.length > 0 && (
                    <div className="table-responsive">
                      <table className="table align-middle mb-0">
                        <thead>
                          <tr>
                            <th>Producto</th>
                            <th style={{ width: "120px" }} className="text-end">
                              Stock
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.stock_bajo.map((p) => (
                            <tr key={p.id}>
                              <td>{p.nombre}</td>
                              <td className="text-end fw-bold">{p.stock}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Últimos Movimientos */}
            <div className="col-12 col-lg-6">
              <div className="card shadow-sm h-100">
                <div className="card-body">
                  <h5 className="card-title fw-bold mb-3">
                    Últimos Movimientos
                  </h5>

                  <div className="mb-4">
                    <div className="text-muted text-uppercase small">
                      Última Venta
                    </div>
                    {data.ultimos_movimientos.venta ? (
                      <div className="border rounded p-2">
                        <div className="d-flex justify-content-between">
                          <div>
                            <div>
                              Venta #{data.ultimos_movimientos.venta.id} –{" "}
                              <strong>
                                {data.ultimos_movimientos.venta.estado}
                              </strong>
                            </div>
                            <div className="text-muted">
                              {data.ultimos_movimientos.venta.hora} hs
                            </div>
                          </div>
                          <div className="fw-bold text-nowrap">
                            $
                            {fmtMoney(
                              data.ultimos_movimientos.venta.total
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-muted">
                        No hay ventas confirmadas hoy.
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="text-muted text-uppercase small">
                      Última Compra
                    </div>
                    {data.ultimos_movimientos.compra ? (
                      <div className="border rounded p-2">
                        <div className="d-flex justify-content-between">
                          <div>
                            <div>
                              Compra #{data.ultimos_movimientos.compra.id} –{" "}
                              <strong>
                                {data.ultimos_movimientos.compra.estado}
                              </strong>
                            </div>
                            <div className="text-muted">
                              {data.ultimos_movimientos.compra.hora} hs
                            </div>
                          </div>
                          <div className="fw-bold text-nowrap">
                            $
                            {fmtMoney(
                              data.ultimos_movimientos.compra.total
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-muted">
                        No hay compras confirmadas hoy.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Fecha en el pie */}
          <div className="text-end text-muted small mt-4">
            Datos del día {data.fecha || "-"}
          </div>
        </>
      )}
    </div>
  );
}

