# core_app/permissions.py

from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Permiso personalizado para permitir el acceso solo a usuarios del grupo 'Admin'.
    """
    def has_permission(self, request, view):
        # El usuario debe estar autenticado y pertenecer al grupo 'Admin'.
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()

class IsCajeroUser(permissions.BasePermission):
    """
    Permiso personalizado para permitir el acceso solo a usuarios del grupo 'Cajero'.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='Cajero').exists()

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir que cualquiera pueda leer (GET, HEAD, OPTIONS),
    pero solo los 'Admin' puedan escribir (POST, PUT, PATCH, DELETE).
    """
    def has_permission(self, request, view):
        # Si el método es seguro (lectura), se permite a cualquier usuario autenticado.
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Si el método no es seguro (escritura), solo se permite si es Admin.
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()