import { useEffect, useState } from "react";
import { fetchResumenDia } from "../services/reportes.js";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchResumenDia()
      .then((res) => {
        setData(res.data);
      })
      .catch((err) => {
        console.error("Error cargando resumen del día", err);
        setError("No se pudo cargar el resumen del día.");
      })
      .finally(() => {
        setCargando(false);
      });
  }, []);

  if (cargando) {
    return (
      <div className="container mt-4">
        <h2>Dashboard</h2>
        <p>Cargando...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mt-4">
        <h2>Dashboard</h2>
        <p className="text-danger">{error}</p>
      </div>
    );
  }

  const ventasHoy = data?.ventas ?? { cantidad: "0", total: "0.00" };
  const comprasHoy = data?.compras ?? { cantidad: "0", total: "0.00" };
  const balance = data?.balance ?? "0.00";

  const stockBajo = data?.stock_bajo ?? [];
  const ultimos = data?.ultimos_movimientos ?? {};

  return (
    <div className="container mt-4">
      <h2 className="mb-3">Dashboard</h2>
      <p className="text-muted">Fecha: {data?.fecha}</p>

      {/* KPIs */}
      <div className="row g-3 mb-4">
        <div className="col-12 col-md-4">
          <div className="card shadow-sm">
            <div className="card-body">
              <h5 className="card-title">Ventas hoy</h5>
              <p className="card-text mb-1">
                Cantidad: {ventasHoy.cantidad}
              </p>
              <p className="card-text fw-bold">
                Total: ${Number(ventasHoy.total).toLocaleString("es-AR")}
              </p>
            </div>
          </div>
        </div>

        <div className="col-12 col-md-4">
          <div className="card shadow-sm">
            <div className="card-body">
              <h5 className="card-title">Compras hoy</h5>
              <p className="card-text mb-1">
                Cantidad: {comprasHoy.cantidad}
              </p>
              <p className="card-text fw-bold">
                Total: ${Number(comprasHoy.total).toLocaleString("es-AR")}
              </p>
            </div>
          </div>
        </div>

        <div className="col-12 col-md-4">
          <div className="card shadow-sm">
            <div className="card-body">
              <h5 className="card-title">Balance</h5>
              <p className="card-text fw-bold">
                ${Number(balance).toLocaleString("es-AR")}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Últimos movimientos */}
      <div className="row g-3 mb-4">
        <div className="col-12 col-md-6">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <h5 className="card-title">Última Venta</h5>
              {ultimos.venta ? (
                <>
                  <p className="mb-1">
                    #{ultimos.venta.id} – {ultimos.venta.estado}
                  </p>
                  <p className="mb-1">
                    Total: ${Number(ultimos.venta.total).toLocaleString("es-AR")}
                  </p>
                  <p className="text-muted mb-0">Hora: {ultimos.venta.hora}</p>
                </>
              ) : (
                <p className="text-muted mb-0">No hay ventas hoy.</p>
              )}
            </div>
          </div>
        </div>

        <div className="col-12 col-md-6">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <h5 className="card-title">Última Compra</h5>
              {ultimos.compra ? (
                <>
                  <p className="mb-1">
                    #{ultimos.compra.id} – {ultimos.compra.estado}
                  </p>
                  <p className="mb-1">
                    Total: ${Number(ultimos.compra.total).toLocaleString("es-AR")}
                  </p>
                  <p className="text-muted mb-0">Hora: {ultimos.compra.hora}</p>
                </>
              ) : (
                <p className="text-muted mb-0">No hay compras hoy.</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stock bajo */}
      <div className="card shadow-sm">
        <div className="card-body">
          <h5 className="card-title">Stock bajo (≤5 u.)</h5>
          {stockBajo.length === 0 ? (
            <p className="text-muted mb-0">Todo OK 🎉</p>
          ) : (
            <div className="table-responsive">
              <table className="table align-middle mb-0">
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Stock</th>
                  </tr>
                </thead>
                <tbody>
                  {stockBajo.map((row) => (
                    <tr key={row.id}>
                      <td>{row.nombre}</td>
                      <td>{row.stock}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
