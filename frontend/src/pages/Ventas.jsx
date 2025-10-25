import { useEffect, useState } from "react";
import api from "../api/client.jsx";
import ResumenDeVenta from "../components/ResumenDeVenta.jsx";

// Util: formatear $ con separador miles
function fmtMoney(n) {
  return `$${Number(n || 0).toLocaleString("es-AR")}`;
}

export default function Ventas() {
  // --------------------------
  // Estados principales
  // --------------------------
  const [busqueda, setBusqueda] = useState("");
  const [sugeridos, setSugeridos] = useState([]); // resultados live de búsqueda producto
  const [carrito, setCarrito] = useState([]); // [{id, nombre, precio_venta, cantidad}]
  const [ultimaVenta, setUltimaVenta] = useState(null); // {id, estado, total}
  const [flashOk, setFlashOk] = useState(null); // {numero, total} para banner verde
  const [cargandoConfirmar, setCargandoConfirmar] = useState(false);

  // --------------------------
  // Derivados
  // --------------------------
  const totalVenta = carrito.reduce(
    (acc, item) => acc + item.precio_venta * item.cantidad,
    0
  );

  // --------------------------
  // Efecto para auto-ocultar el banner verde
  // --------------------------
  useEffect(() => {
    if (!flashOk) return;
    const t = setTimeout(() => setFlashOk(null), 4000);
    return () => clearTimeout(t);
  }, [flashOk]);

  // --------------------------
  // Buscar productos al tipear
  // --------------------------
  useEffect(() => {
    if (!busqueda || busqueda.trim().length < 1) {
      setSugeridos([]);
      return;
    }

    const ctrl = new AbortController();
    async function run() {
      try {
        const resp = await api.get(
          `/catalogo/productos/?search=${encodeURIComponent(
            busqueda
          )}&page_size=5`,
          { signal: ctrl.signal }
        );
        // el backend devuelve un paginado tipo {results:[...]}
        const lista = resp.data.results || resp.data || [];
        setSugeridos(lista);
      } catch (err) {
        console.error("Error buscando productos", err);
      }
    }
    run();

    return () => ctrl.abort();
  }, [busqueda]);

  // --------------------------
  // Agregar producto al carrito
  // --------------------------
  function agregarAlCarrito(prod) {
    // prod viene del backend. asumimos:
    // prod.id, prod.nombre, prod.precio_venta (o como se llame tu campo de venta)
    // ⚠ si tu campo no es "precio_venta", cambialo acá y en el render del carrito
    const existente = carrito.find((i) => i.id === prod.id);
    if (existente) {
      setCarrito((prev) =>
        prev.map((i) =>
          i.id === prod.id
            ? { ...i, cantidad: i.cantidad + 1 }
            : i
        )
      );
    } else {
      setCarrito((prev) => [
        ...prev,
        {
          id: prod.id,
          nombre: prod.nombre,
          precio_venta: Number(prod.precio_venta ?? prod.precio ?? 0), // <-- ajustar si tu campo es distinto
          cantidad: 1,
        },
      ]);
    }
    setBusqueda("");
    setSugeridos([]);
  }

  // --------------------------
  // Cambiar cantidad en carrito
  // --------------------------
  function cambiarCantidad(idProd, nuevaCant) {
    if (!nuevaCant || nuevaCant <= 0) return;
    setCarrito((prev) =>
      prev.map((i) =>
        i.id === idProd
          ? { ...i, cantidad: nuevaCant }
          : i
      )
    );
  }

  // --------------------------
  // Eliminar item del carrito
  // --------------------------
  function quitarDelCarrito(idProd) {
    setCarrito((prev) => prev.filter((i) => i.id !== idProd));
  }

  // --------------------------
  // Cancelar venta (vacía carrito COMPLETO)
  // --------------------------
  function handleCancelarVenta() {
    setCarrito([]);
  }

  // --------------------------
  // Confirmar venta:
  //  1. crea venta borrador
  //  2. confirma en backend
  //  3. limpia carrito
  //  4. guarda ultimaVenta
  //  5. arma flashOk
  // --------------------------
  async function handleConfirmarVenta() {
    if (carrito.length === 0) return;

    setCargandoConfirmar(true);
    try {
      // armamos payload según lo que espera tu backend en /ventas/
      // usamos campos:
      //   producto -> id del producto
      //   cantidad
      //   precio_unitario -> precio_venta
      const detallesPayload = carrito.map((item, idx) => ({
        renglon: idx + 1,
        producto: item.id,
        cantidad: item.cantidad,
        precio_unitario: item.precio_venta,
      }));

      // Paso 1: crear venta en borrador
      const crearResp = await api.post("/ventas/", {
        detalles: detallesPayload,
      });
      const ventaCreada = crearResp.data; // {id, total, ...}

      // Paso 2: confirmar
      const confirmarResp = await api.post(
        `/ventas/${ventaCreada.id}/confirmar/`
      );
      const ventaConfirmada = confirmarResp.data; // {id, estado:'CONFIRMADA', total,...}

      // Paso 3: limpiar carrito
      setCarrito([]);

      // Paso 4: guardar ultimaVenta
      setUltimaVenta({
        id: ventaConfirmada.id,
        estado: ventaConfirmada.estado,
        total: ventaConfirmada.total,
      });

      // Paso 5: banner verde
      setFlashOk({
        numero: ventaConfirmada.id,
        total: ventaConfirmada.total,
      });
    } catch (err) {
      console.error("Error al confirmar venta", err);
      // Podés meter un alert si querés feedback inmediato
      // alert("Ocurrió un error al confirmar la venta");
    } finally {
      setCargandoConfirmar(false);
    }
  }

  // --------------------------
  // Anular última venta
  // --------------------------
  async function handleAnularUltimaVenta(idVenta) {
    if (!idVenta) return;
    try {
      const resp = await api.post(`/ventas/${idVenta}/anular/`);
      const ventaAnulada = resp.data; // {id, estado: 'ANULADA', total,...}

      setUltimaVenta({
        id: ventaAnulada.id,
        estado: ventaAnulada.estado,
        total: ventaAnulada.total,
      });
    } catch (err) {
      console.error("Error al anular la venta", err);
      // alert("No se pudo anular la venta");
    }
  }

  // --------------------------
  // Render
  // --------------------------
  return (
    <div className="p-4 lg:p-8">
      <header className="mb-6">
        <h1 className="text-3xl font-semibold">Punto de Venta</h1>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* IZQUIERDA: buscador + carrito */}
        <section>
          {/* Buscar Producto */}
          <div className="mb-4">
            <label
              htmlFor="buscador"
              className="block text-lg font-medium text-gray-900 mb-2"
            >
              Buscar Producto
            </label>
            <input
              id="buscador"
              className="w-full border rounded px-3 py-2 text-base outline-none focus:ring focus:ring-blue-300"
              placeholder="Escriba código o nombre..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
            {/* Lista sugerida */}
            {sugeridos.length > 0 && (
              <ul className="border rounded mt-2 bg-white shadow-md max-h-60 overflow-y-auto text-sm">
                {sugeridos.map((p) => (
                  <li
                    key={p.id}
                    className="px-3 py-2 flex justify-between items-center hover:bg-blue-50 cursor-pointer"
                    onClick={() => agregarAlCarrito(p)}
                  >
                    <span className="text-gray-800">
                      {p.nombre} {/* <-- ajustar si tu backend usa otro campo */}
                    </span>
                    <span className="text-gray-500">
                      {fmtMoney(p.precio_venta ?? p.precio ?? 0)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Carrito */}
          <div>
            <h2 className="text-2xl font-semibold mb-3">Carrito</h2>

            <div className="overflow-x-auto border rounded">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-gray-700 text-left">
                  <tr>
                    <th className="px-3 py-2 font-semibold">Producto</th>
                    <th className="px-3 py-2 font-semibold">Cantidad</th>
                    <th className="px-3 py-2 font-semibold">Precio Unit.</th>
                    <th className="px-3 py-2 font-semibold">Subtotal</th>
                    <th className="px-3 py-2 font-semibold"></th>
                  </tr>
                </thead>
                <tbody>
                  {carrito.length === 0 ? (
                    <tr>
                      <td
                        className="px-3 py-4 text-center text-gray-500"
                        colSpan={5}
                      >
                        El carrito está vacío
                      </td>
                    </tr>
                  ) : (
                    carrito.map((item) => (
                      <tr
                        key={item.id}
                        className="border-t last:border-b text-gray-800"
                      >
                        <td className="px-3 py-2">
                          {item.nombre}
                        </td>

                        <td className="px-3 py-2">
                          <input
                            type="number"
                            min="1"
                            className="w-20 border rounded px-2 py-1 text-sm"
                            value={item.cantidad}
                            onChange={(e) =>
                              cambiarCantidad(
                                item.id,
                                Number(e.target.value)
                              )
                            }
                          />
                        </td>

                        <td className="px-3 py-2 whitespace-nowrap">
                          {fmtMoney(item.precio_venta)}
                        </td>

                        <td className="px-3 py-2 whitespace-nowrap font-medium">
                          {fmtMoney(item.precio_venta * item.cantidad)}
                        </td>

                        <td className="px-3 py-2 text-right">
                          <button
                            className="text-red-600 hover:underline text-sm"
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
        </section>

        {/* DERECHA: resumen / total / botones / ultima venta */}
        <aside className="border rounded p-4 shadow-sm bg-white flex flex-col gap-4">

          {/* Banner verde de venta confirmada */}
          {flashOk && (
            <div className="rounded p-3 text-sm font-medium text-green-900 bg-green-100 border border-green-300">
              ✅ Venta #{flashOk.numero} confirmada (
              {fmtMoney(flashOk.total)})
            </div>
          )}

          <ResumenDeVenta
            total={totalVenta}
            ultimaVenta={ultimaVenta}
            onConfirmar={handleConfirmarVenta}
            onCancelar={handleCancelarVenta}
            onAnularUltima={handleAnularUltimaVenta}
            cargandoConfirmar={cargandoConfirmar}
          />
        </aside>
      </div>
    </div>
  );
}
