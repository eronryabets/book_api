from rest_framework import serializers
from .models import Note, Tag


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag.
    Возвращает id, name и временные метки создания/обновления.
    """

    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at', 'updated_at']


class NoteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Note.
    - Поле tags возвращается с помощью TagSerializer (read-only).
    - Поле tag_names (write-only) позволяет передавать список имен тегов,
      которые будут привязаны к заметке.
    """
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )

    class Meta:
        model = Note
        fields = [
            'id',
            'user_id',
            'title',
            'text',
            'language',
            'tags',
            'tag_names',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        note = Note.objects.create(**validated_data)
        tags = []
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        note.tags.set(tags)
        return note

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Если передан список tag_names, обновляем связь тегов
        if tag_names is not None:
            tags = []
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)

        return instance
