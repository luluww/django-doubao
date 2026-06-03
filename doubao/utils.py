import base64
import os
import time

import requests
from django.conf import settings

DOUBAO_API_KEY = getattr(settings, "DOUBAO_API_KEY", None)
DOUBAO_MODELS = {
    "image": {
        "model": "doubao-seedream-4-5-251128",
        "url": "https://ark.cn-beijing.volces.com/api/v3/images/generations",
        "sizes": [
            "2048x2048",
            "1728x2304",
            "2304x1728",
            "2848x1600",
            "1600x2848",
            "2496x1664",
            "1664x2496",
            "3136x1344",
            "4096x4096",
            "3520x4704",
            "4704x3520",
            "5504x3040",
            "3040x5504",
            "3328x4992",
            "4992x3328",
            "6240x2656",
        ],
    },
    "video": {
        "model": "doubao-seedance-1-5-pro-251215",
        "url": "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
        "ratios": ["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"],
        "max_duration": 12,
        "resolutions": ["480p", "720p", "1024p"],
    },
}


def _get_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
    }


def encode_image_to_data_url(image_file) -> str:
    MIME_MAP = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".gif": "image/gif",
    }

    if hasattr(image_file, "read"):
        image_bytes = image_file.read()
        if hasattr(image_file, "seek"):
            image_file.seek(0)

        content_type = getattr(image_file, "content_type", None)
        if not content_type:
            filename = getattr(image_file, "name", "")
            ext = os.path.splitext(filename)[1].lower()
            content_type = MIME_MAP.get(ext, "image/jpeg")
    else:
        with open(image_file, "rb") as f:
            image_bytes = f.read()
        ext = os.path.splitext(image_file)[1].lower()
        content_type = MIME_MAP.get(ext, "image/jpeg")

    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{content_type};base64,{base64_str}"


def _generate(url, payload=None):
    headers = _get_headers()
    if payload:
        resp = requests.post(url, json=payload, headers=headers)
    else:
        resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise RuntimeError(f"Request failed: {resp.status_code}, {resp.text}")


def generate_image(
    prompt,
    image_list,
    size=DOUBAO_MODELS["image"]["sizes"][0],
    sequential_image_generation="disabled",
    response_format="url",
):
    payload = {
        "model": DOUBAO_MODELS["image"]["model"],
        "prompt": prompt,
        "image": image_list,
        "sequential_image_generation": sequential_image_generation,
        "size": size,
        "watermark": False,
        "response_format": response_format,
    }

    result = _generate(DOUBAO_MODELS["image"]["url"], payload)
    return result["data"][0]["url"]


def submit_video_task(
    image_input: str,
    prompt: str,
    duration: int = DOUBAO_MODELS["video"]["max_duration"],
    resolution: str = DOUBAO_MODELS["video"]["resolutions"][0],
    ratio: str = DOUBAO_MODELS["video"]["ratios"][0],
) -> str:
    payload = {
        "model": DOUBAO_MODELS["video"]["model"],
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_input}},
        ],
        "duration": duration,
        "resolution": resolution,
        "return_last_frame": True,
        "generate_audio": True,
        "draft": False,
        "ratio": ratio,
    }
    result = _generate(DOUBAO_MODELS["video"]["url"], payload)
    return result["id"]


def poll_video_result(task_id: str, interval: int = 5, timeout: int = 120) -> str:
    """
    Poll for video generation result.
    :param task_id: Task ID
    :param interval: Polling interval (seconds)
    :param timeout: Timeout duration (seconds)
    :return: Video URL
    """
    url = f"{DOUBAO_MODELS['video']['url']}/{task_id}"
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError("overtime")
        result = _generate(url)
        status = result["status"]
        if status == "succeeded":
            return (
                result["content"]["video_url"],
                result["content"].get("last_frame_url", ""),
            )
        elif status == "failed":
            raise Exception(f"Failed to generate video: {result}")
        time.sleep(interval)
