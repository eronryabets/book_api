from django.contrib import admin

from text_service.models import Book, Genre, BookGenre, Tag, BookChapter


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_id', 'genre', 'created_at', 'updated_at')
    search_fields = ('title', 'genre')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(BookGenre)
class BookGenreAdmin(admin.ModelAdmin):
    list_display = ('book', 'genre')
    search_fields = ('book__title', 'genre__name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'book')
    search_fields = ('name', 'book__title')

@admin.register(BookChapter)
class BookChapterAdmin(admin.ModelAdmin):
    list_display = ('book', 'chapter_title', 'start_page_number', 'end_page_number')
    search_fields = ('book__title', 'chapter_title')
