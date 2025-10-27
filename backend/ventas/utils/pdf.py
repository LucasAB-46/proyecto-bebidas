from io import BytesIO
from decimal import Decimal
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF


def _draw_qr(c, text, x, y, size=40*mm):
    """
    Dibuja un QR con 'text' en (x,y) sobre el canvas c.
    x,y son la esquina inferior izquierda.
    """
    code = qr.QrCodeWidget(text)
    bounds = code.getBounds()
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]

    d = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
    d.add(code)
    renderPDF.draw(d, c, x, y)


def build_ticket_pdf(venta, local=None):
    """
    Genera un PDF (boleta simple tipo ticket A4 recortable)
    con datos de la venta, sus ítems y total.
    Devuelve bytes.
    """
    buffer = BytesIO()

    # hoja A4 vertical
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4  # en puntos

    # Margenes
    margin_left = 20 * mm
    current_y = height - 20 * mm

    # Encabezado / Local
    titulo_local = local.nombre if local else "Sucursal"
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_left, current_y, f"{titulo_local}")
    current_y -= 14

    c.setFont("Helvetica", 9)
    c.drawString(margin_left, current_y, f"Venta #{venta.id}  -  {venta.fecha.strftime('%Y-%m-%d %H:%M')}")
    current_y -= 12

    c.drawString(margin_left, current_y, f"Estado: {venta.estado.upper()}")
    current_y -= 18

    # Línea separadora
    c.setLineWidth(0.5)
    c.line(margin_left, current_y, width - margin_left, current_y)
    current_y -= 10

    # Tabla de items
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_left, current_y, "Producto")
    c.drawString(margin_left + 70*mm, current_y, "Cant.")
    c.drawString(margin_left + 90*mm, current_y, "P.Unit")
    c.drawString(margin_left + 115*mm, current_y, "Subtot.")
    current_y -= 12

    c.setFont("Helvetica", 9)

    total_calc = Decimal("0")
    for det in venta.detalles.all():
        nombre_prod = det.producto.nombre[:40] if det.producto and det.producto.nombre else f"ID {det.producto_id}"
        subtotal_renglon = Decimal(det.cantidad) * Decimal(det.precio_unitario)

        c.drawString(margin_left, current_y, nombre_prod)
        c.drawRightString(margin_left + 85*mm, current_y, f"{det.cantidad}")
        c.drawRightString(margin_left + 110*mm, current_y, f"${det.precio_unitario}")
        c.drawRightString(margin_left + 140*mm, current_y, f"${subtotal_renglon}")
        current_y -= 12

        total_calc += subtotal_renglon

        # Salto de página muy básico si nos pasamos
        if current_y < 60 * mm:
            c.showPage()
            current_y = height - 20 * mm
            c.setFont("Helvetica", 9)

    # Línea separadora
    current_y -= 4
    c.setLineWidth(0.5)
    c.line(margin_left, current_y, width - margin_left, current_y)
    current_y -= 14

    # Totales
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, current_y, "TOTAL:")
    # usamos venta.total si existe; si no, total_calc
    total_final = venta.total if venta.total is not None else total_calc
    c.drawRightString(width - margin_left, current_y, f"${total_final}")
    current_y -= 24

    # QR con info para validar la venta
    qr_text = f"VENTA:{venta.id}|TOTAL:{total_final}|FECHA:{venta.fecha.strftime('%Y-%m-%d %H:%M')}"
    # Dibujamos el QR abajo a la izquierda
    _draw_qr(c, qr_text, margin_left, current_y - 40*mm, size=40*mm)

    c.setFont("Helvetica", 7)
    c.drawString(margin_left + 45*mm, current_y - 5, "Escaneá el QR para validar esta venta")
    c.drawString(margin_left + 45*mm, current_y - 17, "o para ver la boleta digital")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawRightString(
        width - margin_left,
        20 * mm,
        "Gracias por tu compra 💙"
    )

    # Cerramos
    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
