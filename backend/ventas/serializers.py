# ventas/serializers.py
from decimal import Decimal
from typing import List

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Venta, VentaDetalle
from catalogo.models import Producto


# ----------------------- READ SERIALIZERS -----------------------
class VentaDetalleReadSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = VentaDetalle
        fields = (
            "renglon",
            "producto",
            "cantidad",
            "precio_unitario",
            "bonif",
            "impuestos",
            "total_renglon",
        )


class VentaReadSerializer(serializers.ModelSerializer):
    # related_name esperado: "detalles" (según services)
    detalles = VentaDetalleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = (
            "id",
            "local_id",
            "fecha",
            "cliente",
            "estado",
            "subtotal",
            "impuestos",
            "bonificaciones",
            "total",
            "detalles",
        )


# ----------------------- WRITE SERIALIZERS -----------------------
class VentaDetalleWriteSerializer(serializers.Serializer):
    producto = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=14, decimal_places=4)
    precio_unitario = serializers.DecimalField(max_digits=14, decimal_places=4)
    renglon = serializers.IntegerField(required=False)
    bonif = serializers.DecimalField(max_digits=14, decimal_places=4, required=False)
    impuestos = serializers.DecimalField(max_digits=14, decimal_places=4, required=False)

    def validate(self, data):
        if data["cantidad"] <= 0:
            raise serializers.ValidationError({"cantidad": "Debe ser mayor a 0."})
        if data["precio_unitario"] < 0:
            raise serializers.ValidationError({"precio_unitario": "No puede ser negativo."})
        if data.get("bonif") is not None and data["bonif"] < 0:
            raise serializers.ValidationError({"bonif": "No puede ser negativo."})
        if data.get("impuestos") is not None and data["impuestos"] < 0:
            raise serializers.ValidationError({"impuestos": "No puede ser negativo."})
        return data


class VentaWriteSerializer(serializers.ModelSerializer):
    fecha = serializers.DateTimeField(required=False)
    detalles = VentaDetalleWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Venta
        fields = (
            "id",
            "cliente",
            "fecha",
            "detalles",
            "subtotal",
            "impuestos",
            "bonificaciones",
            "total",
        )
        read_only_fields = ("subtotal", "impuestos", "bonificaciones", "total")

    def validate_detalles(self, value: List[dict]):
        if not value:
            raise serializers.ValidationError("Debe informar al menos un renglón.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """
        Crea la venta en 'BORRADOR' con renglones y totales calculados.
        La view debe llamar a serializer.save(local_id=...).
        El descuento de stock ocurre en services.confirmar_venta().
        """
        local_id = validated_data.pop("local_id")
        detalles = validated_data.pop("detalles", [])
        validated_data.setdefault("fecha", timezone.now())

        venta = Venta.objects.create(local_id=local_id, estado="BORRADOR", **validated_data)

        subtotal = Decimal("0")
        imp_total = Decimal("0")
        bonif_total = Decimal("0")

        for idx, d in enumerate(detalles, start=1):
            prod = (
                Producto.objects.select_for_update()
                .only("id", "local_id")
                .get(pk=d["producto"])
            )
            if prod.local_id != local_id:
                raise serializers.ValidationError(
                    {"producto": f"El producto {d['producto']} no pertenece al Local {local_id}."}
                )

            cant = d["cantidad"]
            precio = d["precio_unitario"]
            bonif = d.get("bonif") or Decimal("0")
            imp = d.get("impuestos") or Decimal("0")

            total_r = (cant * precio) - bonif + imp

            VentaDetalle.objects.create(
                venta=venta,
                renglon=d.get("renglon") or idx,
                producto_id=d["producto"],
                cantidad=cant,
                precio_unitario=precio,
                bonif=bonif,
                impuestos=imp,
                total_renglon=total_r,
            )

            subtotal += cant * precio
            imp_total += imp
            bonif_total += bonif

        venta.subtotal = subtotal
        venta.impuestos = imp_total
        venta.bonificaciones = bonif_total
        venta.total = subtotal - bonif_total + imp_total
        venta.save(update_fields=["subtotal", "impuestos", "bonificaciones", "total"])

        return venta

    @transaction.atomic
    def update(self, instance: Venta, validated_data):
        local_id = validated_data.pop("local_id")
        detalles = validated_data.pop("detalles", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        if detalles is not None:
            # Borramos y re-creamos renglones (simple y efectivo para ahora)
            instance.detalles.all().delete()

            subtotal = Decimal("0")
            imp_total = Decimal("0")
            bonif_total = Decimal("0")

            for idx, d in enumerate(detalles, start=1):
                prod = (
                    Producto.objects.select_for_update()
                    .only("id", "local_id")
                    .get(pk=d["producto"])
                )
                if prod.local_id != local_id:
                    raise serializers.ValidationError(
                        {"producto": f"El producto {d['producto']} no pertenece al Local {local_id}."}
                    )

                cant = d["cantidad"]
                precio = d["precio_unitario"]
                bonif = d.get("bonif") or Decimal("0")
                imp = d.get("impuestos") or Decimal("0")

                total_r = (cant * precio) - bonif + imp

                VentaDetalle.objects.create(
                    venta=instance,
                    renglon=d.get("renglon") or idx,
                    producto_id=d["producto"],
                    cantidad=cant,
                    precio_unitario=precio,
                    bonif=bonif,
                    impuestos=imp,
                    total_renglon=total_r,
                )

                subtotal += cant * precio
                imp_total += imp
                bonif_total += bonif

            instance.subtotal = subtotal
            instance.impuestos = imp_total
            instance.bonificaciones = bonif_total
            instance.total = subtotal - bonif_total + imp_total

        instance.save()
        return instance
