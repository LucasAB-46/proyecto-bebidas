from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import VentaViewSet

router = DefaultRouter()
router.register(r"", VentaViewSet, basename="venta")

urlpatterns = [path("", include(router.urls))]
