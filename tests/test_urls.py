# tests/test_urls.py
from django.urls import include, path

urlpatterns = [
    path("doubao/", include("doubao.urls", namespace="doubao")),
]
