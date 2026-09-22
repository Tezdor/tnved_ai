import os
import json
import re

from gigachat import GigaChat


def extract_gigachat_json(text):
    if not text:
        return None

    text = str(text).strip()

    # -----------------------------------------
    # Убираем Markdown
    # -----------------------------------------

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```",
        "",
        text
    )

    # -----------------------------------------
    # Нормализуем типографские кавычки
    # -----------------------------------------

    text = (
        text
        .replace("“", '"')
        .replace("”", '"')
        .replace("„", '"')
        .replace("«", '"')
        .replace("»", '"')
    )


    if (
        len(text) >= 2
        and text.startswith('"')
        and text.endswith('"')
    ):
        text = text[1:-1].strip()


    text = re.sub(
        r'("tnved_code"\s*:\s*"[^"]*")\s*//[^\n]*',
        r'\1',
        text
    )
   
    try:
        result = json.loads(text)

        if isinstance(result, dict):
            print(
                "GIGACHAT: корректный JSON получен сразу"
            )
            return result

    except json.JSONDecodeError:
        pass

    # -----------------------------------------
    # Пытаемся найти начало JSON
    # -----------------------------------------

    start = text.find("{")

    if start == -1:
        print(
            "GIGACHAT JSON ERROR: "
            "не найдено начало JSON"
        )

        print("GIGACHAT RAW TEXT:")
        print(text)

        return None

    json_part = text[start:]

    # -----------------------------------------
    # Извлекаем отдельные поля.
    #
    # Этот вариант специально устойчив к:
    #
    # 1. незакрытым/лишним кавычкам внутри reasoning
    # 2. Markdown после JSON
    # 3. дополнительному тексту после JSON
    # -----------------------------------------

    def extract_string_field(
        field_name,
        next_fields
    ):

        pattern = (
            r'"'
            + re.escape(field_name)
            + r'"\s*:\s*"'
            + r'(.*?)'
            + r'"'
            + r'\s*,\s*"'
            + r'(?:'
            + "|".join(
                re.escape(field)
                for field in next_fields
            )
            + r')"'
            + r'\s*:'
        )

        match = re.search(
            pattern,
            json_part,
            flags=re.DOTALL
        )

        if not match:
            return None

        return match.group(1).strip()

    # -----------------------------------------
    # tnved_code
    # -----------------------------------------

    tnved_match = re.search(
        r'"tnved_code"\s*:\s*"([^"]*)"',
        json_part,
        flags=re.DOTALL
    )

    tnved_code = (
        tnved_match.group(1).strip()
        if tnved_match
        else None
    )

    # -----------------------------------------
    # title
    # -----------------------------------------

    title_match = re.search(
        r'"title"\s*:\s*"(.*?)"\s*,\s*"confidence"\s*:',
        json_part,
        flags=re.DOTALL
    )

    title = (
        title_match.group(1).strip()
        if title_match
        else None
    )

    # -----------------------------------------
    # confidence
    # -----------------------------------------

    confidence_match = re.search(
        r'"confidence"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
        json_part
    )

    confidence = (
        float(confidence_match.group(1))
        if confidence_match
        else None
    )

    # -----------------------------------------
    # reasoning
    # -----------------------------------------

    reasoning = extract_string_field(
        "reasoning",
        [
            "vat"
        ]
    )

    # -----------------------------------------
    # vat
    # -----------------------------------------

    vat_match = re.search(
        r'"vat"\s*:\s*(?:"([^"]*)"|([0-9]+(?:\.[0-9]+)?))',
        json_part
    )

    vat = None

    if vat_match:

        vat = (
            vat_match.group(1)
            if vat_match.group(1) is not None
            else vat_match.group(2)
        )

    # -----------------------------------------
    # duty
    # -----------------------------------------

    duty_match = re.search(
        r'"duty"\s*:\s*(?:"([^"]*)"|([0-9]+(?:\.[0-9]+)?))',
        json_part
    )

    duty = None

    if duty_match:

        duty = (
            duty_match.group(1)
            if duty_match.group(1) is not None
            else duty_match.group(2)
        )

    # -----------------------------------------
    # customs_reasoning
    # -----------------------------------------

    customs_reasoning = extract_string_field(
        "customs_reasoning",
        []
    )

    # -----------------------------------------
    # Проверяем обязательные поля
    # -----------------------------------------

    result = {
        "tnved_code": tnved_code,
        "title": title,
        "confidence": confidence,
        "reasoning": reasoning,
        "vat": vat,
        "duty": duty,
        "customs_reasoning": customs_reasoning
    }

    missing = [
        key
        for key, value in result.items()
        if value is None
    ]

    if not missing:

        print(
            "GIGACHAT: JSON восстановлен "
            "из повреждённого ответа"
        )

        return result

    # -----------------------------------------
    # Не удалось восстановить
    # -----------------------------------------

    print(
        "GIGACHAT JSON ERROR: "
        "не удалось восстановить JSON"
    )

    print(
        "GIGACHAT MISSING FIELDS:",
        missing
    )

    print("GIGACHAT RAW TEXT:")
    print(text)

    return None

def ask_gigachat(product_data):

    prompt = f"""
Ты эксперт по классификации ТН ВЭД ЕАЭС.

Проанализируй товар и определи наиболее вероятный код ТН ВЭД.

Данные товара:

{json.dumps(
    product_data,
    ensure_ascii=False,
    indent=2
)}

ВАЖНО:

ВАЖНО:

1. Верни только один JSON-объект.
2. Не используй Markdown.
3. Не добавляй пояснения до или после JSON.
4. Не используй ```json.
5. Используй только обычные двойные кавычки " для JSON.
6. Не используй двойные кавычки " внутри значений полей title, reasoning и customs_reasoning.
7. Если необходимо выделить термин, используй одинарные кавычки '.
8. После закрывающей фигурной скобки ничего не пиши.
9. Поле confidence должно быть числом от 0 до 100.

После определения кода ТН ВЭД самостоятельно определи:

1. ставку импортной таможенной пошлины для выбранного кода ТН ВЭД;
2. ставку НДС при импорте товара в Россию;
3. объясни, почему применяются именно такие ставки.

ВАЖНО:

Ставка пошлины должна относиться именно к выбранному тобой
коду ТН ВЭД, а не указываться приблизительно.

Ставка НДС должна соответствовать применяемой ставке
при импорте данного товара в Россию.

Если ставка зависит от дополнительных условий,
учти известные характеристики товара и укажи это
в поле customs_reasoning.

Не выдумывай отдельную ставку только потому,
что она кажется типичной для данной категории товара.

Если ты не уверен в конкретной ставке,
не скрывай это. Укажи степень неопределённости
в поле customs_reasoning.

Формат ответа:

{{
    "tnved_code": "...",
    "title": "...",
    "confidence": 0,
    "reasoning": "...",
    "vat": "...",
    "duty": "...",
    "customs_reasoning": "..."
}}
"""

    credentials = os.getenv(
        "GIGACHAT_AUTH_KEY"
    )

    if not credentials:

        print(
            "GIGACHAT_AUTH_KEY не найден"
        )

        return {
            "tnved_code": "-",
            "title": "GigaChat недоступен",
            "confidence": 0,
            "reasoning": "Не задан GIGACHAT_AUTH_KEY",
            "vat": "-",
            "duty": "-",
            "customs_reasoning": "-"
        }

    try:

        with GigaChat(
            credentials=credentials,
            verify_ssl_certs=False
        ) as giga:

            response = giga.chat(
                prompt
            )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            print(
                "===== GIGACHAT ====="
            )

            print(
                content
            )

            result = extract_gigachat_json(
                content
            )

            if result is None:

                print(
                    "GIGACHAT: "
                    "не удалось распознать JSON"
                )

                return {
                    "tnved_code": "-",
                    "title": "Ошибка формата GigaChat",
                    "confidence": 0,
                    "reasoning": content,
                    "vat": "-",
                    "duty": "-",
                    "customs_reasoning": "-"
                }

            return {

                "tnved_code":
                    str(
                        result.get(
                            "tnved_code",
                            "-"
                        )
                    ),

                "title":
                    str(
                        result.get(
                            "title",
                            "-"
                        )
                    ),

                "confidence":
                    result.get(
                        "confidence",
                        0
                    ),

                "reasoning":
                    str(
                        result.get(
                            "reasoning",
                            "-"
                        )
                    ),

                "vat":
                    str(
                        result.get(
                            "vat",
                            "-"
                        )
                    ),

                "duty":
                    str(
                        result.get(
                            "duty",
                            "-"
                        )
                    ),

                "customs_reasoning":
                    str(
                        result.get(
                            "customs_reasoning",
                            "-"
                        )
                    )
            }

    except Exception as e:

        print(
            "GIGACHAT SDK ERROR:",
            e
        )

        return {

            "tnved_code": "-",

            "title":
                "GigaChat недоступен",

            "confidence": 0,

            "reasoning":
                str(e),

            "vat": "-",

            "duty": "-",

            "customs_reasoning":
                "-"
        }