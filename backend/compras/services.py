from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Compra
from catalogo.models import Producto


@transaction.atomic
def confirmar_compra(compra_id: int, local_id: int) -> Compra:
    """
    Confirma una compra:
    - valida local
    - exige estado 'borrador'
    - recalcula totales de la compra
    - suma stock en cada producto involucrado
    - pasa la compra a 'confirmada'
    """

    # 1. Traemos la compra y la bloqueamos para evitar race conditions
    compra = (
        Compra.objects
        .select_for_update()
        .select_related("local")
        .get(id=compra_id)
    )

    # 2. seguridad: la compra tiene que ser del local del header
    if compra.local_id != local_id:
        raise ValidationError({"local": "Esta compra no pertenece a su local"})

    # 3. sólo se puede confirmar si está en borrador
    if compra.estado != "borrador":
        raise ValidationError({"estado": "Sólo BORRADOR puede confirmarse"})

    subtotal = Decimal("0")
    impuestos_total = Decimal("0")
    bonif_total = Decimal("0")

    # 4. Recorremos cada detalle, aseguramos que el producto pertenece al mismo local,
    #    recalculamos total_renglon y actualizamos stock.
    for det in compra.detalles.select_related("producto").select_for_update():
        prod: Producto = det.producto

        # chequeo de local del producto
        if getattr(prod, "local_id", None) != local_id:
            raise ValidationError({
                "producto": f"{prod.id} ({getattr(prod, 'codigo', '')}) pertenece a otro Local"
            })

        if det.cantidad <= 0:
            raise ValidationError({"cantidad": "Debe ser > 0"})

        # total_renglon = (cantidad * costo_unitario) - bonif + impuestos
        det.total_renglon = (
            det.cantidad * det.costo_unitario
        ) - det.bonif + det.impuestos
        det.save()

        # acumular totales
        subtotal += (det.cantidad * det.costo_unitario)
        impuestos_total += det.impuestos
        bonif_total += det.bonif

        # SUMAR stock (porque es una compra / reposición)
        prod.stock_actual = (prod.stock_actual or 0) + det.cantidad
        prod.save()

    # 5. Guardamos totales en la cabecera
    compra.subtotal = subtotal
    compra.impuestos = impuestos_total
    compra.bonificaciones = bonif_total
    compra.total = subtotal - bonif_total + impuestos_total

    # 6. Marcamos confirmada
    compra.estado = "confirmada"
    compra.save()

    return compra


@transaction.atomic
def anular_compra(compra_id: int, local_id: int) -> Compra:
    """
    Anula una compra confirmada:
    - valida local
    - exige estado 'confirmada'
    - RESTA del stock lo que había entrado
    - pasa la compra a 'anulada'
    """

    compra = (
        Compra.objects
        .select_for_update()
        .select_related("local")
        .get(id=compra_id)
    )

    if compra.local_id != local_id:
        raise ValidationError({"local": "Esta compra no pertenece a su local"})

    if compra.estado != "confirmada":
        raise ValidationError({"estado": "Sólo CONFIRMADA puede anularse"})

    for det in compra.detalles.select_related("producto").select_for_update():
        prod = det.producto

        if getattr(prod, "local_id", None) != local_id:
            raise ValidationError({
                "producto": f"{prod.id} ({getattr(prod, 'codigo', '')}) pertenece a otro Local"
            })

        # revertimos el stock que habíamos sumado en confirmar()
        prod.stock_actual = (prod.stock_actual or 0) - det.cantidad
        prod.save()

    compra.estado = "anulada"
    compra.save()

    return compra
