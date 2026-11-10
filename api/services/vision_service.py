import os
import json
import base64
import imghdr

from .llm.client import client

from django.conf import settings

from pathlib import Path

# ============================================================
# MIME TYPE
# ============================================================

def get_image_mime(image_bytes):

    kind = imghdr.what(
        None,
        h=image_bytes
    )

    if kind == "png":
        return "image/png"

    if kind == "webp":
        return "image/webp"

    if kind == "gif":
        return "image/gif"

    return "image/jpeg"


# ============================================================
# IMAGE -> DATA URL
# ============================================================

def build_image_content_from_bytes(image_bytes):

    if not image_bytes:
        raise Exception(
            "Empty image bytes"
        )

    mime = get_image_mime(
        image_bytes
    )

    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return {
        "type": "image_url",
        "image_url": {
            "url": (
                f"data:{mime};base64,"
                f"{image_base64}"
            )
        }
    }


# ============================================================
# АНАЛИЗ ИЗОБРАЖЕНИЯ + ГЕНЕРАЦИЯ ВОПРОСОВ
# ============================================================

def analyze_image_and_generate_questions(
    image_bytes=None,
    description=""
):

    if not image_bytes:
        raise Exception(
            "Изображение не передано"
        )

    print(
        "IMAGE BYTES SIZE:",
        len(image_bytes)
    )

    image_content = (
        build_image_content_from_bytes(
            image_bytes
        )
    )


    # ========================================================
    # PROMPT
    # ========================================================

    prompt_path = Path(__file__).with_name("prompts") / "vision.txt"
    prompt = prompt_path.read_text(encoding="utf-8").format(
        description=description
    )

    # ========================================================
    # OPENAI
    # ========================================================

    response = client.chat.completions.create(

        model="gpt-4o-mini",

        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    image_content
                ]
            }
        ],

        temperature=0.1
    )


    # ========================================================
    # RAW RESPONSE
    # ========================================================

    content = (
        response
        .choices[0]
        .message
        .content
    )

    print(
        "========== RAW GPT =========="
    )

    print(
        repr(content)
    )

    print(
        "============================="
    )


    # ========================================================
    # CLEAN JSON
    # ========================================================

    content = content.strip()

    if content.startswith(
        "```json"
    ):
        content = content[
            len("```json"):
        ]

    elif content.startswith(
        "```"
    ):
        content = content[
            len("```"):
        ]


    if content.endswith(
        "```"
    ):
        content = content[
            :-3
        ]


    content = content.strip()


    # ========================================================
    # PARSE
    # ========================================================

    result = json.loads(
        content
    )


    # ========================================================
    # ЗАЩИТА ОТ ЛИШНИХ / НЕПРАВИЛЬНЫХ ВОПРОСОВ
    # ========================================================

    if not isinstance(
        result,
        dict
    ):
        raise Exception(
            "GPT вернул не JSON-объект"
        )


    questions = result.get(
        "questions",
        []
    )


    if not isinstance(
        questions,
        list
    ):
        questions = []


    # Максимум 7 вопросов
    result["questions"] = questions[:7]


    # Если вопросов нет —
    # гарантируем пустой массив
    if len(result["questions"]) == 0:
        result["questions"] = []


    print(
        "========== PARSED GPT =========="
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    print(
        "================================"
    )


    return result