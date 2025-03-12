from django_filters import rest_framework as filters
from .models import Note, Tag


class NoteFilter(filters.FilterSet):
    """
    Фильтр для модели Note.
    Позволяет фильтровать заметки по тегам, языку, дате создания и дате обновления.
    """
    # Фильтр по названиям тегов
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__name',  # поле для фильтрации (название тега)
        to_field_name='name',  # фильтруем по полю name модели Tag
        queryset=Tag.objects.all(),  # набор тегов для фильтрации
        conjoined=True,  # заметка должна содержать ВСЕ указанные теги
        label='Tags'
    )

    created_at_after = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created At (After)'
    )
    created_at_before = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created At (Before)'
    )
    updated_at_after = filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte',
        label='Updated At (After)'
    )
    updated_at_before = filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte',
        label='Updated At (Before)'
    )

    class Meta:
        model = Note
        fields = {
            'language': ['exact'],
        }
