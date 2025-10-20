# core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Importaciones de DRF Spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Importaciones de Simple JWT
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView

# Importación de nuestro serializador personalizado
from core_app.serializers import MyTokenObtainPairSerializer


# --- INICIO DE LA CORRECCIÓN ---
# Definimos las vistas simples que estaban causando el NameError.
def health(request):
    """Vista simple para chequeo de salud de la API."""
    return JsonResponse({"status": "ok"})

def home(request):
    """Vista raíz de la aplicación."""
    return JsonResponse({"app": "bebidas_api", "status": "ok"})
# --- FIN DE LA CORRECCIÓN ---


# --- Vista de Token Personalizada ---
class MyTokenObtainPairView(BaseTokenObtainPairView):
    """
    Vista de obtención de token que utiliza nuestro serializador personalizado
    para incluir roles (grupos) en el payload del token.
    """
    serializer_class = MyTokenObtainPairSerializer


# --- Patrones de URL ---
urlpatterns = [
    # Rutas base y de admin
    path("", home),
    path("admin/", admin.site.urls),
    path("api/health", health),

    # Endpoints de las aplicaciones de la API
    path("api/catalogo/", include("catalogo.urls")),
    path("api/compras/",  include("compras.urls")),
    path("api/ventas/",   include("ventas.urls")),
    path("api/core/",    include("core_app.urls")),

    # Endpoints de Autenticación JWT
    path("api/auth/token/",   MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(),    name="token_refresh"),

    # Endpoints de Documentación (OpenAPI / Swagger)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]