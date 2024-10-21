from django.core.files.storage import default_storage
from PyPDF2 import PdfReader
from .utils import save_chapter, detect_chapter_title, split_text_into_pages, clean_text


def process_pdf_file(book, full_original_path):
    try:
        pdf_reader = PdfReader(default_storage.open(full_original_path, 'rb'))
        total_pages_in_pdf = len(pdf_reader.pages)
        chapter_titles_detected = []
        total_chapters = 0
        total_pages = 0
        current_page_number = 1  # Инициализируем номер страницы с 1

        current_chapter_title = None
        current_chapter_text = ''
        for i in range(total_pages_in_pdf):
            page = pdf_reader.pages[i]
            page_text = page.extract_text()
            page_text = clean_text(page_text)

            # Проверяем наличие заголовка главы
            lines = page_text.split('\n')
            for line in lines:
                potential_title = detect_chapter_title(line)
                if potential_title:
                    # Если текущая глава не пустая, сохраняем её
                    if current_chapter_text:
                        pages = split_text_into_pages(current_chapter_text)
                        end_page_number = save_chapter(book, current_chapter_title, pages, current_page_number)
                        total_chapters += 1
                        total_pages += len(pages)
                        chapter_titles_detected.append(current_chapter_title or f"Глава {total_chapters}")
                        current_page_number = end_page_number + 1  # Обновляем номер страницы для следующей главы
                        current_chapter_text = ''
                    current_chapter_title = potential_title
                    break
            else:
                # Если заголовок не найден, добавляем текст страницы в текущую главу
                current_chapter_text += page_text + '\n'

        # Сохраняем последнюю главу
        if current_chapter_text:
            pages = split_text_into_pages(current_chapter_text)
            end_page_number = save_chapter(book, current_chapter_title, pages, current_page_number)
            total_chapters += 1
            total_pages += len(pages)
            chapter_titles_detected.append(current_chapter_title or f"Глава {total_chapters}")
            current_page_number = end_page_number + 1

        return {
            'success': True,
            'chapter_titles': chapter_titles_detected,
            'total_chapters': total_chapters,
            'total_pages': total_pages
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
