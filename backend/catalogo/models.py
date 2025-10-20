# catalogo/models.py
from django.db import models
from core_app.models import Local # Importamos el modelo central 'Local'

# --- MODELO DE CATEGORÍA (AHORA ASOCIADO A UN LOCAL) ---
class Categoria(models.Model):
    
    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name="categorias", null=True)
    nombre = models.CharField(max_length=100, help_text="Nombre de la categoría (ej. Cervezas, Vinos)")
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']
        unique_together = ('local', 'nombre')

    def __str__(self):
        try:
            return f"{self.nombre} ({self.local.nombre})"
        except AttributeError: # Maneja el caso donde self.local es None
            return self.nombre

# --- MODELO DE PROVEEDOR (AHORA ASOCIADO A UN LOCAL) ---
class Proveedor(models.Model):
    
    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name="proveedores")
    nombre = models.CharField(max_length=255)
    cuit = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        try:
            return f"{self.nombre} ({self.local.nombre})"
        except AttributeError:
            return self.nombre

# --- MODELO DE PRODUCTO (AHORA ASOCIADO A UN LOCAL Y COMPLETO) ---
class Producto(models.Model):
    
    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name="productos")
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255, db_index=True)
    categoria = models.ForeignKey(Categoria, related_name='productos_categoria', on_delete=models.SET_NULL, null=True, blank=True) # related_name cambiado para evitar conflicto
    marca = models.CharField(max_length=100, blank=True, null=True)
    unidad = models.CharField(max_length=20, blank=True, null=True)
    precio_compra_prom = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    precio_venta = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    stock_actual = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    stock_minimo = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    activo = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('local', 'codigo')

    def __str__(self):
        try:
            return f"{self.codigo} - {self.nombre} ({self.local.nombre})"
        except AttributeError:
            return f"{self.codigo} - {self.nombre}"

# --- MODELO DE CLIENTE (SIN CAMBIOS) ---
class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    tipo_cliente = models.CharField(max_length=50, blank=True, null=True)
    cuit_doc = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    categoria_cliente = models.CharField(max_length=20, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.nombre

# --- MODELO DE PRECIO HISTÓRICO 
class PrecioHistorico(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="precios_historicos")
    fecha = models.DateTimeField(auto_now_add=True)
    costo_unitario = models.DecimalField(max_digits=14, decimal_places=4)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    moneda = models.CharField(max_length=10, default="ARS")

    def __str__(self):
        return f"{self.producto.codigo} @ {self.costo_unitario} ({self.fecha:%Y-%m-%d})" 
