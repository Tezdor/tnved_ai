import requests
import traceback

from django.http import HttpResponse, JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ProductRequest
from .services.image_pipeline import process_image

@api_view(["GET"])
def image_preview_view(request):

    url = request.GET.get(
        "url"
    )

    if not url:

        return Response(
            {
                "error":
                    "URL не указан"
            },
            status=400
        )

    try:

        image = process_image(
            image_url=url
        )

        if image is None:

            return Response(
                {
                    "error":
                        "Не удалось загрузить изображение"
                },
                status=400
            )

        image.seek(0)

        content = image.read()

        if image.name.endswith(
            ".png"
        ):

            content_type = "image/png"

        elif image.name.endswith(
            ".webp"
        ):

            content_type = "image/webp"

        elif image.name.endswith(
            ".gif"
        ):

            content_type = "image/gif"

        else:

            content_type = "image/jpeg"

        return HttpResponse(
            content,
            content_type=content_type
        )

    except Exception as e:

        return Response(
            {
                "error":
                    str(e)
            },
            status=500
        )


@api_view(["POST"])
def process_image_view(request):

    image_url = request.data.get(
        "image_url",
        ""
    ).strip()

    if not image_url:

        return Response(
            {
                "error":
                    "URL пустой"
            },
            status=400
        )

    image = process_image(
        image_url=image_url
    )

    if not image:

        return Response(
            {
                "error":
                    "Не удалось обработать изображение"
            },
            status=400
        )

    product = ProductRequest.objects.create(
        user=request.user if request.user.is_authenticated else None,
        image=image
    )   

    return Response({
        "image":
            product.image.url
    })


def wb_image_proxy(request):

    image_url = request.GET.get(
        "url"
    )

    if not image_url:

        return JsonResponse(
            {
                "error":
                    "URL изображения не указан"
            },
            status=400
        )

    print(
        "=" * 60
    )

    print(
        "WB PROXY URL:"
    )

    print(
        image_url
    )

    print(
        "=" * 60
    )

    try:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "image/avif,image/webp,image/apng,"
                "image/svg+xml,image/*,*/*;q=0.8"
            ),
            "Accept-Language":
                "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer":
                "https://www.wildberries.ru/",
        }

        response = requests.get(
            image_url,
            headers=headers,
            timeout=30,
            verify=False,
            allow_redirects=True
        )

        print(
            "WB PROXY STATUS:",
            response.status_code
        )

        print(
            "WB PROXY FINAL URL:",
            response.url
        )

        print(
            "WB PROXY CONTENT TYPE:",
            response.headers.get(
                "Content-Type"
            )
        )

        print(
            "WB PROXY SIZE:",
            len(
                response.content
            )
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "image/webp"
        )

        return HttpResponse(
            response.content,
            content_type=content_type
        )

    except requests.exceptions.SSLError as e:

        traceback.print_exc()

        return JsonResponse(
            {
                "error":
                    "SSL ошибка при загрузке изображения WB",

                "details":
                    str(e),

                "url":
                    image_url
            },
            status=502
        )

    except requests.exceptions.RequestException as e:


        traceback.print_exc()

        return JsonResponse(
            {
                "error":
                    "Ошибка загрузки изображения WB",

                "details":
                    str(e),

                "url":
                    image_url
            },
            status=502
        )

    except Exception as e:

        traceback.print_exc()

        return JsonResponse(
            {
                "error":
                    "Не удалось загрузить изображение",

                "details":
                    str(e),

                "url":
                    image_url
            },
            status=502
        )