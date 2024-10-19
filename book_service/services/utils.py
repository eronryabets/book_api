from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid
from book_service.models import BookChapter, Book, Genre, BookGenre
import re


def clean_text(text):
    """
    Удаляет лишние пустые строки из текста.
    Заменяет три и более подряд идущих переводов строк на один.
    """
    # Заменяем три и более переводов строк на один
    cleaned_text = re.sub(r'\n{3,}', '\n', text)
    return cleaned_text.strip()


def detect_chapter_title(line):
    """
    Эвристически определяет, является ли строка заголовком главы.
    """
    if not line:
        return None

    line = line.strip()

    if len(line) < 3:
        return None

    if len(line.split()) > 8:
        return None

    chapter_keywords = ['chapter', 'глава', 'part', 'часть', 'section', 'раздел']

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
                chapters.append((current_chapter_title or f"Untitled Chapter {len(chapters) + 1}", chapter_text))
                chapter_titles_detected.append(current_chapter_title or f"Untitled Chapter {len(chapters) + 1}")
            # Инициализируем новую главу
            current_chapter_title = potential_title
            current_chapter_lines = []
        else:
            current_chapter_lines.append(line)

    # Сохраняем последнюю главу
    if current_chapter_lines:
        chapter_text = '\n'.join(current_chapter_lines)
        chapter_text = clean_text(chapter_text)
        chapters.append((current_chapter_title or f"Untitled Chapter {len(chapters) + 1}", chapter_text))
        chapter_titles_detected.append(current_chapter_title or f"Untitled Chapter {len(chapters) + 1}")

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
