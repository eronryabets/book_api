
from django.core.files.storage import default_storage
from ebooklib import epub
from bs4 import BeautifulSoup
from .utils import clean_text, save_chapter, split_text_into_chapters


def process_epub_file(book, book_path, full_original_path):
    try:
        epub_book = epub.read_epub(default_storage.path(full_original_path))
        text_content = ''
        for item in epub_book.get_items_of_type(epub.ITEM_DOCUMENT):
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
