import ebooklib
from django.core.files.storage import default_storage
from ebooklib import epub
from bs4 import BeautifulSoup
from .utils import clean_text, save_chapter, split_text_into_pages


def process_epub_file(book, full_original_path):
    try:
        epub_book = epub.read_epub(default_storage.path(full_original_path))
        chapter_titles_detected = []
        total_chapters = 0
        total_pages = 0

        # Получаем список элементов документа
        items = list(epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

        for item in items:
            content = item.get_content()
            soup = BeautifulSoup(content, 'html.parser')

            # Попытка найти заголовок главы
            chapter_title = None
            for header_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                header = soup.find(header_tag)
                if header and header.get_text():
                    chapter_title = header.get_text().strip()
                    break

            # Если заголовок не найден, используем название файла
            if not chapter_title:
                chapter_title = item.get_name()

            text_content = soup.get_text()
            text_content = clean_text(text_content)

            # Разбиваем текст главы на страницы
            pages = split_text_into_pages(text_content)

            # Сохраняем главу и страницы
            chapter = save_chapter(book, chapter_title, pages)
            total_chapters += 1
            total_pages += len(pages)
            chapter_titles_detected.append(chapter_title)

        return {
            'success': True,
            'chapter_titles': chapter_titles_detected,
            'total_chapters': total_chapters,
            'total_pages': total_pages
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
