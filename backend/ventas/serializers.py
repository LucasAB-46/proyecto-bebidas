from rest_framework import serializers
from .models import Venta, VentaDetalle


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

    # importante: SIN source="detalles"
    detalles = VentaDetalleReadSerializer(
        many=True,
        read_only=True,
    )

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


class VentaDetalleWriteSerializer(serializers.ModelSerializer):
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


class VentaWriteSerializer(serializers.ModelSerializer):
    """
    Cuerpo esperado en POST /api/ventas/:

    {
      "fecha": "2025-10-28T00:10:30Z",
      "detalles": [
        {
          "producto": 1,
          "cantidad": 2,
          "precio_unitario": 500,
          "bonif": 0,
          "impuestos": 0,
          "renglon": 1
        }
      ]
    }
    """

    detalles = VentaDetalleWriteSerializer(many=True)

    class Meta:
        model = Venta
        fields = [
            "fecha",
            "detalles",
        ]

    def save(self, **kwargs):
        """
        Capturamos local_id y usuario que viene de perform_create()
        y los guardamos en context para que create() pueda usarlos.
        """
        local_id = kwargs.pop("local_id", None)
        usuario = kwargs.pop("usuario", None)

        if local_id is not None:
            self.context["local_id_override"] = local_id
        if usuario is not None:
            self.context["usuario_override"] = usuario

        return super().save(**kwargs)

    def create(self, validated_data):
        """
        - Crea Venta en estado 'borrador'
        - Crea cada VentaDetalle
        - Calcula subtotal/impuestos/bonificaciones/total
        """
        detalles_data = validated_data.pop("detalles", [])

        local_id = self.context.get("local_id_override")
        usuario = self.context.get("usuario_override")

        if local_id is None:
            local_id = 1  # fallback

        venta = Venta.objects.create(
            local_id=local_id,
            usuario=usuario,
            fecha=validated_data.get("fecha"),
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
            cantidad = det.get("cantidad", 0)
            pu = det.get("precio_unitario", 0)
            bon = det.get("bonif", 0)
            imp = det.get("impuestos", 0)

            total_renglon = (cantidad * pu) - bon + imp

            VentaDetalle.objects.create(
                venta=venta,
                renglon=det.get("renglon", 1),
                producto_id=det["producto"],
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
