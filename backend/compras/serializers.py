from decimal import Decimal
from typing import List

from django.apps import apps
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Compra, CompraDetalle
from catalogo.models import Producto  # Producto vive en 'catalogo'


# ----------------------- util: resolver Proveedor -----------------------
def _get_proveedor_model():
    """
    Resuelve el modelo Proveedor dinámicamente.
    Busca primero en app 'catalogo' y luego en 'core_app'.
    Si en tu proyecto Proveedor está en otro lado, agregalo acá.
    """
    candidates = [
        ("catalogo", "Proveedor"),
        ("core_app", "Proveedor"),
    ]
    for app_label, model_name in candidates:
        model = apps.get_model(app_label, model_name)
        if model is not None:
            return model
    raise ImportError(
        "No se encontró el modelo 'Proveedor'. "
        "Si está en otra app, agregalo a la lista 'candidates' en _get_proveedor_model()."
    )


ProveedorModel = _get_proveedor_model()


# ------------------------------------------------------------------------
# READ SERIALIZERS (lo que respondemos al frontend)
# ------------------------------------------------------------------------
class CompraDetalleReadSerializer(serializers.ModelSerializer):
    # mostramos sólo la PK del producto; se puede hacer más rico si querés
    producto = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CompraDetalle
        fields = (
            "renglon",
            "producto",
            "cantidad",
            "costo_unitario",
            "bonif",
            "impuestos",
            "total_renglon",
        )


class CompraReadSerializer(serializers.ModelSerializer):
    proveedor = serializers.PrimaryKeyRelatedField(read_only=True)

    # IMPORTANTÍSIMO: en tu modelo CompraDetalle pusiste
    # compra = models.ForeignKey(Compra, related_name="detalles", ...)
    # así que el reverse name es "detalles".
    detalles = CompraDetalleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = (
            "id",
            "local_id",
            "fecha",
            "proveedor",
            "estado",
            "subtotal",
            "impuestos",
            "bonificaciones",
            "total",
            "detalles",
        )


# ------------------------------------------------------------------------
# WRITE SERIALIZERS (lo que el frontend manda para crear/editar)
# ------------------------------------------------------------------------
class CompraDetalleWriteSerializer(serializers.Serializer):
    producto = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=14, decimal_places=4)
    costo_unitario = serializers.DecimalField(max_digits=14, decimal_places=4)
    renglon = serializers.IntegerField(required=False)
    bonif = serializers.DecimalField(max_digits=14, decimal_places=4, required=False)
    impuestos = serializers.DecimalField(max_digits=14, decimal_places=4, required=False)

    def validate(self, data):
        if data["cantidad"] <= 0:
            raise serializers.ValidationError({"cantidad": "Debe ser mayor a 0."})
        if data["costo_unitario"] < 0:
            raise serializers.ValidationError({"costo_unitario": "No puede ser negativo."})
        if data.get("bonif") is not None and data["bonif"] < 0:
            raise serializers.ValidationError({"bonif": "No puede ser negativo."})
        if data.get("impuestos") is not None and data["impuestos"] < 0:
            raise serializers.ValidationError({"impuestos": "No puede ser negativo."})
        return data


class CompraWriteSerializer(serializers.ModelSerializer):
    # proveedor: PK del proveedor
    proveedor = serializers.PrimaryKeyRelatedField(queryset=ProveedorModel.objects.all())
    # fecha: opcional, si no viene usamos timezone.now()
    fecha = serializers.DateTimeField(required=False)
    # detalles: viene del frontend como array de renglones
    detalles = CompraDetalleWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Compra
        fields = (
            "id",
            "proveedor",
            "fecha",
            "detalles",
            "subtotal",
            "impuestos",
            "bonificaciones",
            "total",
        )
        # estos campos los calculamos nosotros, no los debe mandar el frontend
        read_only_fields = ("subtotal", "impuestos", "bonificaciones", "total")

    def validate_detalles(self, value: List[dict]):
        if not value:
            raise serializers.ValidationError("Debe informar al menos un renglón.")
        return value

    # --------------------------------------------------------------------
    # create / update corren en transacción
    # OJO: la view TIENE que llamar serializer.save(local_id=EL_LOCAL)
    # --------------------------------------------------------------------
    @transaction.atomic
    def create(self, validated_data):
        """
        Crea la compra en estado 'borrador' con sus renglones.
        Espera que venga local_id desde serializer.save(local_id=...).
        Recalcula totales.
        """
        local_id = validated_data.pop("local_id")
        detalles = validated_data.pop("detalles", [])
        validated_data.setdefault("fecha", timezone.now())

        # Creamos cabecera de compra
        compra = Compra.objects.create(
            local_id=local_id,
            estado="borrador",
            **validated_data,
        )

        subtotal = Decimal("0")
        imp_total = Decimal("0")
        bonif_total = Decimal("0")

        # Creamos cada detalle
        for idx, d in enumerate(detalles, start=1):
            # bloquemos y validemos que el producto existe y pertenece al local
            prod = (
                Producto.objects
                .select_for_update()
                .only("id", "local_id")
                .get(pk=d["producto"])
            )

            if prod.local_id != local_id:
                raise serializers.ValidationError(
                    {"producto": f"El producto {d['producto']} no pertenece al Local {local_id}."}
                )

            cant = d["cantidad"]
            costo = d["costo_unitario"]
            bonif = d.get("bonif") or Decimal("0")
            imp = d.get("impuestos") or Decimal("0")

            total_r = (cant * costo) - bonif + imp

            CompraDetalle.objects.create(
                compra=compra,
                renglon=d.get("renglon") or idx,
                producto_id=d["producto"],
                cantidad=cant,
                costo_unitario=costo,
                bonif=bonif,
                impuestos=imp,
                total_renglon=total_r,
            )

            subtotal += cant * costo
            imp_total += imp
            bonif_total += bonif

        # calculamos y guardamos los totales en la cabecera
        compra.subtotal = subtotal
        compra.impuestos = imp_total
        compra.bonificaciones = bonif_total
        compra.total = subtotal - bonif_total + imp_total
        compra.save(update_fields=["subtotal", "impuestos", "bonificaciones", "total"])

        return compra

    @transaction.atomic
    def update(self, instance: Compra, validated_data):
        """
        Edita una compra (sólo mientras sigue siendo 'borrador' normalmente).
        Reemplaza todos los detalles si se mandan nuevos.
        Recalcula totales.
        Espera local_id desde serializer.save(local_id=...).
        """
        local_id = validated_data.pop("local_id")
        detalles = validated_data.pop("detalles", None)

        # Actualizamos campos simples en cabecera (proveedor, fecha, etc.)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        if detalles is not None:
            # pisamos TODOS los renglones
            instance.detalles.all().delete()

            subtotal = Decimal("0")
            imp_total = Decimal("0")
            bonif_total = Decimal("0")

            for idx, d in enumerate(detalles, start=1):
                prod = (
                    Producto.objects
                    .select_for_update()
                    .only("id", "local_id")
                    .get(pk=d["producto"])
                )

                if prod.local_id != local_id:
                    raise serializers.ValidationError(
                        {"producto": f"El producto {d['producto']} no pertenece al Local {local_id}."}
                    )

                cant = d["cantidad"]
                costo = d["costo_unitario"]
                bonif = d.get("bonif") or Decimal("0")
                imp = d.get("impuestos") or Decimal("0")

                total_r = (cant * costo) - bonif + imp

                CompraDetalle.objects.create(
                    compra=instance,
                    renglon=d.get("renglon") or idx,
                    producto_id=d["producto"],
                    cantidad=cant,
                    costo_unitario=costo,
                    bonif=bonif,
                    impuestos=imp,
                    total_renglon=total_r,
                )

                subtotal += cant * costo
                imp_total += imp
                bonif_total += bonif

            instance.subtotal = subtotal
            instance.impuestos = imp_total
            instance.bonificaciones = bonif_total
            instance.total = subtotal - bonif_total + imp_total

        instance.save()
        return instance
