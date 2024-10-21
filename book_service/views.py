from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework import status

from book_service.filters import BookFilter
from book_service.models import Book, Genre, BookChapter, Page
from book_service.pagination import BookPagination
from book_service.serializers import BookSerializer, GenreSerializer, BookChapterSerializer, PageSerializer
from rest_framework.decorators import action
from rest_framework import viewsets
from book_service.services.book_processing import process_uploaded_book


# TODO isAuth, isOwner...
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by('-created_at').prefetch_related(
        'bookgenre_set__genre',
        'chapters'
    )
    serializer_class = BookSerializer
    pagination_class = BookPagination
    filterset_class = BookFilter

    @action(detail=False, methods=['post'], url_path='upload')
    def upload_book(self, request):
        response = process_uploaded_book(request)
        return response

    def perform_destroy(self, instance):
        if instance.cover_image and default_storage.exists(instance.cover_image.path):
            try:
                default_storage.delete(instance.cover_image.path)
            except Exception as e:
                print(f"Ошибка при удалении обложки книги: {e}")

        super().perform_destroy(instance)


class BookChapterViewSet(viewsets.ModelViewSet):
    queryset = BookChapter.objects.all()
    serializer_class = BookChapterSerializer

    @action(detail=False, methods=['get'], url_path='get_chapter_pages')
    def get_chapter_pages(self, request):
        chapter_id = request.query_params.get('chapter_id')

        if not chapter_id:
            return Response({'error': 'Необходимо указать chapter_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            chapter = BookChapter.objects.get(id=chapter_id)
        except BookChapter.DoesNotExist:
            return Response({'error': 'Глава не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pages = chapter.pages.all().order_by('page_number')
        serializer = PageSerializer(pages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    @action(detail=False, methods=['get'], url_path='get_page_by_number')
    def get_page_by_number(self, request):
        chapter_id = request.query_params.get('chapter_id')
        page_number = request.query_params.get('page_number')

        if not chapter_id or not page_number:
            return Response({'error': 'Необходимо указать chapter_id и page_number'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            page = Page.objects.get(chapter_id=chapter_id, page_number=page_number)
        except Page.DoesNotExist:
            return Response({'error': 'Страница не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = PageSerializer(page)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
