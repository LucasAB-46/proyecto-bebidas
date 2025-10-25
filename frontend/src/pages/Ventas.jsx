import { useEffect, useState } from "react";
import { createSale, confirmSale, annulSale } from "../services/sales.js";
import { fetchProductos } from "../services/products.js";
import ResumenDeVenta from "../components/ResumenDeVenta.jsx";

export default function Ventas() {
  // estado UI / data
  const [busqueda, setBusqueda] = useState("");
  const [productos, setProductos] = useState([]);
  const [carrito, setCarrito] = useState([]); // [{id,nombre,precio,cantidad,subtotal}]
  const [loadingVenta, setLoadingVenta] = useState(false);

  const [ultimaVenta, setUltimaVenta] = useState(null); // {id, estado, total}
  const [anulando, setAnulando] = useState(false);

  // cargar productos al montar
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

  // helper: agregar producto existente al carrito
  const agregarAlCarrito = (prod) => {
    const precioBase = Number(prod.precio_venta ?? prod.precio ?? 0);

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
          precio: precioBase,
          cantidad: 1,
          subtotal: precioBase,
        },
      ];
    });
  };

  // buscar con Enter
  const handleBuscarKeyDown = (e) => {
    if (e.key !== "Enter") return;
    const term = busqueda.trim().toLowerCase();
    if (!term) return;

    const prod = productos.find(
      (p) =>
        p.nombre?.toLowerCase().includes(term) ||
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
  };

  // actualizar cantidad de una fila del carrito
  const actualizarCantidad = (idProd, nuevaCantidad) => {
    setCarrito((prev) =>
      prev.map((item) => {
        if (item.id !== idProd) return item;
        const cantNum = Number(nuevaCantidad);
        const cantidadOk = cantNum > 0 && !Number.isNaN(cantNum) ? cantNum : 1;
        return {
          ...item,
          cantidad: cantidadOk,
          subtotal: cantidadOk * item.precio,
        };
      })
    );
  };

  // quitar un producto del carrito
  const quitarDelCarrito = (idProd) => {
    setCarrito((prev) => prev.filter((item) => item.id !== idProd));
  };

  // total venta
  const totalVenta = carrito.reduce((acc, it) => acc + it.subtotal, 0);

  // flujo de confirmar venta
  const confirmarVentaHandler = async () => {
    if (!carrito.length) {
      alert("Agregá productos antes de confirmar.");
      return;
    }

    setLoadingVenta(true);
    try {
      // payload para backend VentaWriteSerializer
      const payload = {
        fecha: new Date().toISOString(),
        detalles: carrito.map((item, idx) => ({
          producto: item.id,
          cantidad: item.cantidad,
          precio_unitario: item.precio,
          renglon: idx + 1,
          bonif: 0,
          impuestos: 0,
        })),
      };

      // 1) crear venta borrador
      const crearResp = await createSale(payload);
      const ventaCreada = crearResp.data;
      const ventaId = ventaCreada.id;

      // 2) confirmar venta
      const confirmarResp = await confirmSale(ventaId);
      const ventaConfirmada = confirmarResp.data;

      setUltimaVenta({
        id: ventaConfirmada.id,
        estado: ventaConfirmada.estado,
        total: ventaConfirmada.total,
      });

      // limpiar carrito
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

  // anular última venta
  const anularUltimaVenta = async () => {
    if (!ultimaVenta || !ultimaVenta.id) return;
    if (
      !window.confirm(
        "¿Seguro que querés anular la última venta? Esto va a devolver stock."
      )
    )
      return;

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
      console.error("Error anulando venta", err);
      alert(
        err.response?.data?.detail ||
          "No se pudo anular la venta (puede que ya esté anulada)"
      );
    } finally {
      setAnulando(false);
    }
  };

  // render
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
          Escribí parte del nombre, código interno o código de barras y presioná
          Enter para agregar.
        </div>
      </div>

      <div className="row">
        {/* TABLA CARRITO */}
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

        {/* PANEL RESUMEN DERECHA */}
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
