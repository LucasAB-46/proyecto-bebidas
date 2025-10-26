from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# DRF Spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# JWT
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView

# Serializer personalizado
from core_app.serializers import MyTokenObtainPairSerializer

def health(_request):
    return JsonResponse({"status": "ok"})

def home(_request):
    return JsonResponse({"app": "bebidas_api", "status": "ok"})

class MyTokenObtainPairView(BaseTokenObtainPairView):
    # MUY IMPORTANTE: dejar el login abierto
    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/health", health),  # o /healthz/ si preferís

    # Apps
    path("api/catalogo/", include("catalogo.urls")),
    path("api/compras/",  include("compras.urls")),
    path("api/ventas/",   include("ventas.urls")),
    path("api/core/",     include("core_app.urls")),
    path("api/reportes/", include("reportes.urls")), 

    # Auth
    path("api/auth/token/",   MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(),      name="token_refresh"),

    # Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
