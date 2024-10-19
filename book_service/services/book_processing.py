import ebooklib
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
import os
import uuid

from book_service.models import BookChapter, Book, Genre, BookGenre
from PyPDF2 import PdfReader
from lxml import etree
from ebooklib import epub
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text
import re


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


def clean_text(text):
    """
    Удаляет лишние пустые строки из текста.
    Заменяет три и более подряд идущих переводов строк на два.
    """
    # Заменяем три и более переводов строк на 1
    cleaned_text = re.sub(r'\n{3,}', '\n', text)
    return cleaned_text.strip()


def detect_chapter_title(line):
    """
    Эвристически определяет, является ли строка заголовком главы.
    Например: проверяет, содержит ли строка определенные ключевые слова или написана заглавными буквами.
    """
    if not line:
        return None

    # Удаляем начальные и конечные пробелы
    line = line.strip()

    # Игнорируем слишком короткие строки
    if len(line) < 3:
        return None

    # Игнорируем слишком длинные строки
    if len(line.split()) > 8:
        return None

    # Ключевые слова для заголовков глав
    chapter_keywords = ['chapter', 'глава', 'part', 'часть', 'section', 'раздел']

    # Проверяем, является ли строка заголовком
    if len(line) < 50 and (line.isupper() or any(line.lower().startswith(keyword) for keyword in chapter_keywords)):
        return line

    return None


def split_text_into_chapters(text):
    """
    Разбивает текст на главы на основе функции detect_chapter_title.
    Возвращает список кортежей: (chapter_title, chapter_text)
    """
    lines = text.split('\n')
    chapters = []
    current_chapter_title = None
    current_chapter_lines = []
    chapter_titles_detected = []

    for line in lines:
        potential_title = detect_chapter_title(line)
        if potential_title:
            # Начинаем новую главу
            if current_chapter_lines:
                # Объединяем линии текущей главы
                chapter_text = '\n'.join(current_chapter_lines)
                # Очищаем текст от лишних пустых строк
                chapter_text = clean_text(chapter_text)
                chapters.append((current_chapter_title or f"Untitled Chapter {len(chapters)+1}", chapter_text))
                chapter_titles_detected.append(current_chapter_title or f"Untitled Chapter {len(chapters)+1}")
            # Инициализируем новую главу
            current_chapter_title = potential_title
            current_chapter_lines = []
        else:
            current_chapter_lines.append(line)

    # Сохраняем последнюю главу
    if current_chapter_lines:
        chapter_text = '\n'.join(current_chapter_lines)
        chapter_text = clean_text(chapter_text)
        chapters.append((current_chapter_title or f"Untitled Chapter {len(chapters)+1}", chapter_text))
        chapter_titles_detected.append(current_chapter_title or f"Untitled Chapter {len(chapters)+1}")

    return chapters, chapter_titles_detected


def save_chapter(book, book_path, chapter_number, start_page, end_page, chapter_title, pdf_reader=None,
                 chapter_text=None):
    """
    Сохраняет главу в виде текстового файла и создает экземпляр BookChapter в базе данных.
    """
    chapter_filename = f"chapter_{chapter_number}.txt"
    chapter_relative_path = os.path.join(book_path, chapter_filename)

    # Если chapter_text не предоставлен, извлекаем его из pdf_reader
    if chapter_text is None and pdf_reader is not None and start_page is not None and end_page is not None:
        # Извлечение страниц и сохранение в текстовый файл
        chapter_text = "\n".join([pdf_reader.pages[i].extract_text() for i in range(start_page, end_page + 1)])

    if chapter_text is None:
        # Если нет текста главы, ничего не делаем
        return

    # Сохранение текста главы в файл
    chapter_full_path = default_storage.save(chapter_relative_path, ContentFile(chapter_text))

    # Создание записи BookChapter
    BookChapter.objects.create(
        id=uuid.uuid4(),
        book=book,
        file_path=f"/media/{chapter_relative_path}",
        start_page_number=(start_page + 1) if start_page is not None else None,
        end_page_number=(end_page + 1) if end_page is not None else None,
        chapter_title=chapter_title or f"Untitled Chapter {chapter_number}"
    )


def process_pdf_file(book, book_path, full_original_path):
    try:
        pdf_reader = PdfReader(default_storage.open(full_original_path, 'rb'))
        total_pages = len(pdf_reader.pages)
        chapter_number = 1
        chapter_start_page = 0
        current_chapter_title = None
        chapter_titles_detected = []

        for i in range(total_pages):
            page = pdf_reader.pages[i]
            page_text = page.extract_text()
            lines = page_text.split('\n')
            chapter_found = False
            for line in lines:
                potential_title = detect_chapter_title(line)
                if potential_title:
                    # Если обнаружен новый заголовок главы
                    if chapter_start_page != i or current_chapter_title is not None:
                        # Сохраняем предыдущую главу
                        save_chapter(
                            book, book_path, chapter_number,
                            chapter_start_page, i - 1,
                            current_chapter_title, pdf_reader=pdf_reader
                        )
                        chapter_number += 1
                    # Начинаем новую главу
                    chapter_start_page = i
                    current_chapter_title = potential_title
                    chapter_titles_detected.append(potential_title)
                    chapter_found = True
                    break  # Переходим к следующей странице после обнаружения заголовка
            if not chapter_found and current_chapter_title is None:
                current_chapter_title = f"Untitled Chapter {chapter_number}"

        # Сохраняем последнюю главу
        if chapter_start_page <= total_pages - 1:
            save_chapter(
                book, book_path, chapter_number,
                chapter_start_page, total_pages - 1,
                current_chapter_title, pdf_reader=pdf_reader
            )

        return {'success': True, 'chapter_titles': chapter_titles_detected}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_fb2_file(book, book_path, full_original_path):
    try:
        with default_storage.open(full_original_path, 'rb') as f:
            xml_content = f.read()

        parser = etree.XMLParser(encoding='utf-8', recover=True)
        tree = etree.fromstring(xml_content, parser=parser)

        # Извлекаем текстовое содержимое
        namespaces = {'fb2': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
        body = tree.find('fb2:body', namespaces)

        if body is None:
            return {'success': False, 'error': 'FB2 body not found'}

        # Получаем все абзацы
        paragraphs = body.findall('.//fb2:p', namespaces)
        text_content = '\n'.join([p.text for p in paragraphs if p.text])

        # Разбиваем текст на главы
        chapters, chapter_titles_detected = split_text_into_chapters(text_content)

        # Сохраняем главы
        chapter_number = 1
        for chapter_title, chapter_text in chapters:
            save_chapter(book, book_path, chapter_number, None, None, chapter_title, chapter_text=chapter_text)
            chapter_number += 1

        return {'success': True, 'chapter_titles': chapter_titles_detected}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_epub_file(book, book_path, full_original_path):
    try:
        epub_book = epub.read_epub(default_storage.path(full_original_path))
        text_content = ''
        for item in epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content = item.get_content()
            soup = BeautifulSoup(content, 'html.parser')
            text_content += soup.get_text() + '\n'

        # Очищаем текст от лишних пустых строк
        text_content = clean_text(text_content)

        # Разбиваем текст на главы
        chapters, chapter_titles_detected = split_text_into_chapters(text_content)

        # Сохраняем главы
        chapter_number = 1
        for chapter_title, chapter_text in chapters:
            save_chapter(book, book_path, chapter_number, None, None, chapter_title, chapter_text=chapter_text)
            chapter_number += 1

        return {'success': True, 'chapter_titles': chapter_titles_detected}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_txt_file(book, book_path, full_original_path):
    try:
        with default_storage.open(full_original_path, 'rb') as f:
            bytes_content = f.read()
            try:
                text_content = bytes_content.decode('utf-8')
            except UnicodeDecodeError:
                # Если не удалось декодировать в UTF-8, пробуем другую кодировку
                text_content = bytes_content.decode('latin1')

        # Очищаем текст от лишних пустых строк
        text_content = clean_text(text_content)

        # Разбиваем текст на главы
        chapters, chapter_titles_detected = split_text_into_chapters(text_content)

        # Сохраняем главы
        chapter_number = 1
        for chapter_title, chapter_text in chapters:
            save_chapter(book, book_path, chapter_number, None, None, chapter_title, chapter_text=chapter_text)
            chapter_number += 1

        return {'success': True, 'chapter_titles': chapter_titles_detected}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_rtf_file(book, book_path, full_original_path):
    try:
        with default_storage.open(full_original_path, 'rb') as f:
            bytes_content = f.read()
            try:
                rtf_content = bytes_content.decode('utf-8')
            except UnicodeDecodeError:
                rtf_content = bytes_content.decode('latin1')
    except Exception as e:
        return {'success': False, 'error': str(e)}

    # Конвертируем RTF в текст
    text_content = rtf_to_text(rtf_content)

    # Разбиваем текст на главы
    chapters, chapter_titles_detected = split_text_into_chapters(text_content)

    # Сохраняем главы
    chapter_number = 1
    for chapter_title, chapter_text in chapters:
        save_chapter(book, book_path, chapter_number, None, None, chapter_title, chapter_text=chapter_text)
        chapter_number += 1

    return {'success': True, 'chapter_titles': chapter_titles_detected}
