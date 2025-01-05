from rest_framework.pagination import PageNumberPagination


class BookPagination(PageNumberPagination):
    """
    Настраиваем пагинацию для списка книг:
    - По умолчанию показывает 6 объектов на странице
    - Позволяет клиенту указать собственный размер страницы через параметр 'page_size'
    - Максимальное количество на одной странице — 24
    """
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 24
