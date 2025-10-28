import { useEffect, useState } from "react";
import api from "../api/client"; // ⬅ usamos el cliente axios centralizado
import { fetchProductos } from "../services/products.js";

// --- componente resumen lateral ---
function ResumenDeVenta({
  total,
  loading,
  ultimaVenta,
  anulando,
  onConfirmar,
  onCancelar,
  onAnularUltima,
}) {
  return (
    <div className="card shadow-sm">
      <div className="card-body">
        <h3 className="card-title fw-bold mb-4">Resumen de la Venta</h3>

        <div className="d-flex justify-content-between align-items-start mb-4">
          <div
            className="text-uppercase fw-semibold"
            style={{ fontSize: "1.1rem" }}
          >
            TOTAL
          </div>
          <div
            className="fw-bold text-nowrap"
            style={{ fontSize: "2rem", lineHeight: 1 }}
          >
            $
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

              {ultimaVenta.estado === "CONFIRMADA" ||
              ultimaVenta.estado === "confirmada" ? (
                <button
                  className="btn btn-warning w-100"
                  disabled={anulando}
                  onClick={onAnularUltima}
                >
                  {anulando ? "Anulando..." : "Anular Última Venta"}
                </button>
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

// helper: base64 -> Blob
function base64ToBlob(b64, mime) {
  const byteChars = atob(b64);
  const byteNums = new Array(byteChars.length);
  for (let i = 0; i < byteChars.length; i++) {
    byteNums[i] = byteChars.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNums);
  return new Blob([byteArray], { type: mime });
}

// --- pantalla principal ---
export default function Ventas() {
  // ---------------- state ----------------
  const [busqueda, setBusqueda] = useState("");
  const [productos, setProductos] = useState([]);
  const [carrito, setCarrito] = useState([]); // [{id, nombre, precio, cantidad, subtotal}]
  const [loadingVenta, setLoadingVenta] = useState(false);

  // para el panel de "última venta"
  const [ultimaVenta, setUltimaVenta] = useState(null); // {id, estado, total}
  const [anulando, setAnulando] = useState(false);

  // si querés mostrar el QR en el futuro podés hacer:
  // const [qrBase64, setQrBase64] = useState(null);

  // ---------------- carga inicial productos ----------------
  useEffect(() => {
    fetchProductos({ search: "", page_size: 100 })
      .then((res) => {
        const data = Array.isArray(res.data.results)
          ? res.data.results
          : res.data;
        setProductos(data || []);
      })
      .catch((err) => {
        console.error("Error cargando productos", err);
        alert("No se pudieron cargar los productos.");
      });
  }, []);

  // ---------------- helpers carrito ----------------
  // busca producto por texto (enter) y lo agrega con cantidad 1
  const handleBuscarKeyDown = (e) => {
    if (e.key === "Enter") {
      const term = busqueda.trim().toLowerCase();
      if (!term) return;
      const prod = productos.find(
        (p) =>
          p.nombre.toLowerCase().includes(term) ||
          String(p.codigo || "").toLowerCase() === term ||
          String(p.codigo_barras || p.barcode || "")
            .toLowerCase()
            .includes(term)
      );
      if (!prod) {
        alert("Producto no encontrado.");
        return;
      }
      agregarAlCarrito(prod);
      setBusqueda("");
    }
  };

  const agregarAlCarrito = (prod) => {
    setCarrito((prev) => {
      // si ya está en carrito, sumo 1
      const idx = prev.findIndex((r) => r.id === prod.id);
      if (idx !== -1) {
        const updated = [...prev];
        const row = { ...updated[idx] };
        row.cantidad = row.cantidad + 1;
        row.subtotal = row.cantidad * row.precio;
        updated[idx] = row;
        return updated;
      }
      // si no está, lo agrego
      return [
        ...prev,
        {
          id: prod.id,
          nombre: prod.nombre,
          precio: Number(prod.precio_venta ?? prod.precio ?? 0),
          cantidad: 1,
          subtotal: Number(prod.precio_venta ?? prod.precio ?? 0),
        },
      ];
    });
  };

  const actualizarCantidad = (idProd, nuevaCantidad) => {
    setCarrito((prev) => {
      const updated = prev.map((item) => {
        if (item.id === idProd) {
          const cantNum = Number(nuevaCantidad);
          return {
            ...item,
            cantidad: cantNum,
            subtotal: cantNum * item.precio,
          };
        }
        return item;
      });
      return updated;
    });
  };

  const quitarDelCarrito = (idProd) => {
    setCarrito((prev) => prev.filter((item) => item.id !== idProd));
  };

  const totalVenta = carrito.reduce((acc, it) => acc + it.subtotal, 0);

  // ---------------- flujo venta ----------------
  // Nuevo flujo FINAL:
  // 1. POST /api/ventas/  -> crea en estado BORRADOR, devuelve { id, estado, total }
  // 2. POST /api/ventas/{id}/confirmar/ -> descuenta stock, genera ticket y qr
  //    devuelve { venta: {...}, qr_base64, ticket_pdf_base64 }
  const handleConfirmarVenta = async () => {
    if (!carrito.length) {
      alert("Agregá productos antes de confirmar.");
      return;
    }

    setLoadingVenta(true);
    try {
      // payload que espera el backend
      const payload = {
        fecha: new Date().toISOString(),
        detalles: carrito.map((item, idx) => ({
          producto: item.id, // 👈 ID numérico del producto
          cantidad: item.cantidad,
          precio_unitario: item.precio,
          renglon: idx + 1,
        })),
      };

      // 1) crear venta borrador
      console.log("[VENTA] Paso 1: crear venta borrador...");
      const resCreate = await api.post("/ventas/", payload);
      console.log("[VENTA] create OK", resCreate.data);

      const nuevaVentaId = resCreate.data.id;
      if (!nuevaVentaId) {
        console.error("No vino id en la venta creada", resCreate.data);
        alert("Error interno: falta ID de la venta creada.");
        return;
      }

      // 2) confirmar venta (descuenta stock + genera PDF+QR)
      console.log("[VENTA] Paso 2: confirmar venta id", nuevaVentaId);
      const resConf = await api.post(`/ventas/${nuevaVentaId}/confirmar/`);
      console.log("[VENTA] confirmar OK", resConf.data);

      const { venta, qr_base64, ticket_pdf_base64 } = resConf.data;

      // guardamos la venta confirmada como "última venta"
      setUltimaVenta({
        id: venta.id,
        estado: venta.estado,
        total: venta.total,
      });

      // Mostrar ticket PDF en pestaña nueva
      if (ticket_pdf_base64) {
        const pdfBlob = base64ToBlob(ticket_pdf_base64, "application/pdf");
        const pdfUrl = URL.createObjectURL(pdfBlob);
        window.open(pdfUrl, "_blank");
      }

      // Opcional: podríamos guardar qr_base64 en un modal
      // setQrBase64(qr_base64);

      // limpio carrito
      setCarrito([]);

      alert("¡Venta confirmada con éxito!");
    } catch (err) {
      console.error("ERROR en confirmar flujo:", err);
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.estado ||
        "No se pudo confirmar la venta.";
      alert(msg);
    } finally {
      setLoadingVenta(false);
    }
  };

  // anular última venta confirmada
  const anularUltimaVenta = async () => {
    if (!ultimaVenta || !ultimaVenta.id) return;
    if (!window.confirm("¿Seguro que querés anular la última venta?")) return;

    setAnulando(true);
    try {
      const resp = await api.post(`/ventas/${ultimaVenta.id}/anular/`);
      const ventaAnulada = resp.data;
      setUltimaVenta({
        id: ventaAnulada.id,
        estado: ventaAnulada.estado,
        total: ventaAnulada.total,
      });
    } catch (err) {
      console.error("Error anulando", err);
      alert(
        err?.response?.data?.detail ||
          "No se pudo anular la venta (puede que ya esté ANULADA)"
      );
    } finally {
      setAnulando(false);
    }
  };

  // ---------------- render ----------------
  return (
    <div className="container mt-4">
      <h1 className="mb-4">Punto de Venta</h1>

      {/* BUSCADOR */}
      <div className="mb-3">
        <label className="form-label fw-bold">Buscar Producto</label>
        <input
          className="form-control form-control-lg"
          placeholder="Escribí código o nombre..."
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          onKeyDown={handleBuscarKeyDown}
        />
        <div className="form-text">
          Escribí parte del nombre o el código y presioná Enter para agregar.
        </div>
      </div>

      {/* CARRITO + RESUMEN */}
      <div className="row">
        {/* tabla carrito */}
        <div className="col-12 col-lg-8 mb-4">
          <h2>Carrito</h2>
          <div className="table-responsive border rounded">
            <table className="table mb-0 align-middle">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cantidad</th>
                  <th>Precio Unit.</th>
                  <th>Subtotal</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {carrito.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center py-4">
                      El carrito está vacío
                    </td>
                  </tr>
                ) : (
                  carrito.map((item) => (
                    <tr key={item.id}>
                      <td style={{ minWidth: "150px" }}>{item.nombre}</td>
                      <td style={{ width: "120px" }}>
                        <input
                          type="number"
                          className="form-control"
                          min="1"
                          value={item.cantidad}
                          onChange={(e) =>
                            actualizarCantidad(item.id, e.target.value)
                          }
                        />
                      </td>
                      <td style={{ whiteSpace: "nowrap" }}>
                        $
                        {item.precio.toLocaleString("es-AR", {
                          minimumFractionDigits: 2,
                        })}
                      </td>
                      <td style={{ whiteSpace: "nowrap" }}>
                        $
                        {item.subtotal.toLocaleString("es-AR", {
                          minimumFractionDigits: 2,
                        })}
                      </td>
                      <td>
                        <button
                          className="btn btn-outline-dark btn-sm"
                          onClick={() => quitarDelCarrito(item.id)}
                        >
                          Quitar
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* panel resumen derecha */}
        <div className="col-12 col-lg-4">
          <ResumenDeVenta
            total={totalVenta}
            loading={loadingVenta}
            ultimaVenta={ultimaVenta}
            anulando={anulando}
            onConfirmar={handleConfirmarVenta}
            onAnularUltima={anularUltimaVenta}
            onCancelar={() => setCarrito([])}
          />
        </div>
      </div>
    </div>
  );
}
