// frontend/src/pages/Ventas.jsx
import { useEffect, useState } from "react";
import { createSale, confirmSale, annulSale } from "../services/sales.js";
import { fetchProductos } from "../services/products.js";
import ResumenDeVenta from "./ResumenDeVenta.jsx";

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

  const handleBuscarKeyDown = (e) => {
    if (e.key === "Enter") {
      const term = busqueda.trim().toLowerCase();
      if (!term) return;
      const prod = productos.find(
        (p) =>
          p.nombre.toLowerCase().includes(term) ||
          String(p.codigo || "").toLowerCase() === term
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
      const idx = prev.findIndex((r) => r.id === prod.id);
      if (idx !== -1) {
        const updated = [...prev];
        const row = { ...updated[idx] };
        row.cantidad = row.cantidad + 1;
        row.subtotal = row.cantidad * row.precio;
        updated[idx] = row;
        return updated;
      }
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

  const confirmarVentaHandler = async () => {
    if (!carrito.length) {
      alert("Agregá productos antes de confirmar.");
      return;
    }

    setLoadingVenta(true);
    try {
      const payload = {
        fecha: new Date().toISOString(),
        detalles: carrito.map((item, idx) => ({
          producto: item.id,
          cantidad: item.cantidad,
          precio_unitario: item.precio,
          renglon: idx + 1,
        })),
      };

      // crear venta
      const crearResp = await createSale(payload);
      const ventaCreada = crearResp.data;
      const ventaId = ventaCreada.id;

      // confirmar venta
      const confirmarResp = await confirmSale(ventaId);
      const ventaConfirmada = confirmarResp.data;

      setUltimaVenta({
        id: ventaConfirmada.id,
        estado: ventaConfirmada.estado,
        total: ventaConfirmada.total,
      });

      setCarrito([]);

      alert("¡Venta confirmada con éxito!");
    } catch (err) {
      console.error("Error confirmando venta", err);
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.estado ||
        "No se pudo confirmar la venta.";
      alert(msg);
    } finally {
      setLoadingVenta(false);
    }
  };

  const anularUltimaVenta = async () => {
    if (!ultimaVenta || !ultimaVenta.id) return;
    if (!window.confirm("¿Seguro que querés anular la última venta?")) return;

    setAnulando(true);
    try {
      const resp = await annulSale(ultimaVenta.id);
      const ventaAnulada = resp.data;
      setUltimaVenta({
        id: ventaAnulada.id,
        estado: ventaAnulada.estado,
        total: ventaAnulada.total,
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
                        ${item.precio.toLocaleString("es-AR", {
                          minimumFractionDigits: 2,
                        })}
                      </td>
                      <td style={{ whiteSpace: "nowrap" }}>
                        ${item.subtotal.toLocaleString("es-AR", {
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
