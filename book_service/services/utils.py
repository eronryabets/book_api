import uuid
from book_service.models import BookChapter, Page
import re


def clean_text(text):
    if not text:
        return ''

    # Заменяем символы табуляции на пробелы
    text = text.replace('\t', ' ')

    # Удаляем избыточные пробелы (более одного пробела подряд)
    text = re.sub(r' {2,}', ' ', text)

    # Удаляем избыточные переносы строк (более двух подряд)
    text = re.sub(r'\n{3,}', '\n', text)

    # Удаляем пробелы в начале и конце каждой строки
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines]
    cleaned_text = '\n'.join(cleaned_lines)

    return cleaned_text.strip()


#  for DPF processing
def detect_chapter_title(line):
    if not line:
        return None

    line = line.strip()

    if len(line) < 3:
        return None

    words = line.split()
    if len(words) > 8:
        return None

    chapter_keywords = [
        'chapter',
        'глава',
        'part',
        'часть',
        'section',
        'раздел'
    ]
    line_lower = line.lower()

    # Проверяем наличие ключевых слов в начале строки
    for keyword in chapter_keywords:
        if line_lower.startswith(keyword):
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
                chapter_titles_detected.append(current_chapter_title or f"Без названия {len(chapters) + 1}")
            current_chapter_title = potential_title
            current_chapter_lines = []
        else:
            current_chapter_lines.append(line)

    if current_chapter_lines:
        chapter_text = '\n'.join(current_chapter_lines)
        chapter_text = clean_text(chapter_text)
        chapters.append((current_chapter_title or f"Без названия {len(chapters) + 1}", chapter_text))
        chapter_titles_detected.append(current_chapter_title or f"Без названия {len(chapters) + 1}")

    return chapters, chapter_titles_detected


def split_text_into_pages(text, lines_per_page=26, max_line_length=125):
    def split_long_line(line, max_length):
        """
        Split a line into multiple lines without splitting words. If a word doesn't fit, move it to the next line.
        """
        words = line.split(' ')
        current_line = ""
        lines = []

        for word in words:
            # Check if adding the word would exceed the max length
            if len(current_line) + len(word) + (1 if current_line else 0) <= max_length:
                # Add the word to the current line
                if current_line:
                    current_line += ' ' + word
                else:
                    current_line = word
            else:
                # If the word doesn't fit, add the current line to lines and start a new line
                if current_line:
                    lines.append(current_line)
                current_line = word

        # Append the last line if it's not empty
        if current_line:
            lines.append(current_line)

        return lines

    lines = text.split('\n')
    adjusted_lines = []

    # Iterate over each line and split it if necessary
    for line in lines:
        adjusted_lines.extend(split_long_line(line, max_line_length))

    pages = []
    for i in range(0, len(adjusted_lines), lines_per_page):
        page_content = '\n'.join(adjusted_lines[i:i + lines_per_page])
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
