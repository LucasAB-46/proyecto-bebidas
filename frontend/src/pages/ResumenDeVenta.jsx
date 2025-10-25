import React from "react";

function money(n) {
  if (n == null || isNaN(n)) return "$0.00";
  const num = Number(n);
  return num.toLocaleString("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function ResumenDeVenta({
  total,
  ultimaVenta,
  confirmDisabled,
  cancelDisabled,
  processing,
  onConfirm,
  onCancel,
  onAnularUltima,
}) {
  return (
    <aside
      style={{
        flex: "0 0 400px",
        maxWidth: 400,
        border: "1px solid #ccc",
        borderRadius: "6px",
        padding: "1rem",
      }}
    >
      {/* Título */}
      <h2
        style={{
          fontSize: "1.6rem",
          marginBottom: "1rem",
          fontWeight: 600,
          lineHeight: 1.2,
        }}
      >
        Resumen de la Venta
      </h2>

      {/* TOTAL */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: "1rem",
        }}
      >
        <div
          style={{
            fontSize: "1.5rem",
            fontWeight: 600,
            color: "#000",
          }}
        >
          TOTAL
        </div>
        <div
          style={{
            fontSize: "2rem",
            fontWeight: 700,
            color: "#000",
          }}
        >
          {money(total)}
        </div>
      </div>

      {/* Botón Confirmar */}
      <button
        disabled={confirmDisabled}
        onClick={onConfirm}
        style={{
          width: "100%",
          backgroundColor: confirmDisabled ? "#4e7dd8aa" : "#4e7dd8",
          color: "white",
          fontSize: "1.4rem",
          fontWeight: 600,
          padding: "1rem",
          borderRadius: "6px",
          border: "1px solid #3061c9",
          cursor: confirmDisabled ? "not-allowed" : "pointer",
          marginBottom: "0.75rem",
        }}
      >
        {processing ? "Procesando..." : "Confirmar Venta"}
      </button>

      {/* Botón Cancelar */}
      <button
        disabled={cancelDisabled}
        onClick={onCancel}
        style={{
          width: "100%",
          backgroundColor: "white",
          color: "#c11a1a",
          fontSize: "1.4rem",
          fontWeight: 500,
          padding: "1rem",
          borderRadius: "6px",
          border: "1px solid #c11a1a",
          cursor: cancelDisabled ? "not-allowed" : "pointer",
          marginBottom: "1rem",
        }}
      >
        Cancelar
      </button>

      {/* Box Última Venta */}
      <div
        style={{
          backgroundColor: "#eee",
          borderRadius: "6px",
          padding: "1rem",
          fontSize: "1.4rem",
          lineHeight: 1.4,
          color: "#000",
        }}
      >
        {ultimaVenta ? (
          <>
            <div style={{ marginBottom: "0.5rem" }}>
              Última venta: #{ultimaVenta.id} – Estado:{" "}
              <strong>{ultimaVenta.estado?.toUpperCase()}</strong>
            </div>
            <div style={{ marginBottom: "0.75rem" }}>
              Total: {money(ultimaVenta.total)}
            </div>

            {ultimaVenta.estado === "confirmada" ? (
              <button
                onClick={onAnularUltima}
                style={{
                  backgroundColor: "#facc15",
                  border: "1px solid #d4b113",
                  borderRadius: "4px",
                  padding: "0.6rem 1rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Anular Última Venta
              </button>
            ) : (
              <button
                disabled
                style={{
                  backgroundColor: "#d1d5db",
                  border: "1px solid #9ca3af",
                  borderRadius: "4px",
                  padding: "0.6rem 1rem",
                  fontWeight: 600,
                  color: "#000",
                  cursor: "not-allowed",
                }}
              >
                Ya anulada
              </button>
            )}
          </>
        ) : (
          <div style={{ color: "#555" }}>
            No hay ventas en este turno todavía.
          </div>
        )}
      </div>

      {/* Link ir a productos */}
      <div
        style={{
          textAlign: "right",
          marginTop: "1.5rem",
          fontSize: "1.4rem",
        }}
      >
        <a
          href="/productos"
          style={{
            color: "#1e3a8a",
            textDecoration: "none",
            fontWeight: 500,
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <span
            style={{
              display: "inline-block",
              border: "2px solid #1e3a8a",
              borderRadius: "4px",
              padding: "0.2rem 0.4rem",
              fontWeight: 600,
              lineHeight: 1,
              fontSize: "1.2rem",
            }}
          >
            ↩
          </span>
          Ir a Productos
        </a>
      </div>
    </aside>
  );
}
