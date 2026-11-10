from concurrent.futures import ThreadPoolExecutor

from datetime import timedelta

from ...models import FinalResult, ModelResult, ProductRequest
from ..final_decision_service import make_final_decision
from ..deepseek_service import ask_deepseek
from ..gigachat_service import ask_gigachat
from ..openai_service import analyze_tnved
from ..utils import normalize_confidence
from ..yandex_service import ask_yandex_gpt

from django.db import transaction
from django.utils import timezone


def safe_call(future):
    try:
        result = future.result()
        result["confidence"] = normalize_confidence(
            result.get("confidence")
        )
        return result
    except Exception as error:
        return {
            "tnved_code": "-",
            "title": "Ошибка",
            "confidence": 0,
            "reasoning": str(error),
        }


def run_models(data):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = (
            executor.submit(analyze_tnved, data),
            executor.submit(ask_deepseek, data),
            executor.submit(ask_gigachat, data),
            executor.submit(ask_yandex_gpt, data),
        )
        return tuple(safe_call(future) for future in futures)

class AnalysisConflict(Exception):
    pass

class AnalysisNotFound(Exception):
    pass

def claim_analysis(available_requests, request_id, run_id, data):
    with transaction.atomic():
        product_request = (
            available_requests.select_for_update()
            .filter(id=request_id)
            .first()
        )

        if product_request is None:
            raise AnalysisNotFound("Запрос не найден или недоступен.")

        if FinalResult.objects.filter(request=product_request).exists():
            raise AnalysisConflict(
                "Этот запрос уже проанализирован. Создайте новый запрос."
            )

        now = timezone.now()

        if product_request.analysis_in_progress:
            started_at = product_request.analysis_started_at

            if started_at is None:
                raise AnalysisConflict(
                    "У запроса старая блокировка без времени начала. "
                    "Необходимо восстановление администратором."
                )

            if started_at > now - timedelta(minutes=15):
                raise AnalysisConflict(
                    "Анализ этого запроса уже выполняется."
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

    return product_request.id


def release_analysis(request_id, run_id):
    ProductRequest.objects.filter(
        id=request_id,
        analysis_run_id=run_id
    ).update(
        analysis_in_progress=False,
        analysis_started_at=None,
        analysis_run_id=None
    )



def run_and_save_analysis(data, claimed_request_id, run_id):
    (   
        openai_result,
        deepseek_result,
        gigachat_result,
        yandex_result,
    ) = run_models(data)

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
            raise AnalysisConflict("Эта попытка анализа больше не активна.")

        if FinalResult.objects.filter(
            request=saved_request
        ).exists():
            raise AnalysisConflict("Результат этого запроса уже сохранён.")

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

    return (
        openai_result,
        deepseek_result,
        gigachat_result,
        yandex_result,
        final_result,
    )