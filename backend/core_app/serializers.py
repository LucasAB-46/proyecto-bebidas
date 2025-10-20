# core_app/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Local

class LocalSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Local.
    Utilizado para listar las sucursales disponibles.
    """
    class Meta:
        model = Local
        fields = ['id', 'nombre']

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador personalizado para el token JWT.
    Hereda del serializador base y le añade información extra (payload)
    a la respuesta del login, como el nombre de usuario y sus roles (grupos).
    """
    @classmethod
    def get_token(cls, user):
        # Llama al método original para obtener el token base con la información estándar
        token = super().get_token(user)

        # Añade campos personalizados al payload del token
        token['username'] = user.username
        token['groups'] = [group.name for group in user.groups.all()]

        return token