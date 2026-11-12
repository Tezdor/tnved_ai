import threading
import time
import traceback
import uuid

from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import ProductRequest

from ..services.openai_service import generate_questions
from ..services.image_pipeline import process_image
from ..services.vision_service import analyze_image_and_generate_questions
from ..core.access import (
    analysis_retry_after,
    available_product_requests,
    guest_limit_reached,
)
from ..services.analysis.pipeline import (
    AnalysisConflict,
    AnalysisNotFound,
    claim_analysis,
    release_analysis,
    run_and_save_analysis,
)

@api_view(['POST'])
def generate_questions_view(request):

    if guest_limit_reached(request):
        return Response(
            {
                "error": "Лимит бесплатных анализов исчерпан.",
                "code": "GUEST_LIMIT_REACHED",
                "requires_auth": True,
                "login_url": "/api/login/",
                "register_url": "/api/register/",
            },
            status=403,
        )

    retry_after = analysis_retry_after(
        request, scope="generate_questions", limit=10
    )

    if retry_after:
        return Response(
            {
                "error": (
                    "Слишком много запросов вопросов. "
                    f"Повторите через {retry_after} сек."
                ),
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": retry_after,
            },
            status=429,
            headers={
                "Retry-After": str(retry_after),
                "Cache-Control": "no-store",
            }
        )
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
            user=request.user if request.user.is_authenticated else None,
            description=description,
            image_url=image_url if image_url else None
        )

        if not request.user.is_authenticated:
            guest_request_ids = request.session.get("guest_request_ids", [])

            guest_request_ids.append(product_request.id)

            request.session["guest_request_ids"] = guest_request_ids

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

        image_warning = None

        if not images_bytes and image_url:
            processed_image = process_image(image_url=image_url)

            if processed_image:
                image_bytes = processed_image.read()
            else:
                image_bytes = b""

            if image_bytes:
                images_bytes.append(image_bytes)
                processed_image.seek(0)
                product_request.image.save(
                    processed_image.name,
                    processed_image,
                    save=True
                )
            elif description:
                image_warning = (
                    "Не удалось загрузить фото по ссылке. "
                    "Вопросы сформированы только по описанию."
                )
            else:
                product_request.delete()
                return Response(
                    {
                        "error": (
                            "Не удалось загрузить фото по ссылке. "
                            "Загрузите фото файлом или добавьте описание товара."
                        )
                    },
                    status=400
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

        if image_warning:
            result["image_warning"] = image_warning

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

@api_view(['POST'])
def analyze_product_view(request):

    if guest_limit_reached(request):
        request_id = request.data.get("request_id")
        guest_request_ids = request.session.get("guest_request_ids", [])

        if type(request_id) is int and request_id in guest_request_ids:
            request.session["pending_guest_request_id"] = request_id
        return Response(
            {
                "error": "Лимит бесплатных анализов исчерпан.",
                "code": "GUEST_LIMIT_REACHED",
                "requires_auth": True,
                "login_url": "/api/login/",
                "register_url": "/api/register/",
            },
            status=403,
        )

    print(
        "========== ANALYZE START ==========",
        "THREAD:",
        threading.current_thread().name,
        "TIME:",
        time.time()
    )

    retry_after = analysis_retry_after(
        request, scope="analyze_product", limit=5
    )

    if retry_after:
        return Response(
            {
                "error": (
                    "Слишком много запросов анализа. "
                    f"Повторите через {retry_after} сек."
                ),
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": retry_after,
            },
            status=429,
            headers={
                "Retry-After": str(retry_after),
                "Cache-Control": "no-store",
            }
        )

    claimed_request_id = None
    run_id = uuid.uuid4()

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

        request_id = data.get("request_id")

        if (
            not isinstance(request_id, int)
            or isinstance(request_id, bool)
            or request_id <= 0
        ):
            return Response(
                {"error": "Необходимо передать корректный request_id."},
                status=400
            )

        available_requests = available_product_requests(request)

        try:
            claimed_request_id = claim_analysis(
                available_requests, request_id, run_id, data
            )
            (
                openai_result,
                deepseek_result,
                gigachat_result,
                yandex_result,
                final_result,
            ) = run_and_save_analysis(data, claimed_request_id, run_id)
        except AnalysisNotFound as error:
            return Response({"error": str(error)}, status=404)
        except AnalysisConflict as error:
            return Response({"error": str(error)}, status=409)

        if not request.user.is_authenticated:

            model_results = [
                openai_result,
                deepseek_result,
                gigachat_result,
                yandex_result,
            ]

            has_valid_result = any(
                str(result.get("tnved_code") or "").strip()
                not in ("", "-")
                for result in model_results
            )

            if has_valid_result:
                request.session["guest_analysis_count"] = (
                    request.session.get(
                        "guest_analysis_count",
                        0
                    ) + 1
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

    finally:
        if claimed_request_id is not None:
            release_analysis(claimed_request_id, run_id)