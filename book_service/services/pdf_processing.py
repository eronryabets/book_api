from django.core.files.storage import default_storage
from PyPDF2 import PdfReader
from .utils import (
    save_chapter,
    detect_chapter_title,
    split_text_into_pages_by_lines,
    clean_text
)
import re


def combine_sentences_in_threes(text, sentences_per_paragraph=3):
    """
    Берёт весь текст, разбивает на предложения по точкам,
    затем каждые три предложения склеивает в один «абзац».

    Пример:
      - Было: "Hello. This is test. One more. Next sentence."
      - Станет 2 абзаца:
         1) "Hello. This is test. One more."
         2) "Next sentence."
    """
    # Сначала максимально «чистим» текст от лишних переносов
    text = clean_text(text)

    # Разбиваем по точкам, чтобы каждое предложение оканчивалось точкой.
    # Используем lookbehind, чтобы точка оставалась в конце предложения,
    # а не «съедалась» регуляркой.
    # Затем strip, чтобы убрать пробелы/переносы вокруг.
    sentences = re.split(r'(?<=\.)', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    paragraphs = []
    buffer_ = []

    for s in sentences:
        buffer_.append(s)
        if len(buffer_) == sentences_per_paragraph:
            # Склеиваем 3 предложения в один абзац
            paragraph = " ".join(buffer_)
            paragraphs.append(paragraph)
            buffer_.clear()

    # Если остались «хвостовые» предложения, склеиваем их тоже
    if buffer_:
        paragraphs.append(" ".join(buffer_))

    # Склеим абзацы переводом строки: каждый абзац будет отдельной строкой
    result_text = "\n".join(paragraphs)
    return result_text


def process_pdf_file(book, full_original_path):
    """
    Обрабатывает загруженный PDF-файл, извлекает из него текст, определяет главы и страницы,
    а затем сохраняет каждую главу в базе данных. Может определить и пропустить оглавление (TOC).

    При сохранении глав:
      - Если распознали новый заголовок (chapter_title) —
        предыдущую главу (если была) сначала превращаем в абзацы по 3 предложения,
        потом разбиваем на страницы (по строкам) и сохраняем.
      - Если заголовок не распознали, продолжаем дописывать текст в текущую главу.
      - Если в конце не оказалось ни одного заголовка, сохраняем «Untitled Chapter».

    :param book: Модель Book, к которой будут привязаны новые главы
    :param full_original_path: Полный путь к загруженному PDF-файлу
    :return: Словарь с ключами:
        - 'success': bool, успешность обработки
        - 'chapter_titles': список названий глав
        - 'total_chapters': общее количество глав
        - 'total_pages': общее количество страниц
        - 'error': текст ошибки (если возникла)

    Используя split_text_into_pages_by_lines(paragraphs_text, lines_per_page=10)
    передаем с параметром lines_per_page=10 - 30 предложений = 10 абзацев.
    """
    try:
        pdf_reader = PdfReader(default_storage.open(full_original_path, 'rb'))
        total_pages_in_pdf = len(pdf_reader.pages)
        chapter_titles_detected = []
        total_chapters = 0
        total_pages = 0
        current_page_number = 1  # Начинаем с первой страницы

        current_chapter_title = None
        current_chapter_text = ''
        untitled_created = False  # Флаг, что мы уже сохранили "Untitled Chapter"
        toc_detected = False  # Флаг, что обнаружили оглавление (TOC) и прекратили обработку

        # Пороговое количество заголовков на странице, чтобы считать её TOC
        TOC_CHAPTER_THRESHOLD = 3

        for i in range(total_pages_in_pdf):
            if toc_detected:
                break  # Прекращаем обработку после обнаружения TOC

            page = pdf_reader.pages[i]
            page_text = page.extract_text()
            if not page_text:
                continue  # Пропускаем пустые страницы

            # 1) «Чистим» текст, чтобы лишние переносы не мешали
            page_text = clean_text(page_text)

            # 2) Смотрим, не является ли текущая страница оглавлением (TOC)
            lines = page_text.split('\n')
            chapter_count_on_page = 0

            for line in lines:
                potential_title = detect_chapter_title(line)
                if potential_title:
                    chapter_count_on_page += 1

            # Если на странице 3+ потенциальных заголовков => считаем, что это оглавление
            if chapter_count_on_page >= TOC_CHAPTER_THRESHOLD:
                toc_detected = True
                continue  # Пропускаем эту страницу без распознавания глав

            # 3) Если страница не TOC, разбираемся с заголовками и текстом
            for line in lines:
                potential_title = detect_chapter_title(line)
                if potential_title:
                    # Если есть накопленная глава, сначала сохраним её
                    if current_chapter_title and current_chapter_text:
                        # Склеиваем 3 предложения в абзац
                        paragraphs_text = combine_sentences_in_threes(current_chapter_text)
                        # Разбиваем «абзацный» текст на страницы
                        pages = split_text_into_pages_by_lines(paragraphs_text, lines_per_page=10)
                        end_page_number = save_chapter(book, current_chapter_title, pages, current_page_number)
                        total_chapters += 1
                        total_pages += len(pages)
                        chapter_titles_detected.append(current_chapter_title)
                        current_page_number = end_page_number + 1
                        current_chapter_text = ''  # Сброс текста

                    # Если заголовок найден в первый раз, но до него уже был текст (без заголовка)
                    if not untitled_created and not current_chapter_title and current_chapter_text:
                        paragraphs_text = combine_sentences_in_threes(current_chapter_text)
                        pages = split_text_into_pages_by_lines(paragraphs_text, lines_per_page=10)
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
                    # (позже всё равно склеим «переносы» в предложения)
                    current_chapter_text += line + ' '

        # 4) После обработки всех страниц, если что-то осталось в current_chapter_text
        if current_chapter_text:
            if current_chapter_title:
                # Склеиваем 3 предложения в абзацы
                paragraphs_text = combine_sentences_in_threes(current_chapter_text)
                pages = split_text_into_pages_by_lines(paragraphs_text, lines_per_page=10)
                end_page_number = save_chapter(book, current_chapter_title, pages, current_page_number)
                total_chapters += 1
                total_pages += len(pages)
                chapter_titles_detected.append(current_chapter_title)
            else:
                # Не было ни одного найденного заголовка
                paragraphs_text = combine_sentences_in_threes(current_chapter_text)
                pages = split_text_into_pages_by_lines(paragraphs_text, lines_per_page=10)
                end_page_number = save_chapter(book, "Untitled Chapter", pages, current_page_number)
                total_chapters += 1
                total_pages += len(pages)
                chapter_titles_detected.append("Untitled Chapter")

        return {
            'success': True,
            'chapter_titles': chapter_titles_detected,
            'total_chapters': total_chapters,
            'total_pages': total_pages
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}
