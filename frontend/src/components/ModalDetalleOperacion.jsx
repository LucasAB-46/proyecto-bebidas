import { useEffect } from "react";

export default function ModalDetalleOperacion({
  show,
  onClose,
  data, // { id, fecha, estado, subtotal, impuestos, bonificaciones, total, detalles: [...] }
  tipo, // "venta" | "compra"
}) {
  // bloquear scroll cuando está abierto para que se sienta modal posta
  useEffect(() => {
    if (show) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [show]);

  if (!show) return null;

  if (!data) {
    return (
      <div
        className="modal d-block"
        tabIndex="-1"
        style={{ background: "rgba(0,0,0,0.5)" }}
      >
        <div className="modal-dialog modal-lg modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Cargando {tipo}...</h5>
              <button type="button" className="btn-close" onClick={onClose}></button>
            </div>
            <div className="modal-body">
              <p className="text-muted">Obteniendo datos...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const {
    id,
    fecha,
    estado,
    subtotal,
    impuestos,
    bonificaciones,
    total,
    detalles = [],
  } = data;

  return (
    <div
      className="modal d-block"
      tabIndex="-1"
      style={{ background: "rgba(0,0,0,0.5)" }}
    >
      <div className="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              {tipo === "venta" ? "Detalle de Venta" : "Detalle de Compra"} #{id}
            </h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>

          <div className="modal-body">
            <div className="mb-3">
              <div><strong>Fecha:</strong> {new Date(fecha).toLocaleString()}</div>
              <div><strong>Estado:</strong> {estado}</div>
            </div>

            <div className="table-responsive border rounded mb-4">
              <table className="table table-sm align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th>#</th>
                    <th>Producto</th>
                    <th>Cant.</th>
                    <th>Precio Unit.</th>
                    {tipo === "compra" ? <th>Costo Unit.</th> : null}
                    <th>Bonif</th>
                    <th>Imp.</th>
                    <th>Total Reng.</th>
                  </tr>
                </thead>
                <tbody>
                  {detalles.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="text-center py-4">
                        Sin renglones
                      </td>
                    </tr>
                  ) : (
                    detalles.map((r) => (
                      <tr key={r.renglon}>
                        <td>{r.renglon}</td>
                        <td>{r.producto_nombre || r.producto}</td>
                        <td>{Number(r.cantidad).toLocaleString("es-AR")}</td>
                        <td>
                          {r.precio_unitario !== undefined
                            ? `$ ${Number(r.precio_unitario).toLocaleString("es-AR", {
                                minimumFractionDigits: 2,
                              })}`
                            : "-"}
                        </td>
                        {tipo === "compra" ? (
                          <td>
                            {r.costo_unitario !== undefined
                              ? `$ ${Number(r.costo_unitario).toLocaleString("es-AR", {
                                  minimumFractionDigits: 2,
                                })}`
                              : "-"}
                          </td>
                        ) : null}
                        <td>
                          $ {Number(r.bonif || 0).toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                        <td>
                          $ {Number(r.impuestos || 0).toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                        <td>
                          $ {Number(r.total_renglon || 0).toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="border rounded p-3 bg-light">
              <div className="d-flex justify-content-between mb-1">
                <span>Subtotal</span>
                <strong>
                  $ {Number(subtotal || 0).toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}
                </strong>
              </div>
              <div className="d-flex justify-content-between mb-1">
                <span>Impuestos</span>
                <strong>
                  $ {Number(impuestos || 0).toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}
                </strong>
              </div>
              <div className="d-flex justify-content-between mb-1">
                <span>Bonificaciones</span>
                <strong>
                  $ {Number(bonificaciones || 0).toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}
                </strong>
              </div>
              <hr />
              <div className="d-flex justify-content-between">
                <span className="fw-bold">TOTAL</span>
                <span className="fw-bold fs-4">
                  $ {Number(total || 0).toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}
                </span>
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose}>
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
