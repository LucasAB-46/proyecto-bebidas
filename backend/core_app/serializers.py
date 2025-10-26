from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Local


class LocalSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Local.
    Usado para poblar el selector de sucursal en el frontend.
    """
    class Meta:
        model = Local
        # IMPORTANTE:
        # - Asegurate que 'nombre' exista en tu modelo Local.
        # - Si tu modelo tiene 'activo' o 'direccion' y lo querés exponer,
        #   podés agregarlos acá. Por ahora mantenemos lo mínimo.
        fields = ['id', 'nombre']


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador personalizado para el token JWT.
    Devuelve access/refresh + info útil del usuario.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # payload extra que viaja DENTRO del JWT
        token['username'] = user.username
        token['groups'] = [group.name for group in user.groups.all()]

        return token

    # esto define lo que vuelve en el response del login POST /auth/token/
    def validate(self, attrs):
        data = super().validate(attrs)

        data['username'] = self.user.username
        data['groups'] = [group.name for group in self.user.groups.all()]

        return data
