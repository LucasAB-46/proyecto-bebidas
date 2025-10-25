import React from "react";

function fmtMoney(n) {
  return `$${Number(n || 0).toLocaleString("es-AR")}`;
}

export default function ResumenDeVenta({
  total,
  ultimaVenta,
  onConfirmar,
  onCancelar,
  onAnularUltima,
  cargandoConfirmar,
}) {
  // Por ahora es un número fijo. Después lo vamos a sacar de /api/reportes/caja_actual/
  const cajaActual = 123456; // TODO: reemplazar con valor real más adelante

  return (
    <div className="flex flex-col gap-4">
      {/* Título */}
      <header>
        <h2 className="text-xl font-semibold text-gray-900">
          Resumen de la Venta
        </h2>
      </header>

      {/* Caja actual */}
      <div className="flex justify-between items-baseline border-b pb-2">
        <span className="text-sm text-gray-600 font-medium">
          Caja actual
        </span>
        <span className="text-base font-semibold text-gray-800">
          {fmtMoney(cajaActual)}
        </span>
      </div>

      {/* TOTAL */}
      <div className="flex justify-between items-baseline">
        <span className="text-2xl font-bold text-gray-900">TOTAL</span>
        <span className="text-2xl font-bold text-gray-900">
          {fmtMoney(total)}
        </span>
      </div>

      {/* Botón Confirmar Venta */}
      <button
        className="w-full rounded bg-blue-500 text-white font-medium text-lg py-3 hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={cargandoConfirmar}
        onClick={onConfirmar}
      >
        {cargandoConfirmar ? "Confirmando..." : "Confirmar Venta"}
      </button>

      {/* Botón Cancelar */}
      <button
        className="w-full rounded border border-red-400 text-red-600 font-medium py-3 hover:bg-red-50 transition"
        onClick={onCancelar}
      >
        Cancelar
      </button>

      {/* Última venta */}
      {ultimaVenta && (
        <div className="bg-gray-100 rounded border border-gray-300 p-3 text-sm text-gray-800 space-y-2">
          <div>
            Última venta: #{ultimaVenta.id} – Estado:{" "}
            <strong className="uppercase">{ultimaVenta.estado}</strong>
          </div>
          <div>Total: {fmtMoney(ultimaVenta.total)}</div>

          {ultimaVenta.estado === "CONFIRMADA" && (
            <button
              className="bg-yellow-400 hover:bg-yellow-500 text-black font-medium rounded px-3 py-2 text-sm"
              onClick={() => onAnularUltima(ultimaVenta.id)}
            >
              Anular Última Venta
            </button>
          )}
        </div>
      )}

      {/* Link a Productos */}
      <div className="text-center text-sm text-gray-700">
        <a
          className="inline-flex items-center gap-2 text-blue-600 hover:underline"
          href="/"
        >
          <span role="img" aria-label="productos">📦</span>
          Ir a Productos
        </a>
      </div>
    </div>
  );
}
