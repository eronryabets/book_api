from django.urls import path, include
from rest_framework import routers
from .views import NoteViewSet, TagViewSet

router = routers.DefaultRouter()
router.register(r'notes', NoteViewSet, basename='notes')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
