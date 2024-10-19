
from django.core.files.storage import default_storage
from PyPDF2 import PdfReader
from .utils import save_chapter, detect_chapter_title


def process_pdf_file(book, book_path, full_original_path):
    try:
        pdf_reader = PdfReader(default_storage.open(full_original_path, 'rb'))
        total_pages = len(pdf_reader.pages)
        chapter_number = 1
        chapter_start_page = 0
        current_chapter_title = None
        chapter_titles_detected = []

        for i in range(total_pages):
            page = pdf_reader.pages[i]
            page_text = page.extract_text()
            lines = page_text.split('\n')
            chapter_found = False
            for line in lines:
                potential_title = detect_chapter_title(line)
                if potential_title:
                    # Если обнаружен новый заголовок главы
                    if chapter_start_page != i or current_chapter_title is not None:
                        # Сохраняем предыдущую главу
                        save_chapter(
                            book, book_path, chapter_number,
                            chapter_start_page, i - 1,
                            current_chapter_title, pdf_reader=pdf_reader
                        )
                        chapter_number += 1
                    # Начинаем новую главу
                    chapter_start_page = i
                    current_chapter_title = potential_title
                    chapter_titles_detected.append(potential_title)
                    chapter_found = True
                    break  # Переходим к следующей странице после обнаружения заголовка
            if not chapter_found and current_chapter_title is None:
                current_chapter_title = f"Untitled Chapter {chapter_number}"

        # Сохраняем последнюю главу
        if chapter_start_page <= total_pages - 1:
            save_chapter(
                book, book_path, chapter_number,
                chapter_start_page, total_pages - 1,
                current_chapter_title, pdf_reader=pdf_reader
            )

        return {'success': True, 'chapter_titles': chapter_titles_detected}
    except Exception as e:
        return {'success': False, 'error': str(e)}