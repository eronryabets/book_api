from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Note, Tag
from .serializers import NoteSerializer, TagSerializer
from .pagination import NotePagination
from .filters import NoteFilter
from note_service.utils.permissions import IsOwner
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions


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


class BulkNoteActionView(APIView):
    """
    View для выполнения массовых операций над заметками.

    Поддерживается действие "delete" - массовое удаление заметок.
    Доступ разрешён только аутентифицированным пользователям.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        action = request.data.get("action")
        note_ids = request.data.get("note_ids", [])

        if not note_ids or not isinstance(note_ids, list):
            return Response(
                {"detail": "note_ids must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if action == "delete":
            with transaction.atomic():
                # Выбираем заметки, принадлежащие текущему пользователю
                notes_qs = Note.objects.filter(pk__in=note_ids, user_id=request.user.id)

                # Если количество найденных заметок меньше переданного списка,
                # значит некоторые заметки не принадлежат пользователю.
                if notes_qs.count() != len(note_ids):
                    return Response(
                        {"detail": "Some notes do not belong to the current user."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                delete_count = notes_qs.count()
                notes_qs.delete()

            return Response(
                {"detail": f"Deleted {delete_count} notes."},
                status=status.HTTP_200_OK
            )

        else:
            return Response(
                {"detail": f"Unknown action: {action}"},
                status=status.HTTP_400_BAD_REQUEST
            )
