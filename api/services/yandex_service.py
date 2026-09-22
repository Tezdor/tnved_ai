import os
import json
import requests

from .openai_service import clean_json


def ask_yandex_gpt(product_data):

    prompt = f"""
Ты эксперт по классификации ТН ВЭД.

Определи наиболее вероятный код ТН ВЭД.
После определения кода ТН ВЭД самостоятельно определи:

1. ставку импортной таможенной пошлины для данного кода;
2. ставку НДС при импорте в Россию;
3. объясни, почему применяются именно эти ставки.

ВАЖНО:

Ставка пошлины должна определяться именно для выбранного
тобой кода ТН ВЭД, а не указываться приблизительно.

Ставка НДС должна соответствовать применяемой ставке
при импорте данного товара в Россию.

Если ставка зависит от дополнительных условий,
укажи это в объяснении и выбери наиболее подходящую
ставку для описанных условий.

Не выдумывай отдельную ставку только потому,
что она кажется типичной для данной категории товара.

Данные товара:

{json.dumps(product_data, ensure_ascii=False)}

Верни ТОЛЬКО JSON:

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

    response = requests.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",

        headers={
            "Authorization":
                f"Api-Key {os.getenv('YANDEX_API_KEY')}"
        },

        json={
            "modelUri":
                f"gpt://{os.getenv('YANDEX_FOLDER_ID')}/yandexgpt/latest",

            "completionOptions": {
                "stream": False,
                "temperature": 0.2,
                "maxTokens": "2000"
            },

            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
    )

    result = response.json()

    print("===== YANDEX GPT =====")
    print(result)

    content = result["result"]["alternatives"][0]["message"]["text"]

    return clean_json(content)