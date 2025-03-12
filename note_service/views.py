from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Note
from .serializers import NoteSerializer
from .pagination import NotePagination
from .filters import NoteFilter
from note_service.utils.permissions import IsOwner


class NoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet для заметок.
    - Позволяет просматривать, создавать, редактировать и удалять заметки.
    - Применяет пагинацию, фильтрацию (по языку, дате создания и обновления)
      и поиск по заголовку (title).
    - Доступ предоставляется только аутентифицированным пользователям,
      причём только владельцу заметки.
    """
    serializer_class = NoteSerializer
    pagination_class = NotePagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = NoteFilter
    search_fields = ['title']
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Возвращает заметки, принадлежащие текущему пользователю.
        """
        return Note.objects.filter(user_id=self.request.user.id).order_by('-created_at')

    def perform_create(self, serializer):
        """
        При создании заметки устанавливает user_id на основе аутентифицированного пользователя.
        """
        serializer.save(user_id=self.request.user.id)
