
from rest_framework import permissions
from book_service.models import Book


class IsOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцам объекта.
    Поддерживаются модели Book, Dictionary и Word.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Book):
            is_owner = str(obj.user_id) == str(request.user.id)
        elif hasattr(obj, 'user_id'):
            is_owner = str(obj.user_id) == str(request.user.id)
        elif hasattr(obj, 'dictionary') and hasattr(obj.dictionary, 'user_id'):
            is_owner = str(obj.dictionary.user_id) == str(request.user.id)
        else:
            is_owner = False
        return is_owner
