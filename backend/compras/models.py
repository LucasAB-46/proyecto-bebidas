# compras/models.py
from django.db import models
from django.utils import timezone
from catalogo.models import Proveedor, Producto, PrecioHistorico
from core_app.models import Local

class Compra(models.Model):
    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name="compras")
    ESTADOS = (
        ("borrador", "Borrador"),
        ("confirmada", "Confirmada"),
        ("anulada", "Anulada"),
    )
    fecha = models.DateTimeField(default=timezone.now)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="compras")
    subtotal = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    bonificaciones = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="borrador")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Compra #{self.id or 'N'} - {self.proveedor.nombre} - {self.estado}"

class CompraDetalle(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name="detalles")
    renglon = models.PositiveIntegerField(default=1)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=14, decimal_places=4)
    costo_unitario = models.DecimalField(max_digits=14, decimal_places=4)
    bonif = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    impuestos = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total_renglon = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    def __str__(self):
        return f"Det #{self.id} de Compra #{self.compra_id}"

