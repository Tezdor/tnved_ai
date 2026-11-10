import os
import json
import requests

from .llm.json_utils import clean_json

from pathlib import Path


def ask_yandex_gpt(product_data):

    prompt_path = Path(__file__).with_name("prompts") / "yandex.txt"
    prompt = prompt_path.read_text(encoding="utf-8").format(
        product_data_json=json.dumps(product_data, ensure_ascii=False)
    )

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