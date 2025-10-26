from django.urls import path
from .views import ReporteFinancieroView  

urlpatterns = [
    path("financieros/", ReporteFinancieroView.as_view(), name="reporte-financiero"),
]
