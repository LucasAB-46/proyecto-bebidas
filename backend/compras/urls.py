# compras/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CompraViewSet

router = DefaultRouter()
router.register(r"", CompraViewSet, basename="compra")

urlpatterns = [
    path("", include(router.urls)),
]
