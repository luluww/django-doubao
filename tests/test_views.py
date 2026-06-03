from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class GenerateImageViewTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@example.com"
        )
        # 确保客户端登录成功
        self.client.login(username="admin", password="admin123")

    def test_get_image_view_returns_template(self):
        response = self.client.get(reverse("doubao:generate_image"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "doubao/generate_image.html")
