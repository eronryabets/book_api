
from django.core.files.storage import default_storage
from striprtf.striprtf import rtf_to_text
from .utils import split_text_into_chapters, save_chapter


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