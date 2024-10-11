from django.core.files.storage import default_storage

from text_api import settings

from text_service.models import Book, Genre, BookGenre, Tag
from text_service.serializers import BookSerializer, GenreSerializer, BookGenreSerializer, TagSerializer
from text_service.services.book_processing import process_uploaded_book
from django.conf import settings
import shutil
import os
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from text_service.models import BookChapter
from text_service.serializers import BookChapterSerializer
from text_service.services.chapter_processing import processing_get_chapter


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    # Custom action for uploading and processing PDF files
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_book(self, request):
        response = process_uploaded_book(request)
        return response

    def perform_destroy(self, instance):
        # Get the path to the book directory
        book_directory = os.path.join(settings.MEDIA_ROOT, str(instance.user_id), str(instance.id))

        # Delete the book directory if it exists
        if os.path.isdir(book_directory):
            try:
                shutil.rmtree(book_directory)
            except Exception as e:
                print(f"Error deleting book directory: {e}")

        # Delete the book cover image if it exists
        if instance.cover_image and default_storage.exists(instance.cover_image.path):
            try:
                default_storage.delete(instance.cover_image.path)
            except Exception as e:
                print(f"Error deleting book cover image: {e}")

        # Call the superclass method to delete the instance from the database
        super().perform_destroy(instance)


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

    # Custom action to get chapter text by chapter id
    @action(detail=False, methods=['get'], url_path='get_chapter')
    def get_chapter(self, request):
        response = processing_get_chapter(request)
        return response
