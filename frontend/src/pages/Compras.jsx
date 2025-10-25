import { useEffect, useState } from "react";
import { fetchProductos, listSuppliers } from "../services/products.js";
import {
  createPurchase,
  confirmPurchase,
  annulPurchase,
} from "../services/purchases.js";

// ---- búsqueda de productos (local + fallback remoto) ----
async function buscarProductoPorTerm(term, productosCache) {
  const t = term.trim().toLowerCase();
  if (!t) return null;

  // 1) buscar en cache local
  const matchLocal = productosCache.find((p) => {
    const nombreOk = p.nombre?.toLowerCase().includes(t);
    const codigoOk = String(p.codigo || "").toLowerCase().includes(t);
    const barcodeOk = String(p.codigo_barras || p.barcode || "")
      .toLowerCase()
      .includes(t);
    return nombreOk || codigoOk || barcodeOk;
  });
  if (matchLocal) return matchLocal;

  // 2) fallback remoto
  try {
    const resp = await fetchProductos({ search: term, page_size: 10 });
    const data = Array.isArray(resp.data.results)
      ? resp.data.results
      : resp.data;
    if (data && data.length > 0) return data[0];
  } catch (e) {
    console.error("buscarProductoPorTerm fallback compras", e);
  }

  return null;
}

export default function Compras() {
  // -------- state global --------
  const [productos, setProductos] = useState([]);
  const [proveedores, setProveedores] = useState([]);

  // elección usuario
  const [proveedorId, setProveedorId] = useState("");
  const [busqueda, setBusqueda] = useState("");

  // carrito de compra
  // [{id, nombre, cantidad, costo_unitario, bonif, impuestos, subtotal}]
  const [carrito, setCarrito] = useState([]);

  // totales
  const [subtotal, setSubtotal] = useState(0);
  const [totalImp, setTotalImp] = useState(0);
  const [totalBonif, setTotalBonif] = useState(0);
  const [totalFinal, setTotalFinal] = useState(0);

  // control proceso / feedback UI
  const [loadingCompra, setLoadingCompra] = useState(false);
  const [ultimaCompra, setUltimaCompra] = useState(null); // {id, estado, total, proveedor_nombre?}
  const [anulando, setAnulando] = useState(false);

  // -------- carga inicial: productos + proveedores --------
  useEffect(() => {
    // productos (stock actual, precios base, etc.)
    fetchProductos({ search: "", page_size: 100 })
      .then((res) => {
        const data = Array.isArray(res.data.results)
          ? res.data.results
          : res.data;
        setProductos(data || []);
      })
      .catch((err) => {
        console.error("Error cargando productos (Compras)", err);
        alert("No se pudieron cargar productos para Compras.");
      });

    // proveedores
    listSuppliers()
      .then((res) => {
        const data = Array.isArray(res.data.results)
          ? res.data.results
          : res.data;
        setProveedores(data || []);
        // No autoselecciono. Que el usuario elija.
      })
      .catch((err) => {
        console.error("Error cargando proveedores", err);
        alert("No se pudieron cargar los proveedores.");
      });
  }, []);

  // -------- recálculo autom. de totales --------
  useEffect(() => {
    let sub = 0;
    let imp = 0;
    let bon = 0;

    carrito.forEach((item) => {
      sub += item.cantidad * item.costo_unitario;
      imp += item.impuestos;
      bon += item.bonif;
    });

    setSubtotal(sub);
    setTotalImp(imp);
    setTotalBonif(bon);
    setTotalFinal(sub - bon + imp);
  }, [carrito]);

  // -------- helpers carrito --------
  const agregarAlCarrito = (prod) => {
    const costoBase = Number(
      prod.precio_costo ??
        prod.costo ??
        prod.precio_venta ??
        prod.precio ??
        0
    );

    setCarrito((prev) => {
      const found = prev.find((r) => r.id === prod.id);
      if (found) {
        // si ya existe en carrito, sumar 1
        return prev.map((row) =>
          row.id === prod.id
            ? {
                ...row,
                cantidad: row.cantidad + 1,
                subtotal:
                  (row.cantidad + 1) * row.costo_unitario -
                  row.bonif +
                  row.impuestos,
              }
            : row
        );
      }

      // si no existe, agregarlo
      return [
        ...prev,
        {
          id: prod.id,
          nombre: prod.nombre,
          cantidad: 1,
          costo_unitario: costoBase,
          bonif: 0,
          impuestos: 0,
          subtotal: costoBase,
        },
      ];
    });
  };

  const handleBuscarKeyDown = async (e) => {
    if (e.key !== "Enter") return;
    const term = busqueda.trim();
    if (!term) return;

    const prod = await buscarProductoPorTerm(term, productos);
    if (!prod) {
      alert("Producto no encontrado.");
      return;
    }

    agregarAlCarrito(prod);
    setBusqueda("");
  };

  const actualizarItem = (idProd, field, valueRaw) => {
    setCarrito((prev) =>
      prev.map((item) => {
        if (item.id !== idProd) return item;

        const n = Number(valueRaw);

        switch (field) {
          case "cantidad": {
            const cantidad = !Number.isNaN(n) && n > 0 ? n : 1;
            return {
              ...item,
              cantidad,
              subtotal:
                cantidad * item.costo_unitario -
                item.bonif +
                item.impuestos,
            };
          }

          case "costo_unitario": {
            const costo = !Number.isNaN(n) && n >= 0 ? n : 0;
            return {
              ...item,
              costo_unitario: costo,
              subtotal:
                item.cantidad * costo -
                item.bonif +
                item.impuestos,
            };
          }

          case "bonif": {
            const bonif = !Number.isNaN(n) && n >= 0 ? n : 0;
            return {
              ...item,
              bonif,
              subtotal:
                item.cantidad * item.costo_unitario -
                bonif +
                item.impuestos,
            };
          }

          case "impuestos": {
            const impuestos = !Number.isNaN(n) && n >= 0 ? n : 0;
            return {
              ...item,
              impuestos,
              subtotal:
                item.cantidad * item.costo_unitario -
                item.bonif +
                impuestos,
            };
          }

          default:
            return item;
        }
      })
    );
  };

  const quitarDelCarrito = (idProd) => {
    setCarrito((prev) => prev.filter((it) => it.id !== idProd));
  };

  // -------- flujo compra DEFINITIVO --------
  const confirmarCompraHandler = async () => {
    if (!carrito.length) {
      alert("Agregá productos antes de confirmar la compra.");
      return;
    }
    if (!proveedorId) {
      alert("Seleccioná un proveedor antes de confirmar.");
      return;
    }

    setLoadingCompra(true);
    try {
      // Payload 100% alineado al backend (CompraWriteSerializer):
      // - proveedor (FK)
      // - fecha
      // - detalles -> [ {producto, cantidad, costo_unitario, bonif, impuestos, renglon} ... ]
      //
      // local_id NO lo mandamos desde el front:
      //   la ViewSet lo obtiene del header X-Local-ID que YA mandamos en api/client.jsx
      //   y hace serializer.save(local_id=eseLocal).
      //
      const payload = {
        proveedor: Number(proveedorId),
        fecha: new Date().toISOString(),
        detalles: carrito.map((item, idx) => ({
          producto: item.id,
          cantidad: item.cantidad,
          costo_unitario: item.costo_unitario,
          bonif: item.bonif,
          impuestos: item.impuestos,
          renglon: idx + 1,
        })),
      };

      // 1) crear compra en estado BORRADOR
      const crearResp = await createPurchase(payload);
      const compraCreada = crearResp.data; // {id, estado: "borrador", ...}
      const compraId = compraCreada.id;

      // 2) confirmar compra (esto actualiza stock y marca estado=CONFIRMADA)
      const confirmarResp = await confirmPurchase(compraId);
      const compraConfirmada = confirmarResp.data;

      // persistimos para mostrar en panel
      setUltimaCompra({
        id: compraConfirmada.id,
        estado: compraConfirmada.estado,
        total: compraConfirmada.total,
        proveedor_nombre:
          compraConfirmada.proveedor_nombre ||
          compraConfirmada.proveedor ||
          proveedorId,
      });

      // limpiamos carrito
      setCarrito([]);

      alert("Compra confirmada con éxito. El stock fue actualizado.");
    } catch (err) {
      console.error("Error confirmando compra", err);
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.estado ||
        "No se pudo confirmar la compra.";
      alert(msg);
    } finally {
      setLoadingCompra(false);
    }
  };

  const anularUltimaCompra = async () => {
    if (!ultimaCompra || !ultimaCompra.id) return;
    if (
      !window.confirm(
        "¿Seguro que querés anular la última compra? Esto revertirá el stock."
      )
    ) {
      return;
    }

    setAnulando(true);
    try {
      const resp = await annulPurchase(ultimaCompra.id);
      const compraAnulada = resp.data;
      setUltimaCompra({
        id: compraAnulada.id,
        estado: compraAnulada.estado,
        total: compraAnulada.total,
        proveedor_nombre:
          compraAnulada.proveedor_nombre ||
          compraAnulada.proveedor ||
          ultimaCompra.proveedor_nombre,
      });
    } catch (err) {
      console.error("Error anulando compra", err);
      alert(
        err.response?.data?.detail ||
          "No se pudo anular la compra (puede que ya esté ANULADA)"
      );
    } finally {
      setAnulando(false);
    }
  };

  // -------- render --------
  return (
    <div className="container mt-4">
      <h1 className="mb-4">Ingreso de Compras</h1>

      {/* PROVEEDOR (dato obligatorio de negocio) */}
      <div className="mb-3">
        <label className="form-label fw-bold">Proveedor</label>
        <select
          className="form-select form-select-lg"
          value={proveedorId}
          onChange={(e) => setProveedorId(e.target.value)}
        >
          <option value="">Seleccione un proveedor...</option>
          {proveedores.map((prov) => (
            <option key={prov.id} value={prov.id}>
              {prov.nombre}
            </option>
          ))}
        </select>
        {!proveedorId && (
          <div className="form-text text-danger">
            Debe seleccionar un proveedor para confirmar la compra.
          </div>
        )}
      </div>

      {/* BUSCADOR PRODUCTOS */}
      <div className="mb-4">
        <label className="form-label fw-bold">
          Buscar Producto a Ingresar
        </label>
        <input
          className="form-control form-control-lg"
          placeholder="Escriba código o nombre y presione Enter..."
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          onKeyDown={handleBuscarKeyDown}
        />
        <div className="form-text">
          El producto se agrega automáticamente al carrito.
        </div>
      </div>

      <div className="row">
        {/* TABLA DEL CARRITO DE COMPRA */}
        <div className="col-12 col-lg-8 mb-4">
          <h2>Items de la Compra</h2>
          <div className="table-responsive border rounded">
            <table className="table mb-0 align-middle">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cant.</th>
                  <th>Costo Unit.</th>
                  <th>Bonif</th>
                  <th>Imp.</th>
                  <th>Subtotal</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {carrito.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="text-center py-4">
                      No hay renglones en la compra
                    </td>
                  </tr>
                ) : (
                  carrito.map((item) => (
                    <tr key={item.id}>
                      <td style={{ minWidth: "150px" }}>{item.nombre}</td>

                      <td style={{ width: "90px" }}>
                        <input
                          type="number"
                          className="form-control"
                          min="1"
                          value={item.cantidad}
                          onChange={(e) =>
                            actualizarItem(
                              item.id,
                              "cantidad",
                              e.target.value
                            )
                          }
                        />
                      </td>

                      <td style={{ width: "130px" }}>
                        <input
                          type="number"
                          className="form-control"
                          min="0"
                          value={item.costo_unitario}
                          onChange={(e) =>
                            actualizarItem(
                              item.id,
                              "costo_unitario",
                              e.target.value
                            )
                          }
                        />
                      </td>

                      <td style={{ width: "110px" }}>
                        <input
                          type="number"
                          className="form-control"
                          min="0"
                          value={item.bonif}
                          onChange={(e) =>
                            actualizarItem(item.id, "bonif", e.target.value)
                          }
                        />
                      </td>

                      <td style={{ width: "110px" }}>
                        <input
                          type="number"
                          className="form-control"
                          min="0"
                          value={item.impuestos}
                          onChange={(e) =>
                            actualizarItem(
                              item.id,
                              "impuestos",
                              e.target.value
                            )
                          }
                        />
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
          <div className="card shadow-sm">
            <div className="card-body">
              <h3 className="card-title fw-bold mb-4">
                Resumen de la Compra
              </h3>

              <div className="mb-3 d-flex justify-content-between">
                <span className="fw-semibold">Subtotal</span>
                <span>
                  $
                  {subtotal.toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}
                </span>
              </div>

              <div className="mb-3 d-flex justify-content-between">
                <span className="fw-semibold">Impuestos</span>
                <span>
                  $
                  {totalImp.toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}
                </span>
              </div>

              <div className="mb-3 d-flex justify-content-between">
                <span className="fw-semibold">Bonificaciones</span>
                <span>
                  $
                  {totalBonif.toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}
                </span>
              </div>

              <hr />

              <div className="mb-4 d-flex justify-content-between align-items-start">
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
                  {totalFinal.toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}
                </div>
              </div>

              {/* Confirmar compra */}
              <button
                className="btn btn-primary btn-lg w-100 mb-3"
                style={{
                  backgroundColor: "#4e7cf5",
                  borderColor: "#4e7cf5",
                }}
                disabled={
                  loadingCompra ||
                  totalFinal <= 0 ||
                  !proveedorId
                }
                onClick={confirmarCompraHandler}
              >
                {loadingCompra
                  ? "Procesando..."
                  : "Confirmar Compra"}
              </button>

              {/* Cancelar (limpia carrito) */}
              <button
                className="btn btn-outline-danger btn-lg w-100 mb-4"
                disabled={loadingCompra}
                onClick={() => setCarrito([])}
              >
                Cancelar
              </button>

              {/* Panel última compra */}
              <div className="border rounded p-3 bg-light">
                {ultimaCompra ? (
                  <>
                    <p className="mb-1">
                      Última compra: #{ultimaCompra.id} – Estado:{" "}
                      <strong>{ultimaCompra.estado}</strong>
                    </p>

                    {ultimaCompra.proveedor_nombre && (
                      <p className="mb-1">
                        Proveedor:{" "}
                        <strong>{ultimaCompra.proveedor_nombre}</strong>
                      </p>
                    )}

                    <p className="mb-3">
                      Total: $
                      {Number(
                        ultimaCompra.total || 0
                      ).toLocaleString("es-AR", {
                        minimumFractionDigits: 2,
                      })}
                    </p>

                    {ultimaCompra.estado === "confirmada" ||
                    ultimaCompra.estado === "CONFIRMADA" ? (
                      <button
                        className="btn btn-warning w-100"
                        disabled={anulando}
                        onClick={anularUltimaCompra}
                      >
                        {anulando
                          ? "Anulando..."
                          : "Anular Última Compra"}
                      </button>
                    ) : (
                      <button
                        className="btn btn-secondary w-100"
                        disabled
                      >
                        Ya anulada
                      </button>
                    )}
                  </>
                ) : (
                  <p className="text-muted mb-0">
                    Todavía no hay compras confirmadas en esta
                    sesión.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
        {/* fin panel resumen */}
      </div>
    </div>
  );
}
