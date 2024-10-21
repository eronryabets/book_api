from rest_framework import routers
from django.urls import path, include
from .views import BookViewSet, BookChapterViewSet, GenreViewSet, PageViewSet

# Routers
router = routers.DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'chapters', BookChapterViewSet, basename='chapters')
router.register(r'genres', GenreViewSet, basename='genres')
router.register(r'pages', PageViewSet, basename='pages')

# URLs
urlpatterns = [
    path('', include(router.urls)),
]
