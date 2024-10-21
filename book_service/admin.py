from django.contrib import admin
from .models import Book, BookChapter, Genre, BookGenre, Page


class BookGenreInline(admin.TabularInline):
    model = BookGenre
    extra = 1
    autocomplete_fields = ['genre']
    verbose_name = "Жанр"
    verbose_name_plural = "Жанры"


class PageInline(admin.TabularInline):
    model = Page
    extra = 1
    readonly_fields = ('id',)
    fields = ('page_number', 'content')
    show_change_link = True


class BookChapterInline(admin.TabularInline):
    model = BookChapter
    extra = 1
    readonly_fields = ('id',)
    fields = ('chapter_title', 'start_page_number', 'end_page_number')
    show_change_link = True
    # Вложенные инлайны не поддерживаются, поэтому страницы управляются отдельно


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_id', 'language', 'total_chapters', 'total_pages', 'created_at', 'updated_at')
    search_fields = ('title', 'genres__name', 'language')
    list_filter = ('language', 'genres__name')
    readonly_fields = ('id', 'total_chapters', 'total_pages', 'created_at', 'updated_at')
    inlines = [BookGenreInline, BookChapterInline]
    # Удален filter_horizontal, так как он несовместим с промежуточной моделью


@admin.register(BookChapter)
class BookChapterAdmin(admin.ModelAdmin):
    list_display = ('book', 'chapter_title', 'start_page_number', 'end_page_number')
    search_fields = ('book__title', 'chapter_title')
    list_filter = ('book',)
    readonly_fields = ('id',)
    inlines = [PageInline]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'page_number')
    search_fields = ('chapter__book__title', 'chapter__chapter_title', 'content')
    list_filter = ('chapter__book',)
    readonly_fields = ('id',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
