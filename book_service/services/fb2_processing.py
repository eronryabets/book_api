from django.core.files.storage import default_storage
from lxml import etree
from .utils import split_text_into_chapters, split_text_into_pages, save_chapter


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

        sections = body.findall('fb2:section', namespaces)
        total_pages = 0
        chapter_titles_detected = []
        total_chapters = 0

        for section in sections:
            chapter_title_elem = section.find('fb2:title/fb2:p', namespaces)
            chapter_title = chapter_title_elem.text if chapter_title_elem is not None else None

            paragraphs = section.findall('.//fb2:p', namespaces)
            chapter_text = '\n'.join([p.text for p in paragraphs if p.text])

            pages = split_text_into_pages(chapter_text)

            chapter = save_chapter(book, chapter_title, pages)
            total_chapters += 1
            total_pages += len(pages)
            chapter_titles_detected.append(chapter_title or f"Глава {total_chapters}")

        return {'success': True, 'chapter_titles': chapter_titles_detected, 'total_chapters': total_chapters,
                'total_pages': total_pages}
    except Exception as e:
        return {'success': False, 'error': str(e)}

