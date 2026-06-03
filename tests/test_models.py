from django.contrib.auth import get_user_model
from django.test import TestCase

from doubao.models import ImageGeneration, VideoGeneration

User = get_user_model()


class ImageGenerationModelTest(TestCase):
    def test_create_image_generation(self):
        img_gen = ImageGeneration.objects.create(prompt="a cat", status="pending")
        self.assertEqual(img_gen.status, "pending")
        self.assertIsNotNone(img_gen.created_at)
        self.assertEqual(str(img_gen), f"ImageGeneration #{img_gen.id} - pending")

    def test_video_generation_relation(self):
        img_gen = ImageGeneration.objects.create(prompt="a dog")
        video_gen = VideoGeneration.objects.create(
            image_generation=img_gen, prompt="a dog running", status="pending"
        )
        self.assertEqual(video_gen.image_generation, img_gen)
        self.assertIn(video_gen, img_gen.videos.all())
