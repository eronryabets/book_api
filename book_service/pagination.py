from rest_framework.pagination import PageNumberPagination


class BookPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'  # Позволяет клиенту задавать размер страницы через параметр запроса
    max_page_size = 24
