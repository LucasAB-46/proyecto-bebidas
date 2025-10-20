# ventas/models.py
from django.db import models
from core_app.models import Local
from catalogo.models import Producto, Cliente

class Venta(models.Model):
    ESTADOS = (
        ("BORRADOR", "BORRADOR"),
        ("CONFIRMADA", "CONFIRMADA"),
        ("ANULADA", "ANULADA"),
    )

    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name="ventas")  # 👈 multi-local
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.SET_NULL)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    bonificaciones = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    estado = models.CharField(max_length=12, choices=ESTADOS, default="BORRADOR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Venta #{self.id} ({self.estado})"

class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, related_name="detalles", on_delete=models.CASCADE)
    renglon = models.IntegerField(default=1)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=14, decimal_places=4)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=4)
    bonif = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total_renglon = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        ordering = ["venta_id", "renglon"]  # 👈 sin coma final
