from django.db import models


class Book(models.Model):
    user_id = models.UUIDField(editable=False)
    id = models.UUIDField(primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class BookChapter(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    file_path = models.CharField(max_length=500)
    start_page_number = models.IntegerField()
    end_page_number = models.IntegerField()
    chapter_title = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.book.title} - {self.chapter_title or 'Chapter starting at page ' + str(self.start_page_number)}"


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


class Tag(models.Model):
    name = models.CharField(max_length=100)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='tags')

    def __str__(self):
        return f"{self.name} ({self.book.title})"
