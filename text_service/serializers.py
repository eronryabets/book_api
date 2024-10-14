from rest_framework import serializers
from text_service.models import Book, Genre, BookGenre, BookChapter


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class BookSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        write_only=True
    )
    genre_details = GenreSerializer(source='bookgenre_set__genre', many=True, read_only=True)
    chapters = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'user_id',
            'title',
            'file_path',
            'created_at',
            'updated_at',
            'cover_image',
            'genres',  # Для передачи списка жанров при создании/обновлении
            'genre_details',  # Для отображения связанных жанров при чтении
            'chapters'
        ]

    def create(self, validated_data):
        genres = validated_data.pop('genres', [])
        book = Book.objects.create(**validated_data)
        # Создание записей в BookGenre
        BookGenre.objects.bulk_create([
            BookGenre(book=book, genre=genre) for genre in genres
        ])
        return book

    def update(self, instance, validated_data):
        genres = validated_data.pop('genres', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if genres is not None:
            # Обновление жанров: удаление старых и добавление новых
            instance.bookgenre_set.all().delete()
            BookGenre.objects.bulk_create([
                BookGenre(book=instance, genre=genre) for genre in genres
            ])
        return instance


class BookChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookChapter
        fields = '__all__'
