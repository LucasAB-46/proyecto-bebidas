# ventas/services.py
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Venta
from catalogo.models import Producto

@transaction.atomic
def confirmar_venta(venta_id: int, local_id: int) -> Venta:
    venta = Venta.objects.select_for_update().get(id=venta_id, local_id=local_id)
    if venta.estado != "BORRADOR":
        raise ValidationError({"estado": "Sólo BORRADOR puede confirmarse"})

    # Recalcular totales y descontar stock
    subtotal = Decimal("0"); impuestos_total = Decimal("0"); bonif_total = Decimal("0")
    for det in venta.detalles.select_related("producto").select_for_update():
        prod: Producto = det.producto
        if prod.local_id != local_id:
            raise ValidationError({"producto": f"{prod.codigo} pertenece a otro Local"})
        if det.cantidad <= 0:
            raise ValidationError({"cantidad": "Debe ser > 0"})
        if prod.stock_actual < det.cantidad:
            raise ValidationError({"stock": f"Stock insuficiente para {prod.codigo}"})

        det.total_renglon = (det.cantidad * det.precio_unitario) - det.bonif + det.impuestos
        det.save()

        subtotal += (det.cantidad * det.precio_unitario)
        impuestos_total += det.impuestos
        bonif_total += det.bonif

        prod.stock_actual = (prod.stock_actual or 0) - det.cantidad
        prod.save()

    venta.subtotal = subtotal
    venta.impuestos = impuestos_total
    venta.bonificaciones = bonif_total
    venta.total = subtotal - bonif_total + impuestos_total
    venta.estado = "CONFIRMADA"
    venta.save()
    return venta

@transaction.atomic
def anular_venta(venta_id: int, local_id: int) -> Venta:
    venta = Venta.objects.select_for_update().get(id=venta_id, local_id=local_id)
    if venta.estado != "CONFIRMADA":
        raise ValidationError({"estado": "Sólo CONFIRMADA puede anularse"})

    for det in venta.detalles.select_related("producto").select_for_update():
        prod = det.producto
        if prod.local_id != local_id:
            raise ValidationError({"producto": f"{prod.codigo} pertenece a otro Local"})
        prod.stock_actual = (prod.stock_actual or 0) + det.cantidad
        prod.save()

    venta.estado = "ANULADA"
    venta.save()
    return venta
