# doubao/views.py
import time

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .models import ImageGeneration, VideoGeneration
from .utils import (
    DOUBAO_MODELS,
    encode_image_to_data_url,
    generate_image,
    poll_video_result,
    submit_video_task,
)


def get_setting(name, default):
    """Get a Django setting with fallback to default value."""
    return getattr(settings, name, default)


@require_http_methods(["GET", "POST"])
def generate_image_view(request):
    if request.method == "GET":
        # 直接传递 sizes 列表给模板
        size_choices = DOUBAO_MODELS["image"]["sizes"]
        return render(request, "doubao/generate_image.html", {"sizes": size_choices})

    # POST
    prompt = request.POST.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "Prompt is required"}, status=400)

    uploaded_files = request.FILES.getlist("reference_images")
    if not uploaded_files:
        return JsonResponse(
            {"error": "At least one reference image is required"}, status=400
        )

    image_data_urls = []
    for f in uploaded_files:
        if f.size > 30 * 1024 * 1024:
            return JsonResponse(
                {"error": f"Image {f.name} exceeds 30MB limit"}, status=400
            )
        data_url = encode_image_to_data_url(f)
        image_data_urls.append(data_url)

    image_gen = ImageGeneration.objects.create(
        reference_images=[],
        prompt=prompt,
        status="pending",
    )

    try:
        final_url = generate_image(image_data_urls, prompt)
        image_gen.result_url = final_url
        image_gen.status = "success"
        image_gen.save()
    except Exception as e:
        image_gen.status = "failed"
        image_gen.save()
        return JsonResponse({"error": f"API error: {str(e)}"}, status=500)

    return JsonResponse(
        {"success": True, "image_url": final_url, "image_gen_id": image_gen.id}
    )


@require_http_methods(["GET", "POST"])
def generate_video_view(request):
    if request.method == "GET":
        context = {
            "ratios": DOUBAO_MODELS["video"]["ratios"],
            "resolutions": DOUBAO_MODELS["video"]["resolutions"],
            "max_duration": DOUBAO_MODELS["video"]["max_duration"],
        }
        return render(request, "doubao/generate_video.html", context)

    # POST
    prompt = request.POST.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "Prompt is required"}, status=400)

    duration = int(request.POST.get("duration", DOUBAO_MODELS["video"]["max_duration"]))
    resolution = request.POST.get(
        "resolution", DOUBAO_MODELS["video"]["resolutions"][0]
    )
    ratio = request.POST.get("ratio", DOUBAO_MODELS["video"]["ratios"][0])

    uploaded_file = request.FILES.get("image")
    image_url = request.POST.get("image_url", "").strip()

    image_input = None
    image_generation = None

    if uploaded_file:
        if uploaded_file.size > 30 * 1024 * 1024:
            return JsonResponse({"error": "Image size exceeds 30MB"}, status=400)
        image_input = encode_image_to_data_url(uploaded_file)
    elif image_url:
        image_input = image_url
        try:
            image_generation = ImageGeneration.objects.filter(
                result_url=image_url
            ).first()
        except Exception:
            pass
    else:
        return JsonResponse({"error": "No image provided"}, status=400)

    video_gen = VideoGeneration.objects.create(
        image_generation=image_generation,
        prompt=prompt,
        task_id="",
        status="pending",
    )

    try:
        task_id = submit_video_task(
            image_input=image_input,
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            ratio=ratio,
        )
        video_gen.task_id = task_id
        video_gen.status = "processing"
        video_gen.save()
    except Exception as e:
        video_gen.status = "failed"
        video_gen.save()
        return JsonResponse(
            {"error": f"Failed to submit video task: {str(e)}"}, status=500
        )

    try:
        video_url, last_frame_url = poll_video_result(task_id, interval=5, timeout=180)
        video_gen.result_url = video_url
        video_gen.status = "success"
        video_gen.save()
    except Exception as e:
        video_gen.status = "failed"
        video_gen.save()
        return JsonResponse({"error": f"Video generation failed: {str(e)}"}, status=500)

    return JsonResponse(
        {
            "success": True,
            "video_url": video_url,
            "last_frame_url": last_frame_url,
            "video_gen_id": video_gen.id,
        }
    )


def get_image_url(request, image_id):
    try:
        img_gen = ImageGeneration.objects.get(id=image_id)
        return JsonResponse({"success": True, "image_url": img_gen.result_url})
    except ImageGeneration.DoesNotExist:
        return JsonResponse({"success": False, "error": "Image not found"}, status=404)
