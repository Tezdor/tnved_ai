import os
import requests
import json

from .llm.json_utils import clean_json

from pathlib import Path


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

    prompt_path = Path(__file__).with_name("prompts") / "deepseek.txt"
    prompt = prompt_path.read_text(encoding="utf-8").format(
        description=description,
        detected_product=vision_data.get("detected_product", ""),
        material=vision_data.get("material", ""),
        purpose=vision_data.get("purpose", ""),
        answers_json=json.dumps(answers, ensure_ascii=False, indent=2)
    )

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