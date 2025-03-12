
import uuid
from django.db import models


class Note(models.Model):
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

    def __str__(self):
        return self.title
