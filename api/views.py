import io
import requests
import traceback
import threading
import time
import uuid


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import render
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse, FileResponse

from .services.openai_service import generate_questions
from .services.deepseek_service import ask_deepseek
from .services.openai_service import analyze_tnved
from .services.pdf_service import generate_pdf
from .services.gigachat_service import ask_gigachat
from .services.yandex_service import ask_yandex_gpt
from .services.image_pipeline import process_image
from .services.utils import normalize_confidence
from .services.customs_service import get_customs_info
from .services.vision_service import analyze_image_and_generate_questions
from .services.final_decision_service import make_final_decision
from .services.parser.product_parser import parse_product_page

print(parse_product_page.__module__)

from concurrent.futures import ThreadPoolExecutor

from .models import ProductRequest, ModelResult, FinalResult


def index(request):
    return render(request, 'api/index.html')


@api_view(['POST'])
def generate_questions_view(request):

    description = request.data.get(
        'description',
        ''
    ).strip()

    image_files = request.FILES.getlist('image')

    image_url = request.data.get(
        'image_url',
        ''
    ).strip()

    print(
        "========== GENERATE QUESTIONS =========="
    )

    print(
        "DESCRIPTION:",
        description
    )

    print(
        "NUMBER OF IMAGE FILES:",
        len(image_files)
    )

    for index, image_file in enumerate(
        image_files,
        start=1
    ):
        print(
            f"IMAGE FILE {index}:",
            image_file.name,
            image_file.size,
            image_file.content_type
        )

    print(
        "IMAGE URL:",
        image_url
    )

    if (
        not description
        and not image_files
        and not image_url
    ):
        return Response(
            {
                "error":
                    "Необходимо указать описание или загрузить изображение"
            },
            status=400
        )

    try:

        product_request = ProductRequest.objects.create(
            description=description,
            image_url=image_url if image_url else None
        )

        images_bytes = []

        if image_files:

            for index, image_file in enumerate(
                image_files,
                start=1
            ):

                try:

                    image_file.seek(0)

                    image_bytes = image_file.read()

                    image_file.seek(0)

                    if not image_bytes:

                        print(
                            f"IMAGE {index} IS EMPTY:",
                            image_file.name
                        )

                        continue

                    images_bytes.append(
                        image_bytes
                    )

                    print(
                        f"IMAGE {index} READ SUCCESSFULLY:",
                        image_file.name,
                        "SIZE:",
                        len(image_bytes)
                    )

                    if (
                        index == 1
                        and not product_request.image
                    ):

                        image_file.seek(0)

                        product_request.image = image_file

                        product_request.save(
                            update_fields=['image']
                        )

                except Exception as file_error:

                    print(
                        f"ERROR READING IMAGE {index}:",
                        file_error
                    )

        if (
            not images_bytes
            and image_url
        ):

            processed_image = process_image(
                image_url=image_url
            )

            if not processed_image:

                product_request.delete()

                return Response(
                    {
                        "error":
                            "Не удалось загрузить изображение по ссылке"
                    },
                    status=400
                )

            processed_image.seek(0)

            image_bytes = processed_image.read()

            processed_image.seek(0)

            if image_bytes:

                images_bytes.append(
                    image_bytes
                )

            processed_image.seek(0)

            product_request.image.save(
                processed_image.name,
                processed_image,
                save=True
            )

            print(
                "IMAGE FROM URL READ:",
                len(image_bytes) if image_bytes else 0
            )

        print(
            "TOTAL IMAGES FOR VISION:",
            len(images_bytes)
        )

        for index, image_bytes in enumerate(
            images_bytes,
            start=1
        ):

            print(
                f"VISION IMAGE {index} SIZE:",
                len(image_bytes)
            )

        if images_bytes:

            result = analyze_image_and_generate_questions(
                image_bytes=images_bytes[0],
                description=description
            )

        else:

            result = {
                "questions":
                    generate_questions(
                        description
                    )
            }

        result["request_id"] = product_request.id

        result["preview"] = (
            product_request.image.url
            if product_request.image
            else None
        )

        print(
            "GENERATE QUESTIONS FINISHED:",
            product_request.id
        )

        return Response(
            result
        )

    except Exception as e:

        traceback.print_exc()

        return Response(
            {
                "error":
                    str(e)
            },
            status=500
        )


@api_view(["POST"])
def parse_product_view(request):

    request_id = str(
        uuid.uuid4()
    )[:8]

    print(
        "\n" + "=" * 80
    )

    print(
        "PARSE PRODUCT REQUEST"
    )

    print(
        "REQUEST ID:",
        request_id
    )

    print(
        "TIME:",
        time.time()
    )

    print(
        "METHOD:",
        request.method
    )

    print(
        "URL:",
        request.data.get("url")
    )

    print(
        "REFERER:",
        request.META.get("HTTP_REFERER")
    )

    print(
        "USER AGENT:",
        request.META.get("HTTP_USER_AGENT")
    )

    print(
        "=" * 80
    )

    url = request.data.get(
        "url",
        ""
    ).strip()

    if not url:

        return Response(
            {
                "error":
                    "URL не указан"
            },
            status=400
        )

    try:

        result = parse_product_page(
            url
        )

        print(
            f"[{request_id}] END parse_product_page"
        )

        return Response(
            result
        )

    except Exception as e:

        traceback.print_exc()

        return Response(
            {
                "error":
                    str(e)
            },
            status=500
        )


@api_view(['POST'])
def analyze_product_view(request):

    print(
        "========== ANALYZE START ==========",
        "THREAD:",
        threading.current_thread().name,
        "TIME:",
        time.time()
    )

    try:

        data = request.data

        print(
            "REQUEST DATA:"
        )

        print(
            data
        )

        vision_data = (
            data.get("vision_data")
            or {}
        )

        preview = vision_data.get(
            "preview"
        )

        print(
            "SAVED IMAGE PREVIEW:",
            preview
        )

        product_request = ProductRequest.objects.create(
            description=data.get(
                "description",
                ""
            ),
            image=None,
            image_url=preview or ""
        )

        with ThreadPoolExecutor(
            max_workers=4
        ) as executor:

            future_openai = executor.submit(
                analyze_tnved,
                data
            )

            future_deepseek = executor.submit(
                ask_deepseek,
                data
            )

            future_gigachat = executor.submit(
                ask_gigachat,
                data
            )

            future_yandex = executor.submit(
                ask_yandex_gpt,
                data
            )

            try:

                openai_result = (
                    future_openai.result()
                )

                openai_result["confidence"] = (
                    normalize_confidence(
                        openai_result.get(
                            "confidence"
                        )
                    )
                )

            except Exception as e:

                openai_result = {
                    "tnved_code": "-",
                    "title": "Ошибка",
                    "confidence": 0,
                    "reasoning": str(e)
                }

            try:

                deepseek_result = (
                    future_deepseek.result()
                )

                deepseek_result["confidence"] = (
                    normalize_confidence(
                        deepseek_result.get(
                            "confidence"
                        )
                    )
                )

            except Exception as e:

                deepseek_result = {
                    "tnved_code": "-",
                    "title": "Ошибка",
                    "confidence": 0,
                    "reasoning": str(e)
                }

            try:

                gigachat_result = (
                    future_gigachat.result()
                )

                gigachat_result["confidence"] = (
                    normalize_confidence(
                        gigachat_result.get(
                            "confidence"
                        )
                    )
                )

            except Exception as e:

                gigachat_result = {
                    "tnved_code": "-",
                    "title": "Ошибка",
                    "confidence": 0,
                    "reasoning": str(e)
                }

            try:

                yandex_result = (
                    future_yandex.result()
                )

                yandex_result["confidence"] = (
                    normalize_confidence(
                        yandex_result.get(
                            "confidence"
                        )
                    )
                )

            except Exception as e:

                yandex_result = {
                    "tnved_code": "-",
                    "title": "Ошибка",
                    "confidence": 0,
                    "reasoning": str(e)
                }

        for model_name, result in [
            ("openai", openai_result),
            ("deepseek", deepseek_result),
            ("gigachat", gigachat_result),
            ("yandex", yandex_result),
        ]:

            ModelResult.objects.create(
                request=product_request,
                model_name=model_name,
                tnved_code=result.get(
                    "tnved_code",
                    ""
                ),
                title=result.get(
                    "title",
                    ""
                ),
                confidence=result.get(
                    "confidence",
                    0
                ),
                reasoning=result.get(
                    "reasoning",
                    ""
                )
            )

        final_result = make_final_decision(
            openai_result,
            deepseek_result,
            gigachat_result,
            yandex_result,
            description=data.get(
                "description",
                ""
            ),
            answers=data.get(
                "answers",
                []
            ),
            vision_data=data.get(
                "vision_data"
            ) or {}
        )

        final_result["confidence"] = (
            normalize_confidence(
                final_result.get(
                    "confidence"
                )
            )
        )

        FinalResult.objects.create(
            request=product_request,
            recommended_code=final_result.get(
                "recommended_code"
            ),
            confidence=final_result.get(
                "confidence",
                0
            ),
            supported_by=final_result.get(
                "supported_by",
                []
            ),
            reasoning=final_result.get(
                "reasoning",
                ""
            )
        )

        return Response({

            "openai":
                openai_result,

            "deepseek":
                deepseek_result,

            "gigachat":
                gigachat_result,

            "yandex":
                yandex_result,

            "final":
                final_result

        })

    except Exception as e:

        print(
            "\n========== ERROR =========="
        )

        traceback.print_exc()

        print(
            "===========================\n"
        )

        print(
            "========== ANALYZE END ==========",
            "THREAD:",
            threading.current_thread().name,
            "TIME:",
            time.time()
        )

        return Response(
            {
                "error":
                    str(e)
            },
            status=500
        )


@api_view(['POST'])
def download_pdf_view(request):

    results = request.data

    pdf_path = generate_pdf(
        results
    )

    return FileResponse(
        open(
            pdf_path,
            'rb'
        ),
        as_attachment=True,
        filename='tnved_result.pdf'
    )


@api_view(['GET'])
def history_view(request):

    requests = (
        ProductRequest.objects.all()
        .select_related('final')
        .prefetch_related('results')
        .order_by('-created_at')
    )

    data = []

    for req in requests:

        data.append({

            "id":
                req.id,

            "description":
                req.description,

            "image":
                req.image.url
                if req.image
                else None,

            "image_url":
                req.image_url,

            "created_at":
                req.created_at,

            "results": [

                {
                    "model":
                        r.model_name,

                    "tnved_code":
                        r.tnved_code,

                    "title":
                        r.title,

                    "confidence":
                        r.confidence,

                    "reasoning":
                        r.reasoning,
                }

                for r in req.results.all()

            ],

            "final": (

                {
                    "recommended_code":
                        req.final.recommended_code,

                    "confidence":
                        req.final.confidence,

                    "supported_by":
                        req.final.supported_by,

                    "reasoning":
                        req.final.reasoning,

                    "vat":
                        req.final.vat,

                    "duty":
                        req.final.duty,
                }

                if hasattr(
                    req,
                    "final"
                )
                and req.final

                else None
            )
        })

    return Response(
        data
    )


def history_page(request):

    return render(
        request,
        'api/history.html'
    )


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