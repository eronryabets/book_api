from django.db import models


def book_cover_upload_path(instance, filename):
    # Define the path for the cover image: /user_id/book_id/cover/
    return f'{instance.user_id}/{instance.id}/cover/{filename}'


class Book(models.Model):
    user_id = models.UUIDField(editable=False)
    id = models.UUIDField(primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, help_text='Path should be in the format: /<UUID user>/<UUID book>')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cover_image = models.ImageField(max_length=500, upload_to=book_cover_upload_path, null=True, blank=True,
                                    help_text='Upload a cover image for the book')

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
    id = models.UUIDField(primary_key=True, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    file_path = models.CharField(max_length=500, help_text='Full path format: /<UUID user>/<UUID book>/<file name>')
    start_page_number = models.IntegerField()
    end_page_number = models.IntegerField()
    chapter_title = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.book.title} - {self.chapter_title or 'Chapter starting at page ' + str(self.start_page_number)}"
