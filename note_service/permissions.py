from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцу объекта.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
