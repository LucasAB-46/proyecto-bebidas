# reportes/urls.py
from django.urls import path
from .views import ResumenFinancieroView, TopProductosView

urlpatterns = [
    path("financieros/", ResumenFinancieroView.as_view(), name="resumen-financiero"),
    path("top-productos/", TopProductosView.as_view(), name="top-productos"),
]
