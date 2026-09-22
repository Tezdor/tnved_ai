import os
import requests
import json

from .openai_service import clean_json


def ask_deepseek(product_data):

    description = product_data.get(
        "description",
        ""
    )

    answers = product_data.get(
        "answers",
        []
    )

    vision_data = product_data.get(
        "vision_data"
    ) or {}

    print("VISION DATA INSIDE DEEPSEEK:")
    print(vision_data)
    print(type(vision_data))

    prompt = f"""
Ты эксперт по классификации ТН ВЭД ЕАЭС.

Твоя задача — определить максимально точный код ТН ВЭД.

Описание пользователя:

{description}

Результат анализа изображения:

Наименование товара:

{vision_data.get('detected_product', '')}

Материал:

{vision_data.get('material', '')}

Назначение:

{vision_data.get('purpose', '')}

Ответы пользователя:

{json.dumps(answers, ensure_ascii=False, indent=2)}

Определи наиболее вероятный код ТН ВЭД.

После определения кода самостоятельно определи:

1. ставку импортной таможенной пошлины для выбранного кода;
2. ставку НДС при импорте товара в Россию;
3. объясни, почему применяются именно такие ставки.

Ставка пошлины должна относиться именно к выбранному коду ТН ВЭД.

Если ставка зависит от дополнительных условий,
учти известные характеристики товара и опиши это
в customs_reasoning.

Верни ТОЛЬКО JSON:

{{
    "tnved_code": "",
    "title": "",
    "confidence": 0,
    "reasoning": "",
    "vat": "",
    "duty": "",
    "customs_reasoning": ""
}}
"""

    response = requests.post(
        url="https://api.proxyapi.ru/v1/chat/completions",

        headers={
            "Authorization": f"Bearer {os.getenv('PROXYAPI_API_KEY')}",
            "Content-Type": "application/json"
        },

        json={
            "model": "deepseek/deepseek-chat",

            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            "temperature": 0.2
        }
    )

    result = response.json()

    if "choices" not in result:
        raise Exception(
            f"Ошибка ProxyAPI / DeepSeek: {result}"
        )

    content = result["choices"][0]["message"]["content"]

    print(content)

    return clean_json(content)