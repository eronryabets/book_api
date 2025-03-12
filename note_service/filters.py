import django_filters
from .models import Note


class NoteFilter(django_filters.FilterSet):
    class Meta:
        model = Note
        fields = {
            'language': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
            'updated_at': ['exact', 'gte', 'lte'],
        }
