from django.contrib import admin

from book_service.models import Book, Genre, BookGenre, BookChapter


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_id', 'created_at', 'updated_at')
    search_fields = ('title', 'genre')


@admin.register(BookChapter)
class BookChapterAdmin(admin.ModelAdmin):
    list_display = ('book', 'chapter_title', 'start_page_number', 'end_page_number')
    search_fields = ('book__title', 'chapter_title')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

