from django.urls import path
from . import views
from .views_historial import CompraHistorialView, CompraDetalleView

urlpatterns = [
    # crear compra borrador, listar compras existentes si usás GET
    path("", views.CompraListCreateView.as_view(), name="compra-list-create"),

    # confirmar / anular
    path("<int:pk>/confirmar/", views.CompraConfirmView.as_view(), name="compra-confirm"),
    path("<int:pk>/anular/",    views.CompraAnnulView.as_view(),   name="compra-annul"),

    # historial + detalle
    path("historial/", CompraHistorialView.as_view(), name="compra-historial"),
    path("<int:pk>/",  CompraDetalleView.as_view(),   name="compra-detail"),
]
