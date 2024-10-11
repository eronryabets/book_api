
from rest_framework import viewsets, status
from rest_framework.decorators import action
from text_service.models import Book, Genre, BookGenre, Tag, BookChapter
from text_service.serializers import BookSerializer, GenreSerializer, BookGenreSerializer, TagSerializer, \
    BookChapterSerializer


from text_service.services.book_processing import process_uploaded_book


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    # Custom action for uploading and processing PDF files
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_book(self, request):
        response = process_uploaded_book(request)
        return response


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class BookGenreViewSet(viewsets.ModelViewSet):
    queryset = BookGenre.objects.all()
    serializer_class = BookGenreSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


# Added new ViewSet for BookChapter
class BookChapterViewSet(viewsets.ModelViewSet):
    queryset = BookChapter.objects.all()
    serializer_class = BookChapterSerializer
