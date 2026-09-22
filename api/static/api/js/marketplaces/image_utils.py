import os
import uuid
import requests

from django.conf import settings


def download_marketplace_image(image_url):
    """
    Скачивает картинку маркетплейса и сохраняет локально в MEDIA_ROOT.
    Возвращает URL вида /media/products/xxxx.webp
    """

    if not image_url:
        return None

    try:
        response = requests.get(
            image_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.wildberries.ru/",
            },
            timeout=15
        )

        response.raise_for_status()

        content = response.content

        if not content:
            print("IMAGE DOWNLOAD: пустой ответ")
            return None

        # Определяем расширение
        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        if "webp" in content_type:
            extension = ".webp"

        elif "png" in content_type:
            extension = ".png"

        elif "jpeg" in content_type or "jpg" in content_type:
            extension = ".jpg"

        else:
            extension = ".webp"

        filename = (
            f"{uuid.uuid4()}{extension}"
        )

        relative_path = os.path.join(
            "products",
            filename
        )

        full_path = os.path.join(
            settings.MEDIA_ROOT,
            relative_path
        )

        os.makedirs(
            os.path.dirname(full_path),
            exist_ok=True
        )

        with open(full_path, "wb") as f:
            f.write(content)

        print(
            "LOCAL IMAGE SAVED:",
            full_path
        )

        return (
            settings.MEDIA_URL +
            relative_path.replace("\\", "/")
        )

    except Exception as e:

        print(
            "IMAGE DOWNLOAD ERROR:",
            e
        )

        return None