import json
import os
import re

from .llm.json_utils import clean_json
from .llm.client import client

from django.conf import settings
from pathlib import Path
# ============================================================
# НОРМАЛИЗАЦИЯ КОДА
# ============================================================

def normalize_code(code):
    """
    Убирает пробелы, дефисы и другие символы из кода.

    Например:

        6110
        6110 20 910 0
        6110209100

    превращаются соответственно в:

        6110
        6110209100
        6110209100

    Важно:
    это только техническая нормализация для сравнения.
    Мы НЕ сокращаем и НЕ дополняем коды.
    """

    if not isinstance(code, str):
        return ""

    return re.sub(r"\D", "", code)


# ============================================================
# ИЗВЛЕЧЕНИЕ КОДОВ ТОЛЬКО ИЗ tnved_code
# ============================================================

def extract_tnved_codes(value):
    """
    Извлекает ТОЛЬКО значения поля tnved_code.

    Это принципиально важно.

    НЕЛЬЗЯ искать любые последовательности цифр в reasoning,
    потому что там могут быть:

        2018
        69
        6104
        20
        10
        и т.д.

    Они НЕ являются кандидатами ТН ВЭД.

    Мы принимаем код кандидатом только если модель сама
    записала его в поле:

        "tnved_code": "..."

    Функция умеет работать как с обычным JSON,
    так и со строкой, внутри которой модель вернула
    JSON в ```json ... ``` или ``` ... ```.
    """

    found = []

    def add_code(code):
        if not isinstance(code, str):
            return

        code = code.strip()

        if not code:
            return

        normalized = normalize_code(code)

        # Разрешаем только разумную длину кода,
        # но не придумываем код.
        if not normalized:
            return

        if len(normalized) < 4:
            return

        if len(normalized) > 10:
            return

        if normalized not in found:
            found.append(normalized)

    def process(item):

        if item is None:
            return

        # ----------------------------------------------------
        # JSON object
        # ----------------------------------------------------

        if isinstance(item, dict):

            for key, value2 in item.items():

                if str(key).lower() == "tnved_code":

                    if isinstance(value2, str):
                        add_code(value2)

                    elif isinstance(value2, (int, float)):
                        add_code(str(value2))

                # Продолжаем искать вложенные JSON-объекты.
                process(value2)

            return

        # ----------------------------------------------------
        # JSON list
        # ----------------------------------------------------

        if isinstance(item, list):

            for sub_item in item:
                process(sub_item)

            return

        # ----------------------------------------------------
        # Строка
        # ----------------------------------------------------

        if isinstance(item, str):

            text = item.strip()

            if not text:
                return

            # ------------------------------------------------
            # Сначала пытаемся разобрать строку как JSON
            # ------------------------------------------------

            try:
                parsed = json.loads(text)
                process(parsed)
            except Exception:
                pass

            # ------------------------------------------------
            # Затем ищем ТОЛЬКО:
            #
            # "tnved_code": "..."
            #
            # ------------------------------------------------

            patterns = [
                r'"tnved_code"\s*:\s*"([^"]+)"',
                r"'tnved_code'\s*:\s*'([^']+)'",
            ]

            for pattern in patterns:

                matches = re.findall(
                    pattern,
                    text,
                    flags=re.IGNORECASE
                )

                for match in matches:
                    add_code(match)

            return

    process(value)

    return found


# ============================================================
# КОДЫ КАЖДОЙ МОДЕЛИ
# ============================================================

def get_model_codes(model_result):
    """
    Возвращает только реальные tnved_code конкретной модели.
    """

    return extract_tnved_codes(model_result)


# ============================================================
# ВСЕ КАНДИДАТЫ
# ============================================================

def collect_all_candidate_codes(
    openai_result,
    deepseek_result,
    gigachat_result,
    yandex_result
):
    """
    Формирует список кодов по каждой модели.

    Здесь НЕТ определения правильного кода.

    Мы только фиксируем:
    какие tnved_code реально предложили модели.
    """

    models = {
        "OPENAI": openai_result,
        "DEEPSEEK": deepseek_result,
        "GIGACHAT": gigachat_result,
        "YANDEXGPT": yandex_result,
    }

    result = {}

    for model_name, model_result in models.items():

        result[model_name] = get_model_codes(
            model_result
        )

    return result


# ============================================================
# ВСЕ УНИКАЛЬНЫЕ КОДЫ
# ============================================================

def get_unique_candidate_codes(candidate_codes):
    """
    Возвращает плоский список всех уникальных кандидатов.

    Например:

    {
        OPENAI: ["6110"],
        GIGACHAT: ["6104900000"],
        YANDEXGPT: ["6110209100", "6110309100"]
    }

    превращается в:

    [
        "6110",
        "6104900000",
        "6110209100",
        "6110309100"
    ]
    """

    result = []

    for model_codes in candidate_codes.values():

        for code in model_codes:

            normalized = normalize_code(code)

            if not normalized:
                continue

            if normalized not in result:
                result.append(normalized)

    return result


# ============================================================
# supported_by
# ============================================================

def find_models_for_code(
    candidate_codes,
    target_code
):
    """
    Возвращает модели, которые предложили ТОЧНО такой же код.

    Например:

    OPENAI -> 6110
    YANDEX -> 6110209100

    Для 6110:

    ["OPENAI"]

    Для 6110209100:

    ["YANDEXGPT"]

    6110 НЕ считается совпадением с 6110209100.
    """

    target = normalize_code(target_code)

    if not target:
        return []

    supported_by = []

    for model_name, codes in candidate_codes.items():

        for code in codes:

            if normalize_code(code) == target:

                supported_by.append(model_name)
                break

    return supported_by


# ============================================================
# БЕЗОПАСНЫЙ FALLBACK
# ============================================================

def make_uncertain_result(reasoning):
    """
    Унифицированный результат для ситуации,
    когда классификацию нельзя надёжно завершить.
    """

    return {
        "recommended_code": "Уточнить",
        "vat": "Уточнить",
        "duty": "Уточнить",
        "confidence": 0,
        "supported_by": [],
        "reasoning": reasoning,
        "customs_reasoning": (
            "Ставки не определены, поскольку итоговый код "
            "ТН ВЭД не установлен однозначно."
        )
    }


# ============================================================
# ПРОВЕРКА ФИНАЛЬНОГО JSON
# ============================================================

def validate_final_result(
    result,
    candidate_codes
):
    """
    Программная проверка ответа финальной модели.

    Эта функция НЕ определяет правильный ТН ВЭД.

    Она только не позволяет финальной модели нарушить
    технические правила системы.
    """

    if not isinstance(result, dict):

        raise ValueError(
            "Финальный ответ модели не является JSON-объектом"
        )

    required_fields = [
        "recommended_code",
        "vat",
        "duty",
        "confidence",
        "supported_by",
        "reasoning",
        "customs_reasoning",
    ]

    # --------------------------------------------------------
    # Обязательные поля
    # --------------------------------------------------------

    for field in required_fields:

        if field not in result:

            raise ValueError(
                f"В финальном ответе отсутствует поле: {field}"
            )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    try:

        confidence = float(
            result.get("confidence", 0)
        )

    except (TypeError, ValueError):

        confidence = 0

    confidence = max(
        0,
        min(100, confidence)
    )

    result["confidence"] = int(
        round(confidence)
    )

    # --------------------------------------------------------
    # supported_by
    # --------------------------------------------------------

    supported_by = result.get(
        "supported_by",
        []
    )

    if not isinstance(
        supported_by,
        list
    ):
        supported_by = []

    allowed_models = {
        "OPENAI",
        "DEEPSEEK",
        "GIGACHAT",
        "YANDEXGPT",
    }

    supported_by = [
        str(model).upper().strip()
        for model in supported_by
        if str(model).upper().strip()
        in allowed_models
    ]

    # --------------------------------------------------------
    # recommended_code
    # --------------------------------------------------------

    recommended_code = result.get(
        "recommended_code",
        ""
    )

    if not isinstance(
        recommended_code,
        str
    ):
        recommended_code = str(
            recommended_code
        )

    recommended_code = recommended_code.strip()

    # ========================================================
    # СЛУЧАЙ "УТОЧНИТЬ"
    # ========================================================

    if recommended_code.lower() == "уточнить":

        result["recommended_code"] = "Уточнить"

        result["confidence"] = min(
            result["confidence"],
            39
        )

        result["supported_by"] = []

        result["vat"] = "Уточнить"
        result["duty"] = "Уточнить"

        if not isinstance(
            result.get("reasoning"),
            str
        ):
            result["reasoning"] = (
                "Недостаточно подтверждённых данных "
                "для однозначной классификации."
            )

        if not isinstance(
            result.get("customs_reasoning"),
            str
        ):
            result["customs_reasoning"] = (
                "Ставки не определены."
            )

        return result

    # ========================================================
    # КОНКРЕТНЫЙ КОД
    # ========================================================

    normalized_recommended = normalize_code(
        recommended_code
    )

    if not normalized_recommended:

        raise ValueError(
            "Финальная модель вернула некорректный "
            "recommended_code"
        )

    # --------------------------------------------------------
    # Получаем реальные кандидаты
    # --------------------------------------------------------

    all_candidates = get_unique_candidate_codes(
        candidate_codes
    )

    print(
        "FINAL UNIQUE CANDIDATES:",
        all_candidates
    )

    # --------------------------------------------------------
    # КРИТИЧЕСКАЯ ЗАЩИТА:
    #
    # Финальная модель НЕ МОЖЕТ придумать новый код.
    # --------------------------------------------------------

    if normalized_recommended not in all_candidates:

        print(
            "FINAL DECISION REJECTED:"
        )

        print(
            "Код финальной модели:",
            normalized_recommended
        )

        print(
            "Допустимые кандидаты:",
            all_candidates
        )

        return make_uncertain_result(
            "Финальная модель выбрала код "
            f"{recommended_code}, которого нет среди "
            "явно предложенных исходными моделями "
            "кандидатов. Новый код автоматически "
            "не создаётся."
        )

    # --------------------------------------------------------
    # Пересчитываем supported_by самостоятельно
    # --------------------------------------------------------

    real_supported_by = find_models_for_code(
        candidate_codes,
        normalized_recommended
    )

    result["supported_by"] = real_supported_by

    # --------------------------------------------------------
    # Если код предложен только одной моделью,
    # не разрешаем confidence >= 90.
    #
    # Один источник не запрещает выбрать код,
    # но confidence не должен быть искусственно завышен.
    # --------------------------------------------------------

    if len(real_supported_by) <= 1:

        result["confidence"] = min(
            result["confidence"],
            89
        )

    # --------------------------------------------------------
    # Текстовые поля
    # --------------------------------------------------------

    if not isinstance(
        result.get("reasoning"),
        str
    ):
        result["reasoning"] = str(
            result.get("reasoning", "")
        )

    if not isinstance(
        result.get("customs_reasoning"),
        str
    ):
        result["customs_reasoning"] = str(
            result.get(
                "customs_reasoning",
                ""
            )
        )

    # --------------------------------------------------------
    # VAT / DUTY
    # --------------------------------------------------------

    if result.get("vat") in (
        None,
        ""
    ):
        result["vat"] = "Уточнить"

    if result.get("duty") in (
        None,
        ""
    ):
        result["duty"] = "Уточнить"

    return result


# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================================

def make_final_decision(
    openai_result,
    deepseek_result,
    gigachat_result,
    yandex_result,
    description="",
    answers=None,
    vision_data=None
):

    answers = answers or []
    vision_data = vision_data or {}

    # ========================================================
    # 1. СОБИРАЕМ КАНДИДАТЫ
    # ========================================================

    candidate_codes = collect_all_candidate_codes(
        openai_result,
        deepseek_result,
        gigachat_result,
        yandex_result
    )

    unique_candidates = get_unique_candidate_codes(
        candidate_codes
    )

    print(
        "========== FINAL CANDIDATE CODES =========="
    )

    print(
        json.dumps(
            candidate_codes,
            ensure_ascii=False,
            indent=2
        )
    )

    print(
        "========== FINAL UNIQUE CANDIDATES =========="
    )

    print(
        json.dumps(
            unique_candidates,
            ensure_ascii=False,
            indent=2
        )
    )

    print(
        "============================================="
    )

    # ========================================================
    # 2. PROMPT
    # ========================================================

    prompt_path = Path(__file__).with_name("prompts") / "final_decision.txt"
    prompt = prompt_path.read_text(encoding="utf-8").format(
        description=description,
        answers_json=json.dumps(answers, ensure_ascii=False, indent=2),
        vision_data_json=json.dumps(vision_data, ensure_ascii=False, indent=2),
        openai_result_json=json.dumps(openai_result, ensure_ascii=False, indent=2),
        deepseek_result_json=json.dumps(deepseek_result, ensure_ascii=False, indent=2),
        gigachat_result_json=json.dumps(gigachat_result, ensure_ascii=False, indent=2),
        yandex_result_json=json.dumps(yandex_result, ensure_ascii=False, indent=2),
        unique_candidates_json=json.dumps(unique_candidates, ensure_ascii=False, indent=2),
    )
    # ========================================================
    # 3. ВЫЗОВ GPT
    # ========================================================

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты выполняешь строгую финальную "
                        "проверку кандидатов ТН ВЭД. "
                        "Используй только подтверждённые "
                        "факты и только коды из разрешённого "
                        "списка кандидатов. "
                        "Не придумывай новые коды."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content

        print(
            "========== FINAL DECISION RAW =========="
        )

        print(
            repr(content)
        )

        print(
            "========================================"
        )

        # ====================================================
        # 4. JSON
        # ====================================================

        result = clean_json(content)

        if not isinstance(result, dict):

            raise ValueError(
                "Финальный ответ имеет неправильный формат"
            )

        # ====================================================
        # 5. ПРОГРАММНАЯ ПРОВЕРКА
        # ====================================================

        result = validate_final_result(
            result,
            candidate_codes
        )

        # ====================================================
        # 6. ФИНАЛЬНЫЙ ЛОГ
        # ====================================================

        print(
            "========== FINAL DECISION VALIDATED =========="
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        print(
            "=============================================="
        )

        return result

    except Exception as e:

        print(
            "FINAL DECISION ERROR:",
            e
        )

        return make_uncertain_result(
            "Не удалось определить итоговую классификацию: "
            f"{str(e)}"
        )