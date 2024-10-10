from rest_framework import routers
from django.urls import path, include
from .views import BookViewSet, GenreViewSet, BookGenreViewSet, TagViewSet

# Routers
router = routers.DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'bookgenres', BookGenreViewSet)
router.register(r'tags', TagViewSet)

# URLs
urlpatterns = [
    path('', include(router.urls)),
]
