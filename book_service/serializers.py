import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import serializers


from book_service.models import Book, Genre, BookGenre, BookChapter


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class BookChapterSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookChapter
        fields = ['id', 'chapter_title']  # Включаем только id и title


class BookSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        write_only=True
    )
    genre_details = serializers.SerializerMethodField()
    chapters = BookChapterSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'user_id',
            'title',
            'description',  # Описание книги
            'file_path',
            'created_at',
            'updated_at',
            'cover_image',
            'genres',  # Для передачи списка жанров при создании/обновлении
            'genre_details',  # Для отображения связанных жанров при чтении
            'chapters'
        ]

    def get_genre_details(self, obj):
        # Получаем все связанные BookGenre и извлекаем Genre
        genres = obj.bookgenre_set.all().select_related('genre')
        return GenreSerializer([bg.genre for bg in genres], many=True).data

    def create(self, validated_data):
        genres = validated_data.pop('genres', [])
        book = Book.objects.create(**validated_data)
        # Создание записей в BookGenre
        BookGenre.objects.bulk_create([
            BookGenre(book=book, genre=genre) for genre in genres
        ])
        return book

    def update(self, instance, validated_data):
        # Получаем обложку из данных
        new_cover_image = validated_data.pop('cover_image', None)

        # Если обложка уже существовала, удаляем старую
        if new_cover_image and instance.cover_image and default_storage.exists(instance.cover_image.name):
            default_storage.delete(instance.cover_image.name)

        # Обновляем остальные поля книги
        genres = validated_data.pop('genres', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Если новая обложка предоставлена, сохраняем её в той же папке, что и книга
        if new_cover_image:
            # Используем относительный путь для сохранения файла обложки
            book_path = os.path.join(os.path.dirname(instance.file_path.replace('/media/', '')), str(instance.id))
            cover_image_filename = new_cover_image.name
            cover_image_path = os.path.join(book_path, cover_image_filename)

            # Сохраняем файл с использованием `default_storage`
            full_cover_image_path = default_storage.save(cover_image_path, ContentFile(new_cover_image.read()))
            instance.cover_image = full_cover_image_path
            instance.save()

        # Обновление жанров: удаление старых и добавление новых
        if genres is not None:
            instance.bookgenre_set.all().delete()
            BookGenre.objects.bulk_create([
                BookGenre(book=instance, genre=genre) for genre in genres
            ])

        return instance


class BookChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookChapter
        fields = '__all__'
