import ebooklib
from django.core.files.storage import default_storage
from ebooklib import epub
from bs4 import BeautifulSoup
from .utils import clean_text, split_text_into_chapters, split_text_into_pages, save_chapter


def process_epub_file(book, full_original_path):
    try:
        epub_full_path = default_storage.path(full_original_path)
        epub_book = epub.read_epub(epub_full_path)
        chapter_titles_detected = []
        total_chapters = 0
        total_pages = 0

        # Извлекаем весь текст из EPUB файла
        text_content = ''
        for item in epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content = item.get_content()
            soup = BeautifulSoup(content, 'html.parser')
            text_content += soup.get_text() + '\n'

        # Проверяем, что текст был извлечен
        if not text_content.strip():
            return {'success': False, 'error': 'Не удалось извлечь текст из EPUB файла'}

        # Очищаем текст от лишних пустых строк
        text_content = clean_text(text_content)

        # Разбиваем текст на главы
        chapters, chapter_titles_detected = split_text_into_chapters(text_content)

        # Проверяем, что главы были обнаружены
        if not chapters:
            return {'success': False, 'error': 'Не удалось разделить текст на главы'}

        # Сохраняем главы
        for chapter_title, chapter_text in chapters:
            pages = split_text_into_pages(chapter_text)
            chapter = save_chapter(book, chapter_title, pages)
            total_chapters += 1
            total_pages += len(pages)

        return {
            'success': True,
            'chapter_titles': chapter_titles_detected,
            'total_chapters': total_chapters,
            'total_pages': total_pages
        }
    except Exception as e:
        # Логируем полную информацию об исключении
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
