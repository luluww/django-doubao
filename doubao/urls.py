from django.urls import include, path

from . import views

app_name = "doubao"

urlpatterns = [
    path(
        "image/",
        include(
            [
                path("", views.generate_image_view, name="generate_image"),
                path(
                    "get-url/<int:image_id>/", views.get_image_url, name="get_image_url"
                ),
            ]
        ),
    ),
    path("video/", views.generate_video_view, name="generate_video"),
]
