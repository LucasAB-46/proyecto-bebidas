import { useEffect, useState } from "react";
import {
  fetchHistorialVentas,
  fetchVentaDetalle,
} from "../services/historial.js";
import ModalDetalleOperacion from "../components/ModalDetalleOperacion.jsx";

export default function HistorialVentas() {
  const hoyISO = new Date().toISOString().slice(0, 10);

  const [desde, setDesde] = useState(hoyISO);
  const [hasta, setHasta] = useState(hoyISO);
  const [estado, setEstado] = useState("todos");

  const [items, setItems] = useState([]); // listado
  const [loadingList, setLoadingList] = useState(false);

  const [showModal, setShowModal] = useState(false);
  const [detalle, setDetalle] = useState(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);

  const buscar = async () => {
    setLoadingList(true);
    try {
      const resp = await fetchHistorialVentas({
        desde,
        hasta,
        estado,
      });
      const data = resp.data?.results || [];
      setItems(data);
    } catch (err) {
      console.error("Error cargando historial ventas", err);
      alert("No se pudo cargar el historial de ventas.");
    } finally {
      setLoadingList(false);
    }
  };

  const verDetalle = async (id) => {
    setShowModal(true);
    setLoadingDetalle(true);
    setDetalle(null);

    try {
      const resp = await fetchVentaDetalle(id);
      setDetalle(resp.data);
    } catch (err) {
      console.error("Error cargando detalle venta", err);
      alert("No se pudo cargar el detalle.");
    } finally {
      setLoadingDetalle(false);
    }
  };

  useEffect(() => {
    buscar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="container mt-4">
      <h1 className="mb-4">Historial de Ventas</h1>

      {/* Filtros */}
      <div className="card mb-4">
        <div className="card-body row g-3 align-items-end">
          <div className="col-sm-6 col-md-3">
            <label className="form-label fw-bold">Desde</label>
            <input
              type="date"
              className="form-control"
              value={desde}
              onChange={(e) => setDesde(e.target.value)}
            />
          </div>

          <div className="col-sm-6 col-md-3">
            <label className="form-label fw-bold">Hasta</label>
            <input
              type="date"
              className="form-control"
              value={hasta}
              onChange={(e) => setHasta(e.target.value)}
            />
          </div>

          <div className="col-sm-6 col-md-3">
            <label className="form-label fw-bold">Estado</label>
            <select
              className="form-select"
              value={estado}
              onChange={(e) => setEstado(e.target.value)}
            >
              <option value="todos">Todos</option>
              <option value="borrador">Borrador</option>
              <option value="confirmada">Confirmada</option>
              <option value="anulada">Anulada</option>
            </select>
          </div>

          <div className="col-sm-6 col-md-3 d-grid">
            <button
              className="btn btn-primary btn-lg"
              disabled={loadingList}
              onClick={buscar}
            >
              {loadingList ? "Buscando..." : "Buscar"}
            </button>
          </div>
        </div>
      </div>

      {/* Tabla resultados */}
      <div className="table-responsive border rounded">
        <table className="table align-middle mb-0">
          <thead className="table-light">
            <tr>
              <th>#</th>
              <th>Fecha</th>
              <th>Estado</th>
              <th>Total</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan="5" className="text-center py-4">
                  {loadingList
                    ? "Cargando..."
                    : "No se encontraron ventas en ese rango"}
                </td>
              </tr>
            ) : (
              items.map((venta) => (
                <tr key={venta.id}>
                  <td>#{venta.id}</td>
                  <td>{new Date(venta.fecha).toLocaleString()}</td>
                  <td className="text-capitalize">{venta.estado}</td>
                  <td>
                    $
                    {Number(venta.total || 0).toLocaleString("es-AR", {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                  <td>
                    <button
                      className="btn btn-outline-dark btn-sm"
                      onClick={() => verDetalle(venta.id)}
                    >
                      Ver detalle
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal detalle */}
      <ModalDetalleOperacion
        show={showModal}
        onClose={() => setShowModal(false)}
        data={loadingDetalle ? null : detalle}
        tipo="venta"
      />
    </div>
  );
}
