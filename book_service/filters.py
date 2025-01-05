import django_filters
from .models import Book, Genre


class BookFilter(django_filters.FilterSet):
    """
    Фильтр для модели Book, позволяющий искать книги по частичному совпадению названия (title)
    и выбирать книги сразу по нескольким жанрам (genres). Использует соединённую фильтрацию (conjoined=True),
    требуя, чтобы все выбранные жанры присутствовали у книги.

    :param title: Поиск по названию книги (регистр не учитывается)
    :param genres: Выбор книг, содержащих все указанные жанры
    """
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Book name'
    )
    genres = django_filters.ModelMultipleChoiceFilter(
        field_name='bookgenre__genre',
        queryset=Genre.objects.all(),
        to_field_name='name',
        label='Genres',
        conjoined=True  # Требует, чтобы все выбранные жанры присутствовали у книги
    )

    class Meta:
        model = Book
        fields = ['title', 'genres']
