# django-doubao

A reusable Django app to generate AI images and videos using ByteDance's **Doubao API**.

## Features

- 🎨 **Multi‑image fusion** – create one image from several reference images
- 🎬 **Image‑to‑video generation** – turn images into short videos (5–12 sec)
- 📐 Support for multiple aspect ratios and resolutions
- 🔌 Easy integration with Django projects

## Requirements

- Python ≥ 3.9
- Django ≥ 6.0
- `requests` ≥ 2.34.2

## Installation

```bash
pip install django-doubao
```

## Configuration

1. Add `doubao` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'doubao',
]
```

2. Set your Doubao API key (obtain it from [Volcano Ark](https://console.volcengine.com/ark)):

```python
# settings.py
DOUBAO_API_KEY = "your-api-key-here"
```

3. Include the app’s URLs in your project:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('doubao/', include('doubao.urls')),
]
```

## Supported models

Currently the app is tested and verified with the following Doubao models:

- **Image generation**: `doubao-seedream-4-5-251128`
- **Video generation**: `doubao-seedance-1-5-pro-251215`

The app’s internal parameters (duration, resolution, ratio, etc.) are tailored specifically to these models.  
Future versions may add support for additional models (e.g. newer Seedream or Seedance versions), which may introduce different parameter sets and not be a simple model ID swap.

## Usage

### Image generation

1. Visit `/doubao/image/` (or the URL you configured).
2. Upload one or more reference images.
3. Write a prompt describing the desired output.
4. Choose a size and click **Generate Image**.
5. Download the result or proceed to video generation.

### Video generation

1. From the image generation page, click **Generate Video** (the image ID is passed automatically).
2. Alternatively, open `/doubao/video/` directly and upload an image.
3. Enter a video prompt, select duration (5–12 seconds) and aspect ratio.
4. Click **Generate Video** – the app will poll the API and return the video URL along with the last frame.
5. Download the video and/or the last frame image.

### Programmatic usage

You can also call the underlying functions directly:

```python
from doubao.utils import generate_image, submit_video_task, poll_video_result

# Generate an image from multiple reference images
image_url = generate_image(
    prompt="a girl with a cat",
    image_list=["https://example.com/ref1.jpg", "https://example.com/ref2.jpg"]
)

# Submit a video task
task_id = submit_video_task(
    image_input=image_url,
    prompt="the girl laughs",
    duration=5
)

# Poll for the result
video_url, last_frame_url = poll_video_result(task_id)
```

## License

MIT
