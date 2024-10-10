from rest_framework import routers
from django.urls import path, include
from .views import BookViewSet, GenreViewSet, BookGenreViewSet, TagViewSet

# Routers
router = routers.DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'genres', GenreViewSet, basename='genres')
router.register(r'bookgenres', BookGenreViewSet, basename='bookgenres')
router.register(r'tags', TagViewSet, basename='tags')

# URLs
urlpatterns = [
    path('', include(router.urls)),
]
