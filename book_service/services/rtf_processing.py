from django.core.files.storage import default_storage
from striprtf.striprtf import rtf_to_text
from .utils import split_text_into_chapters, save_chapter, split_text_into_pages


def process_rtf_file(book, full_original_path):
    """
    Обрабатывает загруженный RTF-файл, извлекает из него текст, разбивает его на главы и страницы.
    Затем сохраняет каждую главу в базе данных, вычисляя общее количество глав и страниц.

    :param book: Модель Book, к которой будут привязаны новые главы
    :param full_original_path: Полный путь к загруженному RTF-файлу
    :return: Словарь с ключами:
        - 'success': bool, успешность обработки
        - 'chapter_titles': список названий глав
        - 'total_chapters': общее количество глав
        - 'total_pages': общее количество страниц
        - 'error': текст ошибки (если возникла)
"""
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
        current_page_number = 1  # Инициализируем номер страницы с 1

        # Сохраняем главы
        for chapter_title, chapter_text in chapters:
            pages = split_text_into_pages(chapter_text)
            end_page_number = save_chapter(book, chapter_title, pages, current_page_number)
            total_chapters += 1
            pages_in_chapter = len(pages)
            total_pages += pages_in_chapter
            current_page_number = end_page_number + 1  # Обновляем номер страницы для следующей главы

        return {
            'success': True,
            'chapter_titles': chapter_titles_detected,
            'total_chapters': total_chapters,
            'total_pages': total_pages
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
