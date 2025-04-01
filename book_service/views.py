from django.db import transaction
from django.core.files.storage import default_storage
from django.db.models import Count
from rest_framework.response import Response
from rest_framework import status

from book_service.filters import BookFilter
from book_service.models import Book, Genre, BookChapter, Page
from book_service.pagination import BookPagination
from book_service.serializers import BookSerializer, GenreSerializer, BookChapterSerializer, PageSerializer
from rest_framework.decorators import action
from rest_framework import viewsets, permissions
from book_service.services.book_processing import process_uploaded_book

from .utils.permissions import IsOwner


# TODO isAuth, isOwner... доделать для остальных действий, изменение, удаление и т.д.
class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с книгами (Book).
    - Позволяет просматривать, создавать, редактировать и удалять книги.
    - Подключён кастомный фильтр BookFilter для поиска по названию и жанрам.
    - Имеет отдельный метод «upload_book», который обрабатывает загружаемую книгу.
    """
    queryset = Book.objects.all().order_by('-created_at').prefetch_related(
        'bookgenre_set__genre',
        'chapters'
    )
    serializer_class = BookSerializer
    pagination_class = BookPagination
    filterset_class = BookFilter
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Возвращает только те книги, которые принадлежат текущему пользователю.
        """
        return Book.objects.filter(user_id=self.request.user.id).order_by('-created_at').prefetch_related(
            'bookgenre_set__genre',
            'chapters'
        )

    """
    Больше не получаем user_id из request.data, а берем ид юзера из самого токена.
    """
    def perform_create(self, serializer):
        # Здесь user_id устанавливается из токена, и клиент не должен его передавать
        serializer.save(user_id=self.request.user.id)

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
    """
    ViewSet для работы с главами книги (BookChapter).
    Позволяет просматривать, создавать, редактировать и удалять главы.
    Пользователь может видеть и управлять только своими главами.
    """
    serializer_class = BookChapterSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Возвращает только те главы, которые принадлежат книгам текущего пользователя.
        """
        return BookChapter.objects.filter(book__user_id=self.request.user.id).order_by(
            'start_page_number').prefetch_related('pages')

    @action(detail=False, methods=['get'], url_path='get_chapter_pages')
    def get_chapter_pages(self, request):
        chapter_id = request.query_params.get('chapter_id')

        if not chapter_id:
            return Response({'error': 'Необходимо указать chapter_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            chapter = self.get_queryset().get(id=chapter_id)
        except BookChapter.DoesNotExist:
            return Response({'error': 'Глава не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pages = chapter.pages.all().order_by('page_number')
        serializer = PageSerializer(pages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='bulk_delete')
    def bulk_delete(self, request):
        """
        Массовое удаление глав из книги. Удаление глав также удаляет связанные страницы.
        После удаления необходимо обновить данные книги и глав, а также номера страниц.
        """
        chapter_ids = request.data.get('chapter_ids', [])

        # Валидация входных данных
        if not isinstance(chapter_ids, list) or not all(isinstance(id, str) for id in chapter_ids):
            return Response({'error': 'chapter_ids должен быть списком строковых идентификаторов.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Получаем главы для удаления, фильтруя по пользователю
                chapters_to_delete = BookChapter.objects.filter(id__in=chapter_ids, book__user_id=request.user.id)
                if not chapters_to_delete.exists():
                    return Response({'error': 'Ни одна из указанных глав не найдена или у вас нет к ним доступа.'},
                                    status=status.HTTP_404_NOT_FOUND)

                # Проверяем, что все главы принадлежат одной книге
                book_ids = chapters_to_delete.values_list('book_id', flat=True).distinct()
                if book_ids.count() > 1:
                    return Response({'error': 'Все главы должны принадлежать одной книге.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                book_id = book_ids.first()
                book = Book.objects.select_for_update().get(id=book_id, user_id=request.user.id)

                # Подсчитываем количество страниц, которые будут удалены
                total_deleted_pages = Page.objects.filter(chapter_id__in=chapter_ids).count()

                # Удаляем главы (и связанные страницы через on_delete=models.CASCADE)
                chapters_to_delete.delete()

                # Обновляем количество страниц в книге
                book.total_pages -= total_deleted_pages

                # Получаем оставшиеся главы, аннотированные количеством страниц, упорядоченные по start_page_number
                remaining_chapters = BookChapter.objects.filter(book_id=book_id).annotate(
                    page_count=Count('pages')
                ).order_by('start_page_number')

                # Подготовка данных для bulk_update глав
                updated_chapters = []
                current_page_number = 1  # Инициализируем для назначения номеров глав

                for chapter in remaining_chapters:
                    chapter.start_page_number = current_page_number
                    chapter.end_page_number = current_page_number + chapter.page_count - 1
                    updated_chapters.append(chapter)
                    current_page_number += chapter.page_count

                # Массовое обновление глав
                BookChapter.objects.bulk_update(updated_chapters, ['start_page_number', 'end_page_number'])

                # Сбросим current_page_number для назначения номеров страниц
                current_page_number = 1

                # Получаем все оставшиеся страницы, упорядоченные по новым номерам глав и старым номерам страниц
                pages = Page.objects.filter(chapter__book_id=book_id).select_related('chapter').order_by(
                    'chapter__start_page_number', 'page_number'
                )

                # Подготовка данных для bulk_update страниц
                updated_pages = []
                for page in pages:
                    page.page_number = current_page_number
                    updated_pages.append(page)
                    current_page_number += 1

                # Массовое обновление страниц
                Page.objects.bulk_update(updated_pages, ['page_number'])

                # Сохраняем изменения в книге
                book.save()

                return Response({'status': 'success', 'deleted_pages': total_deleted_pages}, status=status.HTTP_200_OK)

        except Book.DoesNotExist:
            return Response({'error': 'Книга не найдена или у вас нет к ней доступа.'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PageViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы со страницами (Page).
    - Позволяет просматривать, создавать, редактировать и удалять страницы.
    - Содержит метод «get_page_by_number» для получения конкретной страницы по номеру и ID главы.
    """
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
    """
    ViewSet для работы с жанрами (Genre).
    - Позволяет просматривать, создавать, редактировать и удалять жанры.
    - Сортировка по алфавиту (name).
    """
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
