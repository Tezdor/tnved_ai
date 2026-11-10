import os
import json
import base64
from pathlib import Path

from .llm.client import client
from django.conf import settings
from .llm.json_utils import clean_json

# ============================================================
# Загрузка сохранённой картинки
# ============================================================

def image_to_data_url(image_path):

    if not image_path:
        return None


    image_path = Path(image_path)


    if not image_path.exists():

        print(
            "OPENAI IMAGE NOT FOUND:",
            image_path
        )

        return None


    # Определяем MIME
    suffix = image_path.suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }

    mime_type = mime_types.get(
        suffix,
        "image/webp"
    )


    try:

        with open(
            image_path,
            "rb"
        ) as image_file:

            image_bytes = (
                image_file.read()
            )


        if not image_bytes:

            print(
                "OPENAI IMAGE IS EMPTY:",
                image_path
            )

            return None


        encoded = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        return (
            f"data:{mime_type};base64,{encoded}"
        )


    except Exception as e:

        print(
            "OPENAI IMAGE READ ERROR:",
            e
        )

        return None


# ============================================================
# Получение пути картинки из vision_data
# ============================================================

def get_preview_path(vision_data):

    preview = (
        vision_data
        .get("preview")
    )


    if not preview:

        print(
            "OPENAI: preview отсутствует"
        )

        return None


    print(
        "OPENAI PREVIEW:",
        preview
    )


    # --------------------------------------------------------
    # preview обычно выглядит:
    #
    # /media/products/xxxxx.webp
    #
    # Нам нужно:
    #
    # MEDIA_ROOT/products/xxxxx.webp
    # --------------------------------------------------------

    preview = str(
        preview
    ).replace(
        "\\",
        "/"
    )


    media_url = str(
        settings.MEDIA_URL
    ).replace(
        "\\",
        "/"
    )


    if preview.startswith(
        media_url
    ):

        relative_path = (
            preview[
                len(media_url):
            ]
            .lstrip("/")
        )

    else:

        relative_path = (
            preview
            .lstrip("/")
        )


    image_path = (
        Path(
            settings.MEDIA_ROOT
        )
        / relative_path
    )


    print(
        "OPENAI IMAGE PATH:",
        image_path
    )


    return image_path


# ============================================================
# Генерация вопросов
# ============================================================

def generate_questions(product_description):

    prompt_path = Path(__file__).with_name("prompts") / "openai_questions.txt"
    prompt = prompt_path.read_text(encoding="utf-8").format(
        product_description=product_description
    )


    response = client.chat.completions.create(

        model="gpt-4o-mini",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    print(
        "===== GENERATE QUESTIONS RAW ====="
    )

    print(
        repr(content)
    )

    result = clean_json(
        content
    )

    if not isinstance(
        result,
        list
    ):
        print(
            "QUESTIONS: GPT RETURNED NOT LIST"
        )

        return []

    # Максимум 7 вопросов
    result = result[:7]

    print(
        "===== GENERATE QUESTIONS PARSED ====="
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    return result

# ============================================================
# Анализ ТН ВЭД
# ============================================================

def analyze_tnved(product_data):

    description = (
        product_data
        .get(
            "description",
            ""
        )
    )


    answers = (
        product_data
        .get(
            "answers",
            []
        )
    )


    vision_data = (
        product_data
        .get(
            "vision_data"
        )
        or {}
    )


    print(
        "VISION DATA INSIDE OPENAI:"
    )

    print(
        vision_data
    )

    print(
        type(vision_data)
    )


    # ========================================================
    # Получаем сохранённую картинку
    # ========================================================

    image_path = get_preview_path(
        vision_data
    )


    image_data_url = None


    if image_path:

        image_data_url = (
            image_to_data_url(
                image_path
            )
        )


    print(
        "OPENAI IMAGE AVAILABLE:",
        bool(image_data_url)
    )


    # ========================================================
    # Текстовый prompt
    # ========================================================
    prompt_path = Path(__file__).with_name("prompts") / "openai_analysis.txt"
    prompt = prompt_path.read_text(encoding="utf-8").format(
        description=description,
        detected_product=vision_data.get("detected_product", ""),
        material=vision_data.get("material", ""),
        purpose=vision_data.get("purpose", ""),
        answers_json=json.dumps(answers, ensure_ascii=False, indent=2)
    )

    # ========================================================
    # Формируем сообщение OpenAI
    # ========================================================

    content = [
        {
            "type": "text",
            "text": prompt
        }
    ]


    # ========================================================
    # Добавляем изображение
    # ========================================================

    if image_data_url:

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url
                }
            }
        )


        print(
            "OPENAI: IMAGE ADDED TO REQUEST"
        )

    else:

        print(
            "OPENAI: IMAGE NOT ADDED"
        )


    # ========================================================
    # Запрос OpenAI
    # ========================================================

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[
            {
                "role": "user",
                "content": content
            }
        ],

        temperature=0.2
    )


    result_content = (
        response
        .choices[0]
        .message
        .content
    )


    print(
        "===== OPENAI ====="
    )

    print(
        result_content
    )


    return clean_json(
        result_content
    )