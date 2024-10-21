from django.core.files.storage import default_storage
from striprtf.striprtf import rtf_to_text
from .utils import split_text_into_chapters, save_chapter, split_text_into_pages


def process_rtf_file(book, full_original_path):
    try:
        with default_storage.open(full_original_path, 'rb') as f:
            bytes_content = f.read()
            try:
                rtf_content = bytes_content.decode('utf-8')
            except UnicodeDecodeError:
                rtf_content = bytes_content.decode('latin1')

        # Конвертируем RTF в текст
        text_content = rtf_to_text(rtf_content)

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
