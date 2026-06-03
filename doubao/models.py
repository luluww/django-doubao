from django.db import models


class ImageGeneration(models.Model):
    """Record of each multi-image fusion generated final reference image"""

    reference_images = models.JSONField(
        default=list,
        verbose_name="Reference images list",
        help_text="Store list of reference image URLs or file paths (depending on implementation)",
    )
    prompt = models.TextField(verbose_name="Generation prompt")
    result_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Result image URL",
        help_text="Generated final image address",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Processing"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="pending",
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        verbose_name = "Image Generation Record"
        verbose_name_plural = "Image Generation Records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ImageGeneration #{self.id} - {self.status}"


class VideoGeneration(models.Model):
    """Record of a video generated from an image"""

    image_generation = models.ForeignKey(
        ImageGeneration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="videos",
        verbose_name="Source image record",
        help_text="Optional: if the video was created from a previously generated image, associate it",
    )
    prompt = models.TextField(verbose_name="Video description prompt")
    result_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Video result URL",
        help_text="Generated video address",
    )
    task_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Task ID",
        help_text="Doubao video generation task ID, used for polling",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending submission"),
            ("processing", "Processing"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="pending",
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        verbose_name = "Video Generation Record"
        verbose_name_plural = "Video Generation Records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"VideoGeneration #{self.id} - {self.status}"
