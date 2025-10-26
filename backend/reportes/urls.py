from django.urls import path
from .views import ResumenDiaView, ResumenFinancieroView

urlpatterns = [
    path("resumen-dia/", ResumenDiaView.as_view(), name="resumen-dia"),
    path("financieros/", ResumenFinancieroView.as_view(), name="financieros"),
]
