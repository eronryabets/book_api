
from django.core.files.storage import default_storage
from lxml import etree
from .utils import split_text_into_chapters, save_chapter


def process_fb2_file(book, book_path, full_original_path):
    try:
        with default_storage.open(full_original_path, 'rb') as f:
            xml_content = f.read()

        parser = etree.XMLParser(encoding='utf-8', recover=True)
        tree = etree.fromstring(xml_content, parser=parser)

        # Извлекаем текстовое содержимое
        namespaces = {'fb2': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
        body = tree.find('fb2:body', namespaces)

        if body is None:
            return {'success': False, 'error': 'FB2 body not found'}

        # Получаем все абзацы
        paragraphs = body.findall('.//fb2:p', namespaces)
        text_content = '\n'.join([p.text for p in paragraphs if p.text])

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