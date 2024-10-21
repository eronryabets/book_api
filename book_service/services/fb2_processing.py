from django.core.files.storage import default_storage
from lxml import etree
from .utils import split_text_into_chapters, split_text_into_pages, save_chapter, clean_text


def process_fb2_file(book, full_original_path):
    try:
        with default_storage.open(full_original_path, 'rb') as f:
            xml_content = f.read()

        parser = etree.XMLParser(encoding='utf-8', recover=True)
        tree = etree.fromstring(xml_content, parser=parser)

        namespaces = {'fb2': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
        body = tree.find('fb2:body', namespaces)

        if body is None:
            return {'success': False, 'error': 'FB2 body not found'}

        # Извлекаем весь текст из тела документа
        paragraphs = body.findall('.//fb2:p', namespaces)
        text_content = '\n'.join([p.text for p in paragraphs if p.text])

        # Очищаем текст от лишних пустых строк
        text_content = clean_text(text_content)

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
