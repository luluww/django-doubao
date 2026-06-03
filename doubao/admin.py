from django.contrib import admin

from .models import ImageGeneration, VideoGeneration


@admin.register(ImageGeneration)
class ImageGenerationAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("prompt",)


@admin.register(VideoGeneration)
class VideoGenerationAdmin(admin.ModelAdmin):
    list_display = ("id", "image_generation", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("prompt",)
