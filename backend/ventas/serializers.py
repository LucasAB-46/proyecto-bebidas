from decimal import Decimal
from typing import List

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Venta, VentaDetalle
from catalogo.models import Producto


# ---------- READ SERIALIZERS ----------

class VentaDetalleReadSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = VentaDetalle
        fields = (
            "renglon",
            "producto",
            "producto_nombre",
            "cantidad",
            "precio_unitario",
            "bonif",
            "impuestos",
            "total_renglon",
        )


class VentaReadSerializer(serializers.ModelSerializer):
    detalles = VentaDetalleReadSerializer(many=True, read_only=True)
    usuario_username = serializers.SerializerMethodField()
    estado = serializers.CharField()

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
            "usuario_username",
            "detalles",
        )

    def get_usuario_username(self, obj):
        # usuario puede ser null
        if getattr(obj, "usuario", None):
            return obj.usuario.username
        return None


# ---------- WRITE SERIALIZERS ----------

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
            "fecha",
            "detalles",
            "subtotal",
            "impuestos",
            "bonificaciones",
            "total",
        )
        read_only_fields = ("subtotal", "impuestos", "bonificaciones", "total")

    def validate_detalles(self, value: List[dict]):
        if not value or len(value) == 0:
            raise serializers.ValidationError("Debe informar al menos un renglón.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """
        Crea venta en estado 'borrador', calcula totales y genera renglones.
        Usa self.context["local_id"] y self.context["usuario"].
        Esta función NO descuenta stock todavía.
        """
        local_id = self.context.get("local_id")
        usuario = self.context.get("usuario")

        if not local_id:
            raise serializers.ValidationError(
                {"local": "Falta local_id en el contexto del serializer."}
            )

        detalles_payload = validated_data.pop("detalles", [])
        # fecha opcional → default ahora
        fecha = validated_data.pop("fecha", None) or timezone.now()

        # creamos venta base
        venta = Venta.objects.create(
            local_id=local_id,
            usuario=usuario if getattr(usuario, "id", None) else None,
            fecha=fecha,
            estado="borrador",
            subtotal=Decimal("0"),
            impuestos=Decimal("0"),
            bonificaciones=Decimal("0"),
            total=Decimal("0"),
        )

        subtotal = Decimal("0")
        imp_total = Decimal("0")
        bonif_total = Decimal("0")

        # iterar detalles
        for idx, d in enumerate(detalles_payload, start=1):
            prod_id = d["producto"]

            # lock producto
            prod = (
                Producto.objects
                .select_for_update()
                .only("id", "stock_actual", "local_id")
                .get(pk=prod_id)
            )

            cantidad = Decimal(d["cantidad"])
            precio_u = Decimal(d["precio_unitario"])
            bonif = Decimal(d.get("bonif") or "0")
            imp = Decimal(d.get("impuestos") or "0")

            total_r = (cantidad * precio_u) - bonif + imp

            VentaDetalle.objects.create(
                venta=venta,
                renglon=d.get("renglon") or idx,
                producto_id=prod.id,
                cantidad=cantidad,
                precio_unitario=precio_u,
                bonif=bonif,
                impuestos=imp,
                total_renglon=total_r,
            )

            subtotal += cantidad * precio_u
            imp_total += imp
            bonif_total += bonif

        venta.subtotal = subtotal
        venta.impuestos = imp_total
        venta.bonificaciones = bonif_total
        venta.total = subtotal - bonif_total + imp_total
        venta.save(
            update_fields=[
                "subtotal",
                "impuestos",
                "bonificaciones",
                "total",
                "updated_at",
            ]
        )

        return venta
