from django.contrib import admin
from .models import Venta, VentaDetalle

class VentaDetalleInline(admin.TabularInline):
    model = VentaDetalle
    extra = 0

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "estado", "fecha", "total")
    inlines = [VentaDetalleInline]
