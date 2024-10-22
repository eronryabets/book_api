import uuid
from book_service.models import BookChapter, Page
import re


def clean_text(text):
    cleaned_text = re.sub(r'\n{3,}', '\n', text)
    return cleaned_text.strip()


def detect_chapter_title(line):
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
    lines = text.split('\n')
    chapters = []
    current_chapter_title = None
    current_chapter_lines = []
    chapter_titles_detected = []

    for line in lines:
        potential_title = detect_chapter_title(line)
        if potential_title:
            if current_chapter_lines:
                chapter_text = '\n'.join(current_chapter_lines)
                chapter_text = clean_text(chapter_text)
                chapters.append((current_chapter_title or f"Untitled Chapter {len(chapters) + 1}", chapter_text))
                chapter_titles_detected.append(current_chapter_title or f"Untitled Chapter {len(chapters) + 1}")
            current_chapter_title = potential_title
            current_chapter_lines = []
        else:
            current_chapter_lines.append(line)

    if current_chapter_lines:
        chapter_text = '\n'.join(current_chapter_lines)
        chapter_text = clean_text(chapter_text)
        chapters.append((current_chapter_title or f"Untitled Chapter {len(chapters) + 1}", chapter_text))
        chapter_titles_detected.append(current_chapter_title or f"Untitled Chapter {len(chapters) + 1}")

    return chapters, chapter_titles_detected


def split_text_into_pages(text, lines_per_page=26):
    lines = text.split('\n')
    pages = []
    for i in range(0, len(lines), lines_per_page):
        page_content = '\n'.join(lines[i:i + lines_per_page])
        pages.append(page_content)
    return pages


def save_chapter(book, chapter_title, pages_content, current_page_number):
    """
    Сохраняет главу и связанные страницы в базе данных.
    """
    if not chapter_title or chapter_title.strip() == '':
        chapter_title = f"Untitled Chapter {book.chapters.count() + 1}"

    chapter = BookChapter.objects.create(
        id=uuid.uuid4(),
        book=book,
        chapter_title=chapter_title
    )

    start_page_number = current_page_number
    page_number = start_page_number
    for page_content in pages_content:
        Page.objects.create(
            id=uuid.uuid4(),
            chapter=chapter,
            page_number=page_number,
            content=page_content
        )
        page_number += 1

    end_page_number = page_number - 1
    chapter.start_page_number = start_page_number
    chapter.end_page_number = end_page_number
    chapter.save()

    # Возвращаем последний использованный номер страницы
    return end_page_number

