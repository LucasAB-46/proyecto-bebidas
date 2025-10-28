from rest_framework import serializers
from .models import Venta, VentaDetalle
from catalogo.models import Producto


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

    # 👇 IMPORTANTE: NO usar source="detalles" acá
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
    Se usa para crear la venta desde el POS del front.
    Espera algo tipo:
    {
        "fecha": "...",
        "detalles": [
            {
                "producto": 123,
                "cantidad": 2,
                "precio_unitario": 500,
                "bonif": 0,
                "impuestos": 0,
                "renglon": 1
            },
            ...
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

    def create(self, validated_data):
        """
        Armamos la Venta en estado 'borrador':
        - calculamos subtotal / impuestos / bonificaciones / total
        - creamos los VentaDetalle
        """
        detalles_data = validated_data.pop("detalles", [])

        # estos vienen inyectados por perform_create en la view
        local_id = self.context.get("local_id")
        usuario = self.context.get("usuario")

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

    def to_internal_value(self, data):
        """
        Permitimos que el front nos mande números como string.
        """
        ret = super().to_internal_value(data)
        # podríamos normalizar acá si quisiéramos, pero por ahora DRF ya lo valida
        return ret

    def __init__(self, *args, **kwargs):
        """
        Hacemos override de __init__ para pasar local_id y usuario
        desde la view (perform_create).
        """
        self.context.setdefault("local_id", kwargs.pop("local_id", None))
        self.context.setdefault("usuario", kwargs.pop("usuario", None))
        super().__init__(*args, **kwargs)
