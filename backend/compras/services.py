# backend/compras/services.py

from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Compra
from catalogo.models import Producto

@transaction.atomic
def confirmar_compra(compra_id: int, local_id: int) -> Compra:
    """
    Confirma la compra:
    - recalcula totales
    - suma stock a cada producto
    - marca la compra como CONFIRMADA
    """
    # bloqueamos la compra para edición concurrente
    compra = (
        Compra.objects
        .select_for_update()
        .get(id=compra_id, local_id=local_id)
    )

    if compra.estado != "BORRADOR":
        raise ValidationError({"estado": "Sólo BORRADOR puede confirmarse"})

    subtotal = Decimal("0")
    impuestos_total = Decimal("0")
    bonif_total = Decimal("0")

    # recorremos cada detalle/renglón
    for det in (
        compra.detalles
        .select_related("producto")
        .select_for_update()
    ):
        prod: Producto = det.producto

        # seguridad: el producto debe pertenecer al mismo local
        if prod.local_id != local_id:
            raise ValidationError({
                "producto": f"{prod.codigo} pertenece a otro Local"
            })

        if det.cantidad <= 0:
            raise ValidationError({
                "cantidad": "Debe ser > 0"
            })

        # total_renglon = (cantidad * costo_unitario) - bonif + impuestos
        det.total_renglon = (
            det.cantidad * det.costo_unitario
        ) - det.bonif + det.impuestos
        det.save()

        subtotal += (det.cantidad * det.costo_unitario)
        impuestos_total += det.impuestos
        bonif_total += det.bonif

        # SUMAMOS stock al producto porque es una compra
        prod.stock_actual = (prod.stock_actual or 0) + det.cantidad
        prod.save()

    # seteamos totales en la cabecera
    compra.subtotal = subtotal
    compra.impuestos = impuestos_total
    compra.bonificaciones = bonif_total
    compra.total = subtotal - bonif_total + impuestos_total
    compra.estado = "CONFIRMADA"
    compra.save()

    return compra


@transaction.atomic
def anular_compra(compra_id: int, local_id: int) -> Compra:
    """
    Anula una compra CONFIRMADA:
    - resta stock que había sumado
    - marca la compra como ANULADA
    """
    compra = (
        Compra.objects
        .select_for_update()
        .get(id=compra_id, local_id=local_id)
    )

    if compra.estado != "CONFIRMADA":
        raise ValidationError({"estado": "Sólo CONFIRMADA puede anularse"})

    for det in (
        compra.detalles
        .select_related("producto")
        .select_for_update()
    ):
        prod: Producto = det.producto

        if prod.local_id != local_id:
            raise ValidationError({
                "producto": f"{prod.codigo} pertenece a otro Local"
            })

        # como estamos ANULANDO una compra, tenemos que DEVOLVER el stock
        prod.stock_actual = (prod.stock_actual or 0) - det.cantidad
        prod.save()

    compra.estado = "ANULADA"
    compra.save()

    return compra
