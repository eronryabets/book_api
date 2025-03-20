from django_filters import rest_framework as filters
from .models import Note


class PartialTagFilter(filters.Filter):
    """
    Фильтр для частичного поиска по тегам.

    Этот фильтр извлекает все значения параметра 'tags' из данных запроса и применяет фильтрацию к QuerySet.
    Он проверяет наличие непустых значений в параметрах, а затем для каждого тега выполняет фильтрацию по подстроке
    (case-insensitive) в поле tags__name.

    Как работает:
    1. Извлекается список значений параметра 'tags' с помощью self.parent.data.getlist('tags').
    2. Если список пуст или все значения состоят только из пробелов, фильтрация не применяется и возвращается
    исходный QuerySet.
    3. Для каждого переданного тега:
       - Значение очищается от лишних пробелов.
       - QuerySet фильтруется с использованием метода filter(tags__name__icontains=tag),
         что позволяет найти объекты, у которых имя тега содержит данное значение (без учёта регистра).
    4. Итоговый отфильтрованный QuerySet возвращается.

    Пример использования:
      Если в URL присутствует параметр tags, например:
        ?tags=python,redux
      Фильтр выполнит последовательное применение:
        qs = qs.filter(tags__name__icontains='python').filter(tags__name__icontains='redux')
    """
    def filter(self, qs, value):
        # Получаем список всех значений параметра 'tags' из запроса
        raw_tags = self.parent.data.getlist('tags')
        # Если параметр отсутствует или состоит только из пустых значений – фильтр не применяется
        if not raw_tags or all(not t.strip() for t in raw_tags):
            return qs
        # Для каждого переданного значения применяем фильтрацию по подстроке
        for tag in raw_tags:
            tag = tag.strip()
            qs = qs.filter(tags__name__icontains=tag)
        return qs


class NoteFilter(filters.FilterSet):
    # Используем наш кастомный фильтр для тегов
    tags = PartialTagFilter()

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
