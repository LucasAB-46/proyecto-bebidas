from rest_framework import serializers
from .models import Venta, VentaDetalle
from django.utils import timezone


# -------------------------
# READ SERIALIZERS
# -------------------------

class VentaDetalleReadSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(
        source="producto.nombre",
        read_only=True
    )

    class Meta:
        model = VentaDetalle
        fields = [
            "id",
            "renglon",
            "producto",
            "producto_nombre",
            "cantidad",
            "precio_unitario",
            "bonif",
            "impuestos",
            "total_renglon",
        ]


class VentaReadSerializer(serializers.ModelSerializer):
    local_nombre = serializers.CharField(source="local.nombre", read_only=True)
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)

    detalles = VentaDetalleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = [
            "id",
            "fecha",
            "estado",
            "local",
            "local_nombre",
            "usuario",
            "usuario_username",
            "subtotal",
            "impuestos",
            "bonificaciones",
            "total",
            "detalles",
        ]


# -------------------------
# WRITE SERIALIZERS
# -------------------------

class VentaDetalleWriteSerializer(serializers.ModelSerializer):
    """
    Acepta:
    - producto: 110
    - producto: { "id": 110, "nombre": "...", ... }
    """
    producto = serializers.JSONField()

    class Meta:
        model = VentaDetalle
        fields = [
            "producto",
            "cantidad",
            "precio_unitario",
            "bonif",
            "impuestos",
            "renglon",
        ]

    def to_internal_value(self, data):
        raw = super().to_internal_value(data)
        prod_field = raw.get("producto")

        # dict -> usar .id
        if isinstance(prod_field, dict):
            prod_id = prod_field.get("id")
            raw["producto"] = prod_id

        # string numérica -> casteo
        elif not isinstance(prod_field, int):
            try:
                raw["producto"] = int(prod_field)
            except Exception:
                pass

        return raw


class VentaWriteSerializer(serializers.ModelSerializer):
    detalles = VentaDetalleWriteSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Venta
        fields = [
            "fecha",
            "detalles",
        ]

    def save(self, **kwargs):
        # guardamos info de perform_create
        local_id = kwargs.pop("local_id", None)
        usuario = kwargs.pop("usuario", None)

        if local_id is not None:
            self.context["local_id_override"] = local_id
        if usuario is not None:
            self.context["usuario_override"] = usuario

        return super().save(**kwargs)

    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles", [])

        local_id = self.context.get("local_id_override", 1)
        usuario = self.context.get("usuario_override", None)

        # si no vino fecha en el body, usamos ahora()
        fecha_val = validated_data.get("fecha")
        if not fecha_val:
            fecha_val = timezone.now()

        venta = Venta.objects.create(
            local_id=local_id,
            usuario=usuario,
            fecha=fecha_val,
            estado="borrador",
            subtotal=0,
            impuestos=0,
            bonificaciones=0,
            total=0,
        )

        subtotal_acum = 0
        imp_acum = 0
        bonif_acum = 0

        for det in detalles_data:
            producto_id = det.get("producto")
            cantidad = det.get("cantidad", 0) or 0
            pu = det.get("precio_unitario", 0) or 0
            bon = det.get("bonif", 0) or 0
            imp = det.get("impuestos", 0) or 0

            total_renglon = (cantidad * pu) - bon + imp

            VentaDetalle.objects.create(
                venta=venta,
                renglon=det.get("renglon", 1),
                producto_id=producto_id,
                cantidad=cantidad,
                precio_unitario=pu,
                bonif=bon,
                impuestos=imp,
                total_renglon=total_renglon,
            )

            subtotal_acum += cantidad * pu
            imp_acum += imp
            bonif_acum += bon

        total_final = subtotal_acum - bonif_acum + imp_acum

        venta.subtotal = subtotal_acum
        venta.impuestos = imp_acum
        venta.bonificaciones = bonif_acum
        venta.total = total_final
        venta.save()

        return venta
