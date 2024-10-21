from django.core.files.storage import default_storage
from .utils import clean_text, split_text_into_chapters, save_chapter, split_text_into_pages


def process_txt_file(book, full_original_path):
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

        total_chapters = 0
        total_pages = 0

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
        return {'success': False, 'error': str(e)}
