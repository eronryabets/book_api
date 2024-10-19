
from django.core.files.storage import default_storage
from .utils import clean_text, split_text_into_chapters, save_chapter


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