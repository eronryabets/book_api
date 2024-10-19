
from django.core.files.storage import default_storage
from django.conf import settings
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
import os
import uuid

from book_service.models import Book, Genre, BookGenre
from .pdf_processing import process_pdf_file
from .fb2_processing import process_fb2_file
from .epub_processing import process_epub_file
from .txt_processing import process_txt_file
from .rtf_processing import process_rtf_file


def process_uploaded_book(request):
    # Используем транзакцию для обеспечения атомарности операций
    with transaction.atomic():
        user_id = request.data.get('user_id')
        description = request.data.get('description')
        title = request.data.get('title')
        genre_ids = request.data.getlist('genres')  # Используем getlist для получения всех жанров
        uploaded_file = request.FILES.get('file')
        cover_image = request.FILES.get('cover_image')  # Добавляем обложку

        if not uploaded_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        if not genre_ids:
            return Response({'error': 'No genres provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка, что все переданные жанры существуют
        genres = Genre.objects.filter(id__in=genre_ids)
        if genres.count() != len(genre_ids):
            return Response({'error': 'One or more genres are invalid'}, status=status.HTTP_400_BAD_REQUEST)

        # Генерация UUID для книги и создание директории
        book_id = uuid.uuid4()
        book_path = os.path.join(str(user_id), str(book_id))
        os.makedirs(os.path.join(settings.MEDIA_ROOT, book_path), exist_ok=True)

        # Сохранение исходного файла
        original_file_path = os.path.join(book_path, uploaded_file.name)
        full_original_path = default_storage.save(original_file_path, uploaded_file)

        # Сохранение обложки, если предоставлена
        cover_image_path = None
        if cover_image:
            cover_image_path = default_storage.save(os.path.join(book_path, cover_image.name), cover_image)

        # Создание экземпляра книги в базе данных
        book = Book.objects.create(
            id=book_id,
            user_id=user_id,
            title=title,
            description=description,
            file_path=f"/media/{book_path}",
            cover_image=cover_image_path
        )

        # Связывание жанров с книгой
        BookGenre.objects.bulk_create([
            BookGenre(book=book, genre=genre) for genre in genres
        ])

        # Определение типа файла по расширению
        file_extension = uploaded_file.name.lower().split('.')[-1]

        # Обработка файла в зависимости от его типа
        if file_extension == 'pdf':
            result = process_pdf_file(book, book_path, full_original_path)
        elif file_extension == 'fb2':
            result = process_fb2_file(book, book_path, full_original_path)
        elif file_extension == 'epub':
            result = process_epub_file(book, book_path, full_original_path)
        elif file_extension == 'txt':
            result = process_txt_file(book, book_path, full_original_path)
        elif file_extension == 'rtf':
            result = process_rtf_file(book, book_path, full_original_path)
        else:
            return Response({'error': 'Unsupported file type'}, status=status.HTTP_400_BAD_REQUEST)

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Удаление исходного файла после обработки
        try:
            default_storage.delete(full_original_path)
        except Exception as e:
            return Response({'error': f'Failed to delete original file: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {'message': 'Book uploaded and processed successfully', 'chapter_titles': result['chapter_titles']},
            status=status.HTTP_201_CREATED)