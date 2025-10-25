from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Venta, VentaDetalle
from catalogo.models import Producto


@transaction.atomic
def confirmar_venta(venta_id: int, *, local_id: int):
    venta = (
        Venta.objects
        .select_for_update()
        .get(pk=venta_id, local_id=local_id)
    )

    if venta.estado.lower() != "borrador":
        raise ValidationError({"estado": "Sólo BORRADOR puede confirmarse"})

    # bajar stock
    detalles = VentaDetalle.objects.filter(venta=venta).select_for_update()
    for det in detalles:
        prod = Producto.objects.select_for_update().get(pk=det.producto_id)
        if prod.local_id != local_id:
            raise ValidationError(
                {"producto": f"El producto {prod.id} no pertenece al Local {local_id}."}
            )

        # stock disponible?
        if prod.stock_actual < det.cantidad:
            raise ValidationError(
                {"stock": f"Stock insuficiente para producto {prod.id} ({prod.nombre})."}
            )

        prod.stock_actual = prod.stock_actual - det.cantidad
        prod.save(update_fields=["stock_actual"])

    venta.estado = "confirmada"
    venta.save(update_fields=["estado"])
    return venta


@transaction.atomic
def anular_venta(venta_id: int, *, local_id: int):
    venta = (
        Venta.objects
        .select_for_update()
        .get(pk=venta_id, local_id=local_id)
    )

    if venta.estado.lower() != "confirmada":
        raise ValidationError({"estado": "Sólo CONFIRMADA puede anularse"})

    # devolver stock
    detalles = VentaDetalle.objects.filter(venta=venta).select_for_update()
    for det in detalles:
        prod = Producto.objects.select_for_update().get(pk=det.producto_id)
        if prod.local_id != local_id:
            raise ValidationError(
                {"producto": f"El producto {prod.id} no pertenece al Local {local_id}."}
            )
        prod.stock_actual = prod.stock_actual + det.cantidad
        prod.save(update_fields=["stock_actual"])

    venta.estado = "anulada"
    venta.save(update_fields=["estado"])
    return venta
