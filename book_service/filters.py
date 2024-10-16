import django_filters
from .models import Book, Genre


class BookFilter(django_filters.FilterSet):
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
