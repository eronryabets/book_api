from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
import os
import uuid

from django.conf import settings
from book_service.models import Book, Genre, BookGenre
from .pdf_processing import process_pdf_file
from .fb2_processing import process_fb2_file
from .epub_processing import process_epub_file
from .txt_processing import process_txt_file
from .rtf_processing import process_rtf_file


def process_uploaded_book(request):
    """
    Обрабатывает загруженную книгу, создаёт запись в базе данных и прикрепляет выбранные жанры.
    Определяет тип файла и обрабатывает его соответствующим способом (PDF, FB2, EPUB, TXT или RTF),
    а затем удаляет исходный файл.

    :param request: HTTP-запрос, содержащий данные (user_id, title, description, language, genres, file, cover_image)
    :return: Response объект со статусом выполнения и результатом обработки (имена глав, статус, ошибки)
    """
    with transaction.atomic():
        user_id = request.user.id  # берем user_id НЕ из request.data, а используем request.user.id.
        description = request.data.get('description')
        title = request.data.get('title')
        language = request.data.get('language')
        genre_ids = request.data.getlist('genres')
        uploaded_file = request.FILES.get('file')
        cover_image = request.FILES.get('cover_image')

        if not uploaded_file:
            return Response({'error': 'Файл не предоставлен'}, status=status.HTTP_400_BAD_REQUEST)

        if not genre_ids:
            return Response({'error': 'Жанры не указаны'}, status=status.HTTP_400_BAD_REQUEST)

        genres = Genre.objects.filter(id__in=genre_ids)
        if genres.count() != len(genre_ids):
            return Response({'error': 'Один или несколько жанров неверны'}, status=status.HTTP_400_BAD_REQUEST)

        book_id = uuid.uuid4()
        book_path = os.path.join(str(user_id))
        os.makedirs(os.path.join(settings.MEDIA_ROOT, book_path), exist_ok=True)

        original_file_path = os.path.join(book_path, uploaded_file.name)
        full_original_path = default_storage.save(original_file_path, uploaded_file)

        cover_image_path = None
        if cover_image:
            cover_image_path = default_storage.save(os.path.join(book_path, 'cover', cover_image.name), cover_image)

        book = Book.objects.create(
            id=book_id,
            user_id=user_id,
            title=title,
            description=description,
            language=language,
            cover_image=cover_image_path
        )

        BookGenre.objects.bulk_create([
            BookGenre(book=book, genre=genre) for genre in genres
        ])

        file_extension = uploaded_file.name.lower().split('.')[-1]

        if file_extension == 'pdf':
            result = process_pdf_file(book, full_original_path)
        elif file_extension == 'fb2':
            result = process_fb2_file(book, full_original_path)
        elif file_extension == 'epub':
            result = process_epub_file(book, full_original_path)
        elif file_extension == 'txt':
            result = process_txt_file(book, full_original_path)
        elif file_extension == 'rtf':
            result = process_rtf_file(book, full_original_path)
        else:
            return Response({'error': 'Неподдерживаемый тип файла'}, status=status.HTTP_400_BAD_REQUEST)

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        book.total_chapters = result['total_chapters']
        book.total_pages = result['total_pages']
        book.save()

        try:
            default_storage.delete(full_original_path)
        except Exception as e:
            return Response({'error': f'Не удалось удалить исходный файл: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {'message': 'Книга успешно загружена и обработана', 'chapter_titles': result['chapter_titles']},
            status=status.HTTP_201_CREATED)
