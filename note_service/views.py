from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Note, Tag
from .serializers import NoteSerializer, TagSerializer
from .pagination import NotePagination
from .filters import NoteFilter
from note_service.utils.permissions import IsOwner


class NoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с заметками.
    Позволяет просматривать, создавать, редактировать и удалять заметки.
    Применяет пагинацию, фильтрацию (по language, датам, тегам) и поиск по title.
    Доступ разрешён только аутентифицированным пользователям, и только владельцу заметки.
    """
    serializer_class = NoteSerializer
    pagination_class = NotePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = NoteFilter
    search_fields = ['title']
    ordering_fields = ['created_at', 'updated_at', 'title']  # Разрешённые поля для сортировки
    ordering = ['-created_at']  # Сортировка по умолчанию
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Note.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с тегами.
    Позволяет просматривать, создавать, редактировать и удалять теги.
    Сортирует теги по алфавиту.
    """
    serializer_class = TagSerializer
    queryset = Tag.objects.all().order_by('name')
    permission_classes = [permissions.IsAuthenticated]
