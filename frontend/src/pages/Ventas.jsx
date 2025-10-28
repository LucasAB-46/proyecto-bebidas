import { useEffect, useState } from "react";
import { createSale, confirmSale, annulSale } from "../services/sales.js";
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
  // 1. crea la venta borrador en /ventas/
  // 2. confirma en /ventas/{id}/confirmar/
  const confirmarVentaHandler = async () => {
    if (!carrito.length) {
      alert("Agregá productos antes de confirmar.");
      return;
    }

    setLoadingVenta(true);
    try {
      console.log("[VENTA] Paso 1: crear venta borrador...");
      const payload = {
        fecha: new Date().toISOString(),
        detalles: carrito.map((item, idx) => ({
          producto: item.id,
          cantidad: item.cantidad,
          precio_unitario: item.precio,
          renglon: idx + 1,
        })),
      };

      const crearResp = await createSale(payload);
      console.log("[VENTA] create OK", crearResp);

      // en Railway estamos devolviendo algo tipo:
      // { id, estado, total }  -> PERO si por algún motivo falla el serializer
      // puede venir vacío. Entonces hacemos fallback seguro.
      const ventaId = crearResp?.data?.id;
      const ventaEstado = crearResp?.data?.estado ?? "borrador";
      const ventaTotal = crearResp?.data?.total ?? totalVenta;

      if (!ventaId) {
        console.error("No vino id en la venta creada", crearResp);
        alert("No se pudo crear la venta (sin ID).");
        setLoadingVenta(false);
        return;
      }

      console.log("[VENTA] Paso 2: confirmar venta id", ventaId);
      const confirmarResp = await confirmSale(ventaId);
      console.log("[VENTA] confirmar OK", confirmarResp);

      // puede venir vacío confirmarResp.data → fallback
      const finalData = confirmarResp?.data || {};
      const finalId = finalData.id ?? ventaId;
      const finalEstado =
        finalData.estado ?? ventaEstado ?? "confirmada";
      const finalTotal = finalData.total ?? ventaTotal ?? 0;

      // guardo como últimaVenta para el panel resumen
      setUltimaVenta({
        id: finalId,
        estado: finalEstado,
        total: finalTotal,
      });

      // limpio carrito
      setCarrito([]);

      alert("¡Venta confirmada con éxito!");
    } catch (err) {
      console.error("ERROR en confirmar flujo:", err);
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.estado ||
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
      const resp = await annulSale(ultimaVenta.id);
      const ventaAnulada = resp.data || {};
      setUltimaVenta({
        id: ventaAnulada.id ?? ultimaVenta.id,
        estado: ventaAnulada.estado ?? "anulada",
        total: ventaAnulada.total ?? ultimaVenta.total ?? 0,
      });
    } catch (err) {
      console.error("Error anulando", err);
      alert(
        err.response?.data?.detail ||
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
          placeholder="Escriba código o nombre..."
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
            onConfirmar={confirmarVentaHandler}
            onAnularUltima={anularUltimaVenta}
            onCancelar={() => setCarrito([])}
          />
        </div>
      </div>
    </div>
  );
}
