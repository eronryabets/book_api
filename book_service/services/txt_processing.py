from django.core.files.storage import default_storage
from .utils import clean_text, split_text_into_chapters, save_chapter, split_text_into_pages_by_lines


def process_txt_file(book, full_original_path):
    """
    Обрабатывает загруженный TXT-файл: извлекает текст, очищает его, разбивает на главы и страницы,
    а затем сохраняет каждую главу в базе данных.

    :param book: Модель Book, к которой будут привязаны новые главы
    :param full_original_path: Полный путь к загруженному TXT-файлу
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
        current_page_number = 1  # Инициализируем номер страницы с 1

        # Сохраняем главы
        for chapter_title, chapter_text in chapters:
            pages = split_text_into_pages_by_lines(chapter_text)
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
