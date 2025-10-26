// frontend/src/pages/ResumenDeVenta.jsx

export default function ResumenDeVenta({
  total,
  loading,
  ultimaVenta,
  anulando,
  onConfirmar,
  onCancelar,
  onAnularUltima,
}) {
  // helper: la última venta está confirmada?
  const isConfirmada =
    ultimaVenta &&
    ultimaVenta.estado &&
    ultimaVenta.estado.toLowerCase() === "confirmada";

  // abre el ticket PDF en una pestaña nueva
  const handleVerTicket = () => {
    if (!ultimaVenta || !ultimaVenta.id) return;

    const base = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const ventaId = ultimaVenta.id;
    const url = `${base}/api/ventas/${ventaId}/ticket/`;

    window.open(url, "_blank");
  };

  return (
    <div className="card shadow-sm">
      <div className="card-body">
        <h3 className="card-title fw-bold mb-4">Resumen de la Venta</h3>

        <div className="d-flex justify-content-between align-items-start mb-4">
          <div className="text-uppercase fw-semibold" style={{ fontSize: "1.1rem" }}>
            TOTAL
          </div>
          <div
            className="fw-bold text-nowrap"
            style={{ fontSize: "2rem", lineHeight: 1 }}
          >
            ${" "}
            {Number(total || 0).toLocaleString("es-AR", {
              minimumFractionDigits: 2,
            })}
          </div>
        </div>

        {/* Botón confirmar */}
        <button
          className="btn btn-primary btn-lg w-100 mb-3"
          style={{ backgroundColor: "#4e7cf5", borderColor: "#4e7cf5" }}
          disabled={loading || total <= 0}
          onClick={onConfirmar}
        >
          {loading ? "Procesando..." : "Confirmar Venta"}
        </button>

        {/* Botón cancelar */}
        <button
          className="btn btn-outline-danger btn-lg w-100 mb-4"
          disabled={loading}
          onClick={onCancelar}
        >
          Cancelar
        </button>

        {/* panel última venta */}
        <div className="border rounded p-3 bg-light">
          {ultimaVenta ? (
            <>
              <p className="mb-1">
                Última venta: #{ultimaVenta.id} – Estado:{" "}
                <strong>{ultimaVenta.estado}</strong>
              </p>
              <p className="mb-3">
                Total: $
                {Number(ultimaVenta.total || 0).toLocaleString("es-AR", {
                  minimumFractionDigits: 2,
                })}
              </p>

              {isConfirmada ? (
                <>
                  <button
                    className="btn btn-warning w-100 mb-2"
                    disabled={anulando}
                    onClick={onAnularUltima}
                  >
                    {anulando ? "Anulando..." : "Anular Última Venta"}
                  </button>

                  <button
                    className="btn btn-outline-secondary w-100"
                    onClick={handleVerTicket}
                  >
                    Ver Ticket (PDF)
                  </button>
                </>
              ) : (
                <button className="btn btn-secondary w-100" disabled>
                  Ya anulada
                </button>
              )}
            </>
          ) : (
            <p className="text-muted mb-0">
              Todavía no hay ventas confirmadas en esta sesión.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
