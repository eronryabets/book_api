from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from PyPDF2 import PdfReader
import os
import uuid

from text_service.models import BookChapter, Book


def process_uploaded_book(request):
    user_id = request.data.get('user_id')
    title = request.data.get('title')
    genre = request.data.get('genre')
    pdf_file = request.FILES.get('file')

    if not pdf_file:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate UUID for book and create book instance
    book_id = uuid.uuid4()
    book_path = os.path.join(str(user_id), str(book_id))
    os.makedirs(os.path.join(settings.MEDIA_ROOT, book_path),
                exist_ok=True)  # Создаем директорию, если она не существует

    # Save the original PDF file in the designated directory
    original_file_path = os.path.join(book_path, pdf_file.name)
    full_original_path = default_storage.save(original_file_path, pdf_file)

    # Create a book instance in the database
    book = Book.objects.create(
        id=book_id,
        user_id=user_id,
        title=title,
        genre=genre,
        file_path=f"/media/{book_path}"
    )

    # Read and split PDF into chapters (based on 10 pages or detected chapter titles)
    pdf_reader = PdfReader(default_storage.open(full_original_path, 'rb'))
    total_pages = len(pdf_reader.pages)
    chapter_number = 1
    chapter_start_page = 0
    chapter_title = None
    chapter_titles_detected = []

    for i in range(total_pages):
        page = pdf_reader.pages[i]
        page_text = page.extract_text()

        # Detect chapter titles based on heuristics (e.g., certain formatting or keywords)
        potential_title = detect_chapter_title(page_text)

        if potential_title:
            # If we detected a new chapter title, save the previous chapter
            if chapter_start_page != i:
                save_chapter(book, book_path, pdf_reader, chapter_number, chapter_start_page, i - 1, chapter_title)
                chapter_number += 1

            # Start a new chapter
            chapter_start_page = i
            chapter_title = potential_title
            chapter_titles_detected.append(potential_title)

    # Save the last chapter (if any)
    if chapter_start_page < total_pages:
        save_chapter(book, book_path, pdf_reader, chapter_number, chapter_start_page, total_pages - 1, chapter_title)

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