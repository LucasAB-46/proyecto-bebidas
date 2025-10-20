# catalogo/views.py

from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Categoria, Producto, Cliente, Proveedor, PrecioHistorico
from .serializers import (
    CategoriaSerializer, ProductoSerializer, ClienteSerializer,
    ProveedorSerializer, PrecioHistoricoSerializer
)
# --- 1. IMPORTAMOS LOS NUEVOS PERMISOS ---
from core_app.permissions import IsAdminUser, IsAdminOrReadOnly

# Este Mixin no necesita cambios
class LocalScopedMixin:
    """Enforce X-Local-ID for scoping and writes."""
    local_header = "X-Local-ID"
    scope_field = "local_id"

    def _local_id(self):
        local_id = self.request.headers.get(self.local_header)
        if not local_id:
            raise ValidationError({self.local_header: "Header requerido"})
        try:
            return int(local_id)
        except ValueError:
            raise ValidationError({self.local_header: "Debe ser un entero"})

    def filter_by_local(self, qs):
        return qs.filter(**{self.scope_field: self._local_id()})

    def get_queryset(self):
        base = super().get_queryset()
        return self.filter_by_local(base)

    def perform_create(self, serializer):
        serializer.save(local_id=self._local_id())

    def perform_update(self, serializer):
        serializer.save(local_id=self._local_id())

# ---- CATEGORIA ----
class CategoriaViewSet(LocalScopedMixin, viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by("nombre")
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminOrReadOnly] # <-- 2. APLICAMOS PERMISO
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nombre"]
    ordering_fields = ["nombre"]

# ---- PRODUCTO ----
class ProductoViewSet(LocalScopedMixin, viewsets.ModelViewSet):
    queryset = Producto.objects.select_related("categoria").all().order_by("-id")
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly] # <-- 2. APLICAMOS PERMISO
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["activo", "categoria", "marca"]
    search_fields = ["codigo", "nombre", "marca", "categoria__nombre"]
    ordering_fields = ["nombre", "precio_venta", "stock_actual", "updated_at"]

# ---- CLIENTE ----
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by("-id")
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated] # <-- Mantenemos permiso general para autenticados
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["activo"]
    search_fields = ["nombre", "email", "telefono"]
    ordering_fields = ["nombre", "updated_at"]

# ---- PROVEEDOR ----
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all().order_by("nombre")
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminUser] # <-- 2. APLICAMOS PERMISO (SOLO ADMINS)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["activo"]
    search_fields = ["nombre", "cuit", "email", "telefono"]
    ordering_fields = ["nombre", "updated_at"]

# ---- PRECIOS HISTÓRICOS ----
class PrecioHistoricoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PrecioHistorico.objects.select_related("producto", "proveedor").order_by("-fecha", "-id")
    serializer_class = PrecioHistoricoSerializer
    permission_classes = [IsAdminUser] # <-- Solo Admins pueden ver el historial de costos
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["producto", "proveedor", "moneda"]
    search_fields = ["producto__codigo", "proveedor__nombre"]
    ordering_fields = ["fecha", "costo_unitario"]