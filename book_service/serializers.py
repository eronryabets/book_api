import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import serializers

from book_service.models import Book, Genre, BookGenre, BookChapter, Page


class GenreSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Genre. Возвращает идентификатор и название жанра.
    """

    class Meta:
        model = Genre
        fields = ['id', 'name']


class BookChapterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели BookChapter. Включает ключевые поля,
    связанные с главой (id, книга, начальный и конечный номера страниц, заголовок).
    """

    class Meta:
        model = BookChapter
        fields = ['id', 'book', 'start_page_number', 'end_page_number', 'chapter_title']


class BookSerializer(serializers.ModelSerializer):
    """
        Сериализатор для модели Book. Помимо основных полей книги,
        поддерживает работу со связанными жанрами и главами.
        Позволяет создавать и обновлять книгу вместе с указанием жанров и обложки.
    """
    user_id = serializers.UUIDField(read_only=True)  # Теперь поле только для чтения
    genres = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True
    )
    genre_details = serializers.SerializerMethodField()
    chapters = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id',
            'user_id',
            'title',
            'description',
            'created_at',
            'updated_at',
            'cover_image',
            'language',
            'total_chapters',
            'total_pages',
            'genres',
            'genre_details',
            'chapters'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']

    def get_genre_details(self, obj):
        genres = obj.bookgenre_set.all().select_related('genre')
        return GenreSerializer([bg.genre for bg in genres], many=True).data

    def get_chapters(self, obj):
        chapters = obj.chapters.all().order_by('start_page_number')
        return BookChapterSerializer(chapters, many=True, read_only=True).data

    def create(self, validated_data):
        genres = validated_data.pop('genres', [])
        book = Book.objects.create(**validated_data)
        BookGenre.objects.bulk_create([
            BookGenre(book=book, genre=genre) for genre in genres
        ])
        return book

    def update(self, instance, validated_data):
        new_cover_image = validated_data.pop('cover_image', None)
        if new_cover_image and instance.cover_image and default_storage.exists(instance.cover_image.name):
            default_storage.delete(instance.cover_image.name)

        genres = validated_data.pop('genres', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if new_cover_image:
            cover_image_filename = new_cover_image.name
            cover_image_path = os.path.join(str(instance.user_id), 'cover', cover_image_filename)
            full_cover_image_path = default_storage.save(cover_image_path, ContentFile(new_cover_image.read()))
            instance.cover_image = full_cover_image_path
            instance.save()

        if genres is not None:
            instance.bookgenre_set.all().delete()
            BookGenre.objects.bulk_create([
                BookGenre(book=instance, genre=genre) for genre in genres
            ])

        return instance


class PageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Page, включающий информацию о главе, номере и тексте страницы.
    """

    class Meta:
        model = Page
        fields = ['id', 'chapter', 'page_number', 'content']  # id нужно для bulk действия теперь
