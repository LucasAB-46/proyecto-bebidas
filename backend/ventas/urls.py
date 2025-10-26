from django.urls import path
from . import views
from .views_historial import VentaHistorialView, VentaDetalleView

urlpatterns = [
    # crear venta borrador, listar ventas existentes si usás GET
    path("", views.VentaListCreateView.as_view(), name="venta-list-create"),

    # confirmar / anular
    path("<int:pk>/confirmar/", views.VentaConfirmView.as_view(), name="venta-confirm"),
    path("<int:pk>/anular/",    views.VentaAnnulView.as_view(),    name="venta-annul"),

    # historial + detalle lectura
    path("historial/", VentaHistorialView.as_view(), name="venta-historial"),
    path("<int:pk>/",  VentaDetalleView.as_view(),   name="venta-detail"),
]
