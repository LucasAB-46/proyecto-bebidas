from io import BytesIO
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

import qrcode


def build_ticket_pdf(venta, public_base_url: str) -> bytes:
    """
    Genera un comprobante simple tipo ticket en PDF (1 hoja).
    Incluye QR con link público a la venta.

    public_base_url: ej "https://tu-frontend.vercel.app"
    -> vamos a generar algo como {public_base_url}/venta/{venta.id}
    """

    # armamos buffer en memoria
    buffer = BytesIO()

    # tamaño hoja: usamos media carta / tear-off ticket vibe.
    # Podríamos usar letter y recortar, pero para simple hacemos letter (A4 chico USA).
    pdf = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter  # points

    y = height - 40  # empezamos a dibujar desde arriba

    # HEADER LOCAL
    local_nombre = getattr(venta.local, "nombre", "LOCAL")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, f"{local_nombre}")
    y -= 15

    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Venta #{venta.id}")
    y -= 12
    pdf.drawString(40, y, f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}")
    y -= 12
    pdf.drawString(40, y, f"Estado: {venta.estado.upper()}")
    y -= 20

    # DETALLE
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(40, y, "Producto")
    pdf.drawString(250, y, "Cant")
    pdf.drawString(300, y, "P.Unit")
    pdf.drawString(370, y, "Total")
    y -= 12
    pdf.line(40, y, 500, y)
    y -= 10

    pdf.setFont("Helvetica", 10)
    for det in venta.detalles.all():
        prod_nombre = det.producto.nombre if det.producto else "¿?"
        cant = det.cantidad
        pu = det.precio_unitario
        total_r = det.total_renglon

        pdf.drawString(40, y, prod_nombre[:28])  # truncar nombre largo
        pdf.drawRightString(285, y, f"{cant}")
        pdf.drawRightString(
            360, y,
            f"${Decimal(pu):.2f}"
        )
        pdf.drawRightString(
            430, y,
            f"${Decimal(total_r):.2f}"
        )
        y -= 12

        # salto de página ultra simple si nos quedamos sin espacio
        if y < 120:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 10)

    # Totales
    y -= 10
    pdf.line(250, y, 500, y)
    y -= 14
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(360, y, "TOTAL:")
    pdf.drawRightString(
        430, y,
        f"${Decimal(venta.total):.2f}"
    )
    y -= 30

    # QR SECTION
    venta_url = f"{public_base_url.rstrip('/')}/venta/{venta.id}"

    qr_img = qrcode.make(venta_url)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_reader = ImageReader(qr_buffer)

    # dibujamos QR ~40mm
    qr_size = 40 * mm
    pdf.drawImage(qr_reader, 40, y - qr_size + 5, qr_size, qr_size)

    pdf.setFont("Helvetica", 8)
    pdf.drawString(40 + qr_size + 10, y - 5, "Escaneá para ver la venta:")
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawString(40 + qr_size + 10, y - 18, venta_url)

    # footer
    pdf.setFont("Helvetica", 7)
    pdf.drawString(
        40,
        40,
        "Gracias por su compra - Sistema InnovaTI"
    )

    pdf.showPage()
    pdf.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
