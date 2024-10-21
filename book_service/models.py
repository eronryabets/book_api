from django.db import models
import uuid


def book_cover_upload_path(instance, filename):
    # Путь для обложки книги: /user_id/cover/
    return f'{instance.user_id}/cover/{filename}'


class Book(models.Model):
    user_id = models.UUIDField(editable=False)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True, help_text="Краткое описание книги")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cover_image = models.ImageField(max_length=500, upload_to=book_cover_upload_path, null=True, blank=True,
                                    help_text='Загрузите обложку книги')
    language = models.CharField(max_length=10, help_text="Код языка в формате 'en-US', 'ru-RU' и т.д.")
    total_chapters = models.IntegerField(default=0)
    total_pages = models.IntegerField(default=0)
    genres = models.ManyToManyField('Genre', through='BookGenre', related_name='books')

    def __str__(self):
        return self.title


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('book', 'genre'),)

    def __str__(self):
        return f"{self.book.title} - {self.genre.name}"


class BookChapter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    start_page_number = models.IntegerField(null=True, blank=True)
    end_page_number = models.IntegerField(null=True, blank=True)
    chapter_title = models.CharField(
        max_length=255,
        default="Untitled Chapter",
        null=False,
        blank=True
    )

    def __str__(self):
        return f"{self.book.title} - {self.chapter_title or 'Глава с страницы ' + str(self.start_page_number)}"


class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapter = models.ForeignKey(BookChapter, on_delete=models.CASCADE, related_name='pages')
    page_number = models.IntegerField()
    content = models.TextField()

    def __str__(self):
        return f"Страница {self.page_number} главы {self.chapter.chapter_title or 'Без названия'}"
