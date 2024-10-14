from rest_framework import serializers

from text_service.models import Book, Genre, BookGenre, BookChapter


class BookSerializer(serializers.ModelSerializer):
    chapters = serializers.StringRelatedField(many=True, read_only=True)  # Added chapters field to BookSerializer

    class Meta:
        model = Book
        fields = '__all__'


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class BookGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookGenre
        fields = '__all__'


class BookChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookChapter
        fields = '__all__'
