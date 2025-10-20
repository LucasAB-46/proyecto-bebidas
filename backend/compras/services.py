# compras/services.py  (solo muestro cambios clave)
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Compra
from catalogo.models import PrecioHistorico, Producto

@transaction.atomic
def confirmar_compra(compra_id: int) -> Compra:
    compra = Compra.objects.select_for_update().get(id=compra_id)
    if compra.estado != "borrador":
        raise ValidationError({"estado": "Sólo 'borrador' puede confirmarse"})

    subtotal = Decimal("0"); impuestos_total = Decimal("0"); bonif_total = Decimal("0")
    for det in compra.detalles.select_related("producto").select_for_update():
        p: Producto = det.producto
        if p.local_id != compra.local_id:
            raise ValidationError({"producto": f"{p.codigo} no pertenece al Local"})
        det.total_renglon = (det.cantidad * det.costo_unitario) - det.bonif + det.impuestos
        det.save()

        subtotal += (det.cantidad * det.costo_unitario)
        impuestos_total += det.impuestos
        bonif_total += det.bonif

        stock_anterior = p.stock_actual or 0
        p.stock_actual = stock_anterior + det.cantidad
        if (stock_anterior + det.cantidad) > 0:
            p.precio_compra_prom = (
                (p.precio_compra_prom * stock_anterior) + (det.costo_unitario * det.cantidad)
            ) / (stock_anterior + det.cantidad)
        p.save()

        PrecioHistorico.objects.create(
            producto=p,
            costo_unitario=det.costo_unitario,
            proveedor=compra.proveedor,
            moneda="ARS",
        )

    compra.subtotal = subtotal
    compra.impuestos = impuestos_total
    compra.bonificaciones = bonif_total
    compra.total = subtotal - bonif_total + impuestos_total
    compra.estado = "confirmada"
    compra.save()
    return compra

@transaction.atomic
def anular_compra(compra_id: int) -> Compra:
    compra = Compra.objects.select_for_update().get(id=compra_id)
    if compra.estado != "confirmada":
        raise ValidationError({"estado": "Sólo 'confirmada' puede anularse"})
    for det in compra.detalles.select_related("producto").select_for_update():
        p = det.producto
        if p.local_id != compra.local_id:
            raise ValidationError({"producto": f"{p.codigo} no pertenece al Local"})
        p.stock_actual = (p.stock_actual or 0) - det.cantidad
        p.save()
    compra.estado = "anulada"
    compra.save()
    return compra
