# reportes/urls.py
from django.urls import path
from .views import ResumenFinancieroView

urlpatterns = [
    path("financieros/", ResumenFinancieroView.as_view(), name="resumen-financiero"),
]
