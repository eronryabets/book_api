from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from PyPDF2 import PdfReader
import os
import uuid

from text_service.models import BookChapter, Book, Genre, BookGenre


def process_uploaded_book(request):
    # Используем транзакцию для обеспечения атомарности операций
    with transaction.atomic():
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        genre_ids = request.data.getlist('genres')  # Используем getlist для получения всех жанров
        pdf_file = request.FILES.get('file')
        cover_image = request.FILES.get('cover_image')  # Добавляем обложку

        if not pdf_file:
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

        # Сохранение исходного PDF файла в указанной директории
        original_file_path = os.path.join(book_path, pdf_file.name)
        full_original_path = default_storage.save(original_file_path, pdf_file)

        # Сохранение обложки, если предоставлена
        cover_image_path = None
        if cover_image:
            cover_image_path = default_storage.save(os.path.join(book_path, cover_image.name), cover_image)

        # Создание экземпляра книги в базе данных
        book = Book.objects.create(
            id=book_id,
            user_id=user_id,
            title=title,
            file_path=f"/media/{book_path}",
            cover_image=cover_image_path
        )

        # Связывание жанров с книгой
        BookGenre.objects.bulk_create([
            BookGenre(book=book, genre=genre) for genre in genres
        ])

        # Чтение и разбиение PDF на главы
        pdf_reader = PdfReader(default_storage.open(full_original_path, 'rb'))
        total_pages = len(pdf_reader.pages)
        chapter_number = 1
        chapter_start_page = 0
        chapter_title = None
        chapter_titles_detected = []

        for i in range(total_pages):
            page = pdf_reader.pages[i]
            page_text = page.extract_text()

            # Обнаружение заголовка главы на основе эвристик
            potential_title = detect_chapter_title(page_text)

            if potential_title:
                # Если обнаружен новый заголовок главы, сохранить предыдущую главу
                if chapter_start_page != i:
                    save_chapter(book, book_path, pdf_reader, chapter_number, chapter_start_page, i - 1, chapter_title)
                    chapter_number += 1

                # Начало новой главы
                chapter_start_page = i
                chapter_title = potential_title
                chapter_titles_detected.append(potential_title)

        # Сохранение последней главы
        if chapter_start_page < total_pages:
            save_chapter(book, book_path, pdf_reader, chapter_number, chapter_start_page, total_pages - 1, chapter_title)

        # Удаление исходного PDF файла после обработки
        try:
            default_storage.delete(full_original_path)
        except Exception as e:
            return Response({'error': f'Failed to delete original PDF file: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'Book uploaded and processed successfully', 'chapter_titles': chapter_titles_detected},
                        status=status.HTTP_201_CREATED)


def detect_chapter_title(page_text):
    """
    Heuristically detect if the current page starts a new chapter.
    Example: checks for titles that have certain keywords or are in uppercase.
    """
    if not page_text:
        return None

    # Simple heuristic: look for lines that are in uppercase and not too long
    lines = page_text.split('\n')
    for line in lines:
        # Ignore lines that are too short (e.g., a single letter like "I")
        if len(line) < 3:
            continue

        # Ignore lines that are too long (e.g., entire paragraph in uppercase)
        if len(line.split()) > 8:
            continue

        # Consider it a chapter title if it is uppercase and not too long
        if len(line) < 50 and line.isupper():
            return line.strip()

    # You can add more advanced heuristics or regular expressions here
    return None


def save_chapter(book, book_path, pdf_reader, chapter_number, start_page, end_page, chapter_title):
    """
    Save a chapter as a text file and create a BookChapter instance in the database.
    """
    chapter_filename = f"chapter_{chapter_number}.txt"
    chapter_relative_path = os.path.join(book_path, chapter_filename)

    # Extract pages and save as text file
    chapter_text = "\n".join([pdf_reader.pages[i].extract_text() for i in range(start_page, end_page + 1)])
    chapter_full_path = default_storage.save(chapter_relative_path, ContentFile(chapter_text))

    # Create BookChapter entry
    BookChapter.objects.create(
        id=uuid.uuid4(),
        book=book,
        file_path=f"/media/{chapter_relative_path}",
        start_page_number=start_page + 1,
        end_page_number=end_page + 1,
        chapter_title=chapter_title or f"Untitled Chapter {chapter_number}"
    )
