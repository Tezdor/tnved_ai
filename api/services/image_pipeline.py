import requests
from urllib.parse import urlparse, parse_qs, unquote
from django.core.files.base import ContentFile
import uuid

# 1. реальная ссылка
def extract_real_image_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        if "img_url" in query:
            return unquote(query["img_url"][0])

        if "imgurl" in query:
            return unquote(query["imgurl"][0])

        return url
    except:
        return url

def is_image_url(url: str) -> bool:
    url = url.lower()
    return (
        url.startswith("http")
        and any(ext in url for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"])
    )

# 2. строгая проверка URL
def is_valid_image_url(url: str) -> bool:
    if not url:
        return False

    url = url.lower()

    if not url.startswith("http"):
        return False

    # минимальная проверка
    bad_domains = ["yandex.ru/images", "google.com/search"]
    if any(bad in url for bad in bad_domains):
        return False

    return True


def download_image(url: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
        }

        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        if "image" not in content_type:
            print("Not image:", content_type)
            return None

        # проверка размера 
        if len(response.content) < 500:
            print("Image too small or broken")
            return None

        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        elif "gif" in content_type:
            ext = ".gif"

        file_name = f"{uuid.uuid4()}{ext}"

        return ContentFile(response.content, name=file_name)

    except Exception as e:
        print("IMAGE DOWNLOAD ERROR:", e)
        return None


def process_image(image_file=None, image_url=None):

    if image_file:
        return image_file

    if image_url:
        image_url = extract_real_image_url(image_url)
        
        if not image_url.startswith("http"):
            return None

        return download_image(image_url)

    return None

