from rest_framework import permissions
from book_service.models import Book, BookChapter


class IsOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцам объекта.
    Поддерживаются модели Book и BookChapter.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Book):
            return str(obj.user_id) == str(request.user.id)
        elif isinstance(obj, BookChapter):
            return str(obj.book.user_id) == str(request.user.id)
        return False
