import uuid
import re
from book_service.models import BookChapter, Page


def clean_text(text):
    """
    Очищает текст от лишних табуляций, лишних пробелов и переносов строк.
    Возвращает итоговую «чистую» строку.
    """
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


def detect_chapter_title(line):
    """
    Проверяет, является ли строка названием главы, ориентируясь на ключевые слова
    и структуру строки. Возвращает строку, если она распознана как заголовок,
    иначе None.
    """
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
    """
    Разбивает весь текст на главы, опираясь на detect_chapter_title для определения заголовков.
    Если заголовок не найден, формирует главу с названием «Без названия n».

    :param text: Полный текст для разбивки
    :return: Кортеж из списка кортежей (название главы, текст главы) и списка обнаруженных названий глав
    """
    lines = text.split('\n')
    chapters = []
    current_chapter_title = None
    current_chapter_lines = []
    chapter_titles_detected = []

    for line in lines:
        potential_title = detect_chapter_title(line)
        if potential_title:
            # Если уже есть накопленный текст, сохраняем предыдущую главу
            if current_chapter_lines:
                chapter_text = '\n'.join(current_chapter_lines)
                # chapter_text = clean_text(chapter_text)
                chapters.append(
                    (current_chapter_title or f"Untitled Chapter {len(chapters) + 1}",
                     chapter_text)
                )
                chapter_titles_detected.append(
                    current_chapter_title or f"Без названия {len(chapters)}"
                )
            # Начинаем новую главу
            current_chapter_title = potential_title
            current_chapter_lines = []
        else:
            current_chapter_lines.append(line)

    # Сохраняем последнюю накопленную главу, если есть
    if current_chapter_lines:
        chapter_text = '\n'.join(current_chapter_lines)
        chapter_text = clean_text(chapter_text)
        chapters.append(
            (current_chapter_title or f"Без названия {len(chapters) + 1}",
             chapter_text)
        )
        chapter_titles_detected.append(
            current_chapter_title or f"Без названия {len(chapters)}"
        )

    return chapters, chapter_titles_detected


def split_text_into_pages_by_lines(chapter_text, lines_per_page=20):
    """
    Разбивает текст одной главы на страницы по 20 (по умолчанию) строк на страницу.
    :param chapter_text: Текст всей главы
    :param lines_per_page: Сколько строк будет на одной "логической" странице
    :return: Список страниц, где каждая страница — это строка текста, содержащая 10 строк
    """
    # Сначала чистим от лишних символов
    # cleaned = clean_text(chapter_text)    # OLD
    # Разбиваем по переносам строк
    # lines = cleaned.split('\n')    # OLD

    # Стало (убрали clean_text):
    lines = chapter_text.split('\n')    # NEW
    # Убираем возможные пустые хвостовые строки (если нужно)
    # lines = [l for l in lines if l.strip()]

    pages = []
    for i in range(0, len(lines), lines_per_page):
        chunk = lines[i: i + lines_per_page]
        # Склеиваем обратно
        page_content = '\n'.join(chunk)
        pages.append(page_content)

    return pages


def save_chapter(book, chapter_title, pages_content, current_page_number):
    """
    Создаёт модель главы (BookChapter) и связанные с ней страницы (Page) в базе данных.
    Возвращает последний номер страницы, использованный для сохранённой главы.

    :param book: Модель Book, к которой привязана глава
    :param chapter_title: Название главы
    :param pages_content: Список текстов страниц (список строк)
    :param current_page_number: Текущий номер страницы, начиная с которого будут нумероваться новые страницы
    :return: Последний номер страницы, использованный для сохранённой главы
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

    return end_page_number


def add_paragraph_indent(text, indent='    '):
    """
    Добавляет отступ (например, 4 пробела) в начало каждого абзаца (строки),
    кроме, возможно, первого. Под "абзацем" подразумевается текст,
    который идёт после символа перевода строки.

    Пример:
        "Первая строка без отступа
        Вторая строка
        Третья строка"

    После применения будет:
            "Первая строка с отступом
        Вторая строка
        Третья строка"

    :param text: Исходный текст
    :param indent: Строка, которая будет добавлена в качестве отступа (по умолчанию 4 пробела)
    :return: Текст, в котором каждый новый абзац начинается с отступа.
    """
    if not text:
        return ''

    # Регулярное выражение ищет перевод строки,
    # за которым *не* идёт пробельный символ (\s).
    # После такого перевода строки мы подставим indent.
    # Это значит: "\n(?!\s)" -> "найти \n, если дальше НЕ пробел/таб/и т.п."
    # result = re.sub(r'\n(?!\s)', "\n" + indent, text)
    # return result

    # Добавляем отступ к самому первому абзацу
    text = indent + text.lstrip()
    # Потом уже вставляем отступы перед всеми последующими абзацами
    result = re.sub(r'\n(?!\s)', "\n" + indent, text)
    return result

# Пример использования:
# def process_book_text(book, full_text):
#     # Разбиваем на главы
#     chapters_data, _ = split_text_into_chapters(full_text)
#     current_page_number = 1
#     # Для каждой главы делаем разбивку по 10 строк
#     for chapter_title, chapter_text in chapters_data:
#         pages = split_text_into_pages_by_lines(chapter_text, lines_per_page=10)
#         current_page_number = save_chapter(book, chapter_title, pages, current_page_number)
