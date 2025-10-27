from decimal import Decimal
from typing import List

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Venta, VentaDetalle
from catalogo.models import Producto


# -----------------------
# SERIALIZADORES READ
# -----------------------

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
    # usuario puede ser null
    usuario = serializers.SerializerMethodField()
    detalles = VentaDetalleReadSerializer(many=True, read_only=True, source="detalles")

    class Meta:
        model = Venta
        fields = (
            "id",
            "local_id",
            "fecha",
            "estado",
            "subtotal",
            "impuestos",
            "bonificaciones",
            "total",
            "usuario",
            "detalles",
        )

    def get_usuario(self, obj):
        if obj.usuario:
            return obj.usuario.username
        return None


# -----------------------
# SERIALIZADORES WRITE
# -----------------------

class VentaDetalleWriteSerializer(serializers.Serializer):
    producto = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=14, decimal_places=4)
    precio_unitario = serializers.DecimalField(max_digits=14, decimal_places=4)
    renglon = serializers.IntegerField(required=False)
    bonif = serializers.DecimalField(max_digits=14, decimal_places=4, required=False)
    impuestos = serializers.DecimalField(max_digits=14, decimal_places=4, required=False)

    def validate(self, data):
        # cantidad > 0
        if data["cantidad"] <= 0:
            raise serializers.ValidationError({"cantidad": "Debe ser mayor a 0."})
        # precio_unitario >= 0
        if data["precio_unitario"] < 0:
            raise serializers.ValidationError({"precio_unitario": "No puede ser negativo."})
        # bonif >= 0
        if data.get("bonif") is not None and data["bonif"] < 0:
            raise serializers.ValidationError({"bonif": "No puede ser negativo."})
        # impuestos >= 0
        if data.get("impuestos") is not None and data["impuestos"] < 0:
            raise serializers.ValidationError({"impuestos": "No puede ser negativo."})
        return data


class VentaWriteSerializer(serializers.ModelSerializer):
    """
    Este serializer se usa para CREAR / EDITAR ventas en estado 'borrador'.
    El frontend manda:
    {
        "fecha": "...iso...",
        "detalles": [
            {
                "producto": <id>,
                "cantidad": <num>,
                "precio_unitario": <num>,
                "renglon": <n?>,
                "bonif": <num?>,
                "impuestos": <num?>
            },
            ...
        ]
    }

    No hace falta que mande subtotal/total/etc. Eso lo calculamos acá.
    """

    fecha = serializers.DateTimeField(required=False)
    detalles = VentaDetalleWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Venta
        fields = (
            "id",
            "fecha",
            "detalles",
            # totales NO se escriben desde el front, los generamos
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
        Crea la Venta en 'borrador' con detalles y totales calculados.
        La ViewSet llama serializer.save(local_id=?, usuario=?)
        """
        # campos extra que viene del perform_create()
        local_id = validated_data.pop("local_id")
        usuario = validated_data.pop("usuario", None)

        detalles_data = validated_data.pop("detalles", [])
        validated_data.setdefault("fecha", timezone.now())

        # creamos venta en estado borrador
        venta = Venta.objects.create(
            local_id=local_id,
            estado="borrador",
            usuario=usuario,
            **validated_data,
        )

        subtotal = Decimal("0")
        imp_total = Decimal("0")
        bonif_total = Decimal("0")

        for idx, d in enumerate(detalles_data, start=1):
            # lock + chequeo que el producto pertenezca al local correcto en el futuro
            prod = (
                Producto.objects
                .select_for_update()
                .only("id")
                .get(pk=d["producto"])
            )

            cant = d["cantidad"]
            precio = d["precio_unitario"]
            bonif = d.get("bonif") or Decimal("0")
            imp = d.get("impuestos") or Decimal("0")

            total_r = (cant * precio) - bonif + imp

            VentaDetalle.objects.create(
                venta=venta,
                renglon=d.get("renglon") or idx,
                producto_id=prod.id,
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
        """
        Si en algún momento editamos una venta borrador desde el front.
        Por ahora el front no usa PUT/PATCH, pero lo dejamos prolijo.
        """
        local_id = validated_data.pop("local_id")
        usuario = validated_data.pop("usuario", None)
        detalles_data = validated_data.pop("detalles", None)

        # actualizamos campos simples (ej: fecha)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        # si mandaron nuevos detalles, reemplazamos todos
        if detalles_data is not None:
            instance.detalles.all().delete()

            subtotal = Decimal("0")
            imp_total = Decimal("0")
            bonif_total = Decimal("0")

            for idx, d in enumerate(detalles_data, start=1):
                prod = (
                    Producto.objects
                    .select_for_update()
                    .only("id")
                    .get(pk=d["producto"])
                )

                cant = d["cantidad"]
                precio = d["precio_unitario"]
                bonif = d.get("bonif") or Decimal("0")
                imp = d.get("impuestos") or Decimal("0")

                total_r = (cant * precio) - bonif + imp

                VentaDetalle.objects.create(
                    venta=instance,
                    renglon=d.get("renglon") or idx,
                    producto_id=prod.id,
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

        # guardamos
        if usuario and not instance.usuario_id:
            instance.usuario = usuario

        instance.save()
        return instance
