from django.urls import path, include
from rest_framework import routers
from .views import NoteViewSet, TagViewSet, BulkNoteActionView

router = routers.DefaultRouter()
router.register(r'notes', NoteViewSet, basename='notes')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('notes/bulk_action/', BulkNoteActionView.as_view(), name='bulk_note_action'),
    path('', include(router.urls)),
]
