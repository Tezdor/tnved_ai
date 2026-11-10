import threading
import time
import traceback
import uuid

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from concurrent.futures import ThreadPoolExecutor

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ProductRequest, ModelResult, FinalResult

from .services.openai_service import generate_questions, analyze_tnved
from .services.deepseek_service import ask_deepseek
from .services.gigachat_service import ask_gigachat
from .services.yandex_service import ask_yandex_gpt
from .services.image_pipeline import process_image
from .services.utils import normalize_confidence
from .services.vision_service import analyze_image_and_generate_questions
from .services.final_decision_service import make_final_decision
from .services.rate_limit import check_rate_limit, get_client_ip

@api_view(['POST'])
def generate_questions_view(request):

    GUEST_FREE_LIMIT = 2

    if not request.user.is_authenticated:
        guest_attempts = request.session.get(
            "guest_analysis_count",
            0
        )

        if guest_attempts >= GUEST_FREE_LIMIT:
            return Response(
                {
                    "error": "Лимит бесплатных анализов исчерпан.",
                    "code": "GUEST_LIMIT_REACHED",
                    "requires_auth": True,
                    "login_url": "/api/login/",
                    "register_url": "/api/register/"
                },
                status=403
            )
        
    if request.user.is_authenticated:
        rate_identity = f"user:{request.user.pk}"
    else:
        rate_identity = f"ip:{get_client_ip(request)}"

    retry_after = check_rate_limit(
        scope="generate_questions",
        identity=rate_identity,
        limit=10,
        period_seconds=60
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

    GUEST_FREE_LIMIT = 2

    if not request.user.is_authenticated:

        guest_attempts = request.session.get(
            "guest_analysis_count",
            0
        )

        if guest_attempts >= GUEST_FREE_LIMIT:
            return Response(
                {
                    "error": "Лимит бесплатных анализов исчерпан.",
                    "code": "GUEST_LIMIT_REACHED",
                    "requires_auth": True,
                    "login_url": "/api/login/",
                    "register_url": "/api/register/"
                },
                status=403
            )

    print(
        "========== ANALYZE START ==========",
        "THREAD:",
        threading.current_thread().name,
        "TIME:",
        time.time()
    )

    if request.user.is_authenticated:
        rate_identity = f"user:{request.user.pk}"
    else:
        rate_identity = f"ip:{get_client_ip(request)}"

    retry_after = check_rate_limit(
        scope="analyze_product",
        identity=rate_identity,
        limit=5,
        period_seconds=60
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

        if request.user.is_authenticated:
            available_requests = ProductRequest.objects.filter(
                user=request.user
            )
        else:
            guest_request_ids = request.session.get("guest_request_ids", [])

            available_requests = ProductRequest.objects.filter(
                user__isnull=True,
                id__in=guest_request_ids
            )

        with transaction.atomic():
            product_request = (
                available_requests
                .select_for_update()
                .filter(id=request_id)
                .first()
            )

            if product_request is None:
                return Response(
                    {"error": "Запрос не найден или недоступен."},
                    status=404
                )

            if FinalResult.objects.filter(
                request=product_request
            ).exists():
                return Response(
                    {
                        "error":
                            "Этот запрос уже проанализирован. Создайте новый запрос."
                    },
                    status=409
                )

            now = timezone.now()

            if product_request.analysis_in_progress:
                started_at = product_request.analysis_started_at

                if started_at is None:
                    return Response(
                        {
                            "error":
                                "У запроса старая блокировка без времени начала. "
                                "Необходимо восстановление администратором."
                        },
                        status=409
                    )

                if started_at > now - timedelta(minutes=15):
                    return Response(
                        {"error": "Анализ этого запроса уже выполняется."},
                        status=409
                    )

            product_request.analysis_in_progress = True
            product_request.analysis_started_at = now
            product_request.analysis_run_id = run_id
            product_request.description = data.get("description", "")

            product_request.save(
                update_fields=[
                    "analysis_in_progress",
                    "analysis_started_at",
                    "analysis_run_id",
                    "description",
                ]
            )

        claimed_request_id = product_request.id

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

        with transaction.atomic():
            saved_request = (
                ProductRequest.objects
                .select_for_update()
                .get(id=claimed_request_id)
            )

            if (
                not saved_request.analysis_in_progress
                or saved_request.analysis_run_id != run_id
            ):
                return Response(
                    {
                        "error":
                            "Эта попытка анализа больше не активна."
                    },
                    status=409
                )

            if FinalResult.objects.filter(
                request=saved_request
            ).exists():
                return Response(
                    {"error": "Результат этого запроса уже сохранён."},
                    status=409
                )

            # Убираем частичные ответы от прежних неудачных попыток.
            ModelResult.objects.filter(
                request=saved_request
            ).delete()

            for model_name, result in [
                ("openai", openai_result),
                ("deepseek", deepseek_result),
                ("gigachat", gigachat_result),
                ("yandex", yandex_result),
            ]:
                ModelResult.objects.create(
                    request=saved_request,
                    model_name=model_name,
                    tnved_code=result.get("tnved_code", ""),
                    title=result.get("title", ""),
                    confidence=result.get("confidence", 0),
                    reasoning=result.get("reasoning", "")
                )

            FinalResult.objects.create(
                request=saved_request,
                recommended_code=final_result.get("recommended_code"),
                confidence=final_result.get("confidence", 0),
                supported_by=final_result.get("supported_by", []),
                reasoning=final_result.get("reasoning", "")
            )

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
            ProductRequest.objects.filter(
                id=claimed_request_id,
                analysis_run_id=run_id
            ).update(
                analysis_in_progress=False,
                analysis_started_at=None,
                analysis_run_id=None
            )