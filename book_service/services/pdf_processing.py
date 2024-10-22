# pdf_processing.py

from django.core.files.storage import default_storage
from PyPDF2 import PdfReader
from .utils import save_chapter, detect_chapter_title, split_text_into_pages, clean_text
import logging

logger = logging.getLogger(__name__)


def process_pdf_file(book, full_original_path):
    try:
        pdf_reader = PdfReader(default_storage.open(full_original_path, 'rb'))
        total_pages_in_pdf = len(pdf_reader.pages)
        chapter_titles_detected = []
        total_chapters = 0
        total_pages = 0
        current_page_number = 1  # Начинаем с первой страницы

        current_chapter_title = None
        current_chapter_text = ''
        untitled_created = False  # Флаг для создания "Untitled Chapter"

        for i in range(total_pages_in_pdf):
            page = pdf_reader.pages[i]
            page_text = page.extract_text()
            if not page_text:
                logger.debug(f"Страница {i + 1} пуста, пропускаем.")
                continue  # Пропускаем пустые страницы
            page_text = clean_text(page_text)

            # Разделяем страницу на строки
            lines = page_text.split('\n')
            for line in lines:
                potential_title = detect_chapter_title(line)
                if potential_title:
                    logger.debug(f"Обнаружен заголовок главы: '{potential_title}' на странице {i + 1}")

                    # Если до этого была накоплена глава, сохраняем её
                    if current_chapter_title and current_chapter_text:
                        pages = split_text_into_pages(current_chapter_text)
                        end_page_number = save_chapter(book, current_chapter_title, pages, current_page_number)
                        total_chapters += 1
                        total_pages += len(pages)
                        chapter_titles_detected.append(current_chapter_title)
                        current_page_number = end_page_number + 1
                        current_chapter_text = ''

                    # Если заголовок найден первый раз и есть текст до него, создаём "Untitled Chapter"
                    if not untitled_created and not current_chapter_title and current_chapter_text:
                        logger.debug(
                            f"Создаём 'Untitled Chapter' с {len(current_chapter_text.splitlines())} строк до первой главы.")
                        pages = split_text_into_pages(current_chapter_text)
                        end_page_number = save_chapter(book, "Untitled Chapter", pages, current_page_number)
                        total_chapters += 1
                        total_pages += len(pages)
                        chapter_titles_detected.append("Untitled Chapter")
                        current_page_number = end_page_number + 1
                        current_chapter_text = ''
                        untitled_created = True

                    # Устанавливаем новый заголовок главы
                    current_chapter_title = potential_title
                else:
                    # Добавляем строку к текущему тексту главы
                    current_chapter_text += line + '\n'

        # После обработки всех страниц
        if current_chapter_text:
            if current_chapter_title:
                # Если есть текущая глава, добавляем текст в неё
                logger.debug(f"Добавляем оставшийся текст в главу '{current_chapter_title}'.")
                pages = split_text_into_pages(current_chapter_text)
                end_page_number = save_chapter(book, current_chapter_title, pages, current_page_number)
                total_chapters += 1
                total_pages += len(pages)
                chapter_titles_detected.append(current_chapter_title)
            else:
                # Если не было ни одной распознанной главы, сохраняем весь текст как "Untitled Chapter"
                logger.debug(f"Сохраняем весь текст как 'Untitled Chapter'.")
                pages = split_text_into_pages(current_chapter_text)
                end_page_number = save_chapter(book, "Untitled Chapter", pages, current_page_number)
                total_chapters += 1
                total_pages += len(pages)
                chapter_titles_detected.append("Untitled Chapter")

        logger.info(f"Обработка PDF завершена: {total_chapters} глав, {total_pages} страниц.")
        return {
            'success': True,
            'chapter_titles': chapter_titles_detected,
            'total_chapters': total_chapters,
            'total_pages': total_pages
        }
    except Exception as e:
        logger.error(f"Ошибка при обработке PDF: {str(e)}")
        return {'success': False, 'error': str(e)}
