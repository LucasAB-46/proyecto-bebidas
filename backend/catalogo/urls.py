# catalogo/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    CategoriaViewSet,
    ProductoViewSet,
    ClienteViewSet,
    ProveedorViewSet,
    PrecioHistoricoViewSet,
)

# Opción recomendada: acepta con y sin slash final
router = DefaultRouter(trailing_slash=r'/?')

router.register(r"categorias", CategoriaViewSet, basename="categoria")
router.register(r"productos", ProductoViewSet, basename="producto")
router.register(r"clientes", ClienteViewSet, basename="cliente")
router.register(r"proveedores", ProveedorViewSet, basename="proveedor")
router.register(r"precios-historicos", PrecioHistoricoViewSet, basename="preciohistorico")

urlpatterns = [
    path("", include(router.urls)),
]
