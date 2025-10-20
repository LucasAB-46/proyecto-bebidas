# catalogo/admin.py
from django.contrib import admin
from .models import Categoria, Producto, Cliente, Proveedor, PrecioHistorico

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'marca', 'precio_venta', 'stock_actual', 'activo')
    list_filter = ('activo', 'categoria', 'marca') # <-- CORREGIDO
    search_fields = ('codigo', 'nombre', 'marca', 'categoria__nombre')
    list_editable = ('precio_venta', 'stock_actual', 'activo')
    autocomplete_fields = ('categoria',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_cliente', 'cuit_doc', 'telefono', 'categoria_cliente', 'activo') # <-- CORREGIDO
    list_filter = ('activo', 'tipo_cliente', 'categoria_cliente') # <-- CORREGIDO
    search_fields = ('nombre', 'cuit_doc', 'email')

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cuit', 'telefono', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'cuit')

@admin.register(PrecioHistorico)
class PrecioHistoricoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'proveedor', 'costo_unitario', 'fecha')
    list_filter = ('proveedor', 'moneda')
    autocomplete_fields = ('producto', 'proveedor')