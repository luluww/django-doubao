# tests/test_utils.py
import base64
import tempfile
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from doubao.utils import (
    DOUBAO_MODELS,
    _generate,
    _get_headers,
    encode_image_to_data_url,
    generate_image,
    poll_video_result,
    submit_video_task,
)


class EncodeImageToDataUrlTest(SimpleTestCase):
    def test_encode_from_file_object(self):
        # Create a small image content (fake binary)
        image_content = b"fakeimagebinary"
        uploaded_file = SimpleUploadedFile(
            name="test.jpg", content=image_content, content_type="image/jpeg"
        )
        data_url = encode_image_to_data_url(uploaded_file)
        expected_base64 = base64.b64encode(image_content).decode("utf-8")
        self.assertEqual(data_url, f"data:image/jpeg;base64,{expected_base64}")

    def test_encode_from_file_path(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            tmp.write(b"pngcontent")
            tmp.flush()
            data_url = encode_image_to_data_url(tmp.name)
            expected_base64 = base64.b64encode(b"pngcontent").decode("utf-8")
            self.assertEqual(data_url, f"data:image/png;base64,{expected_base64}")

    def test_mime_type_from_extension(self):
        # Use a file-like object with .webp extension but no content_type
        class MockFile:
            name = "test.webp"

            def read(self):
                return b"fake"

            def seek(self, pos):
                pass

        data_url = encode_image_to_data_url(MockFile())
        self.assertTrue(data_url.startswith("data:image/webp;base64,"))


class GenerateFunctionTest(SimpleTestCase):
    @patch("doubao.utils.requests.post")
    def test_generate_post_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "ok"}
        mock_post.return_value = mock_response

        result = _generate("https://example.com/api", {"key": "value"})
        self.assertEqual(result, {"data": "ok"})
        mock_post.assert_called_once_with(
            "https://example.com/api",
            json={"key": "value"},
            headers=_get_headers(),
        )

    @patch("doubao.utils.requests.get")
    def test_generate_get_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "succeeded"}
        mock_get.return_value = mock_response

        result = _generate("https://example.com/task/123")
        self.assertEqual(result, {"status": "succeeded"})
        mock_get.assert_called_once_with(
            "https://example.com/task/123",
            headers=_get_headers(),
        )

    @patch("doubao.utils.requests.post")
    def test_generate_failure_raises(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(RuntimeError, "Request failed: 400, Bad Request"):
            _generate("https://example.com/api", {"key": "value"})


@patch("doubao.utils._generate")
class GenerateImageTest(SimpleTestCase):
    def test_generate_image_calls_correct_payload(self, mock_generate):
        mock_generate.return_value = {"data": [{"url": "https://result.jpg"}]}
        result = generate_image(
            prompt="a cat",
            image_list=["data:image/jpeg;base64,...", "data:image/jpeg;base64,..."],
            size="1024x1024",
            sequential_image_generation="auto",
            response_format="url",
        )
        self.assertEqual(result, "https://result.jpg")
        mock_generate.assert_called_once_with(
            DOUBAO_MODELS["image"]["url"],
            {
                "model": DOUBAO_MODELS["image"]["model"],
                "prompt": "a cat",
                "image": ["data:image/jpeg;base64,...", "data:image/jpeg;base64,..."],
                "sequential_image_generation": "auto",
                "size": "1024x1024",
                "watermark": False,
                "response_format": "url",
            },
        )


@patch("doubao.utils._generate")
class SubmitVideoTaskTest(SimpleTestCase):
    def test_submit_video_task_defaults(self, mock_generate):
        mock_generate.return_value = {"id": "task-123"}
        task_id = submit_video_task(
            image_input="https://example.com/img.jpg", prompt="a dog running"
        )
        self.assertEqual(task_id, "task-123")
        mock_generate.assert_called_once_with(
            DOUBAO_MODELS["video"]["url"],
            {
                "model": DOUBAO_MODELS["video"]["model"],
                "content": [
                    {"type": "text", "text": "a dog running"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/img.jpg"},
                    },
                ],
                "duration": DOUBAO_MODELS["video"]["max_duration"],
                "resolution": DOUBAO_MODELS["video"]["resolutions"][0],
                "return_last_frame": True,
                "generate_audio": True,
                "draft": False,
                "ratio": DOUBAO_MODELS["video"]["ratios"][0],
            },
        )

    def test_submit_video_task_custom_params(self, mock_generate):
        mock_generate.return_value = {"id": "task-456"}
        task_id = submit_video_task(
            image_input="data:image/png;base64,...",
            prompt="a cat sleeping",
            duration=8,
            resolution="720p",
            ratio="1:1",
        )
        self.assertEqual(task_id, "task-456")
        payload = mock_generate.call_args[0][1]
        self.assertEqual(payload["duration"], 8)
        self.assertEqual(payload["resolution"], "720p")
        self.assertEqual(payload["ratio"], "1:1")


@patch("doubao.utils._generate")
@patch("doubao.utils.time.sleep", return_value=None)
class PollVideoResultTest(SimpleTestCase):
    def test_poll_success(self, mock_sleep, mock_generate):
        mock_generate.side_effect = [
            {"status": "pending"},
            {
                "status": "succeeded",
                "content": {
                    "video_url": "https://video.mp4",
                    "last_frame_url": "https://frame.jpg",
                },
            },
        ]
        video_url, last_frame = poll_video_result("task-123", interval=1, timeout=10)
        self.assertEqual(video_url, "https://video.mp4")
        self.assertEqual(last_frame, "https://frame.jpg")
        self.assertEqual(mock_generate.call_count, 2)
        mock_generate.assert_any_call(f"{DOUBAO_MODELS['video']['url']}/task-123")

    def test_poll_failed(self, mock_sleep, mock_generate):
        mock_generate.return_value = {"status": "failed", "error": "some error"}
        with self.assertRaisesRegex(Exception, "Failed to generate video"):
            poll_video_result("task-fail", interval=1, timeout=10)

    def test_poll_timeout(self, mock_sleep, mock_generate):
        mock_generate.return_value = {"status": "pending"}
        with self.assertRaisesRegex(TimeoutError, "overtime"):
            poll_video_result("task-timeout", interval=1, timeout=2)
        # Ensure sleep was called at least once
        self.assertGreaterEqual(mock_sleep.call_count, 1)
