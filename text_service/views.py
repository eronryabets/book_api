from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from text_api.authentication import IsOwner
from text_service.models import Book, Genre, BookGenre, Tag, BookChapter
from text_service.serializers import BookSerializer, GenreSerializer, BookGenreSerializer, TagSerializer, \
    BookChapterSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()  # переопределили его ниже, нужен для корректной отработки
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Возвращаем только книги, принадлежащие текущему пользователю
        return Book.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        # Автоматически устанавливаем текущего пользователя в качестве владельца книги при создании
        serializer.save(user_id=self.request.user.id)


class BookChapterViewSet(viewsets.ModelViewSet):
    queryset = BookChapter.objects.all()
    serializer_class = BookChapterSerializer


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class BookGenreViewSet(viewsets.ModelViewSet):
    queryset = BookGenre.objects.all()
    serializer_class = BookGenreSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
