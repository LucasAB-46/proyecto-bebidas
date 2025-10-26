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
    estado = serializers.CharField()  # aseguramos string plano

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
        # no todos los registros tienen usuario obligatorio
        if obj.usuario_id and obj.usuario:
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
        if not value:
            raise serializers.ValidationError("Debe informar al menos un renglón.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """
        Crea la venta en 'borrador' con sus renglones y totales.
        self.context va a traer:
          - "local_id"
          - "usuario"
        """
        local_id = self.context.get("local_id")
        usuario = self.context.get("usuario")

        detalles = validated_data.pop("detalles", [])
        validated_data.setdefault("fecha", timezone.now())

        venta = Venta.objects.create(
            local_id=local_id,
            estado="borrador",
            usuario=usuario,
            **validated_data
        )

        subtotal = Decimal("0")
        imp_total = Decimal("0")
        bonif_total = Decimal("0")

        for idx, d in enumerate(detalles, start=1):
            # lock producto
            prod = (
                Producto.objects
                .select_for_update()
                .only("id", "local_id", "stock_actual")
                .get(pk=d["producto"])
            )

            # hoy todavía NO controlamos que el producto sea del mismo local
            # porque estamos en modo "local fijo 1"; cuando activemos multi-local
            # vamos a validar acá.

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
