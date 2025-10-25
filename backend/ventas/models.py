from django.db import models
from django.utils import timezone
from core_app.models import Local
from catalogo.models import Producto

class Venta(models.Model):
    ESTADOS = (
        ("borrador", "Borrador"),
        ("confirmada", "Confirmada"),
        ("anulada", "Anulada"),
    )

    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name="ventas")
    fecha = models.DateTimeField(default=timezone.now)

    subtotal = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    bonificaciones = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="borrador")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    usuario = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="ventas_registradas",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Venta #{self.id or 'N'} - {self.estado}"


class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    renglon = models.PositiveIntegerField(default=1)

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)

    cantidad = models.DecimalField(max_digits=14, decimal_places=4)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=4)

    bonif = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    total_renglon = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    def __str__(self):
        return f"Det #{self.id} de Venta #{self.venta_id}"
