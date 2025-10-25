from django.contrib import admin
from .models import Venta, VentaDetalle


class VentaDetalleInline(admin.TabularInline):
    model = VentaDetalle
    extra = 0
    fields = (
        "renglon",
        "producto",
        "cantidad",
        "precio_unitario",
        "bonif",
        "impuestos",
        "total_renglon",
    )
    readonly_fields = ()
    can_delete = True


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "local",
        "usuario",
        "estado",
        "fecha",
        "total",
    )
    list_filter = ("estado", "local")
    search_fields = ("id", "usuario__username")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)

    inlines = [VentaDetalleInline]


@admin.register(VentaDetalle)
class VentaDetalleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "venta",
        "renglon",
        "producto",
        "cantidad",
        "precio_unitario",
        "bonif",
        "impuestos",
        "total_renglon",
    )
    search_fields = ("venta__id", "producto__nombre")
    list_filter = ("venta__estado", "venta__local")
    ordering = ("-venta__fecha", "renglon")
