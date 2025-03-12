import uuid
from django.db import models


class Tag(models.Model):
    """
    Модель тега для заметок.
    Поля:
      - id: Уникальный идентификатор тега.
      - name: Уникальное название тега.
      - created_at: Дата и время создания.
      - updated_at: Дата и время последнего обновления.
    Теги сортируются от самых новых к самым старым.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class Note(models.Model):
    """
    Модель заметки.
    Поля:
      - user_id: Идентификатор пользователя, которому принадлежит заметка.
      - id: Уникальный идентификатор заметки.
      - title: Заголовок заметки.
      - text: Текст заметки.
      - language: Код языка заметки.
      - created_at: Дата и время создания.
      - updated_at: Дата и время последнего обновления.
      - tags: Связь с тегами (ManyToManyField). Теги не удаляются при удалении заметки.
    """
    user_id = models.UUIDField(editable=False)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    text = models.TextField(null=True, blank=True)
    language = models.CharField(
        max_length=10,
        help_text="Код языка в формате 'en-US', 'ru-RU' и т.д."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, related_name='notes', blank=True)

    def __str__(self):
        return self.title
