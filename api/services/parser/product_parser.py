from urllib.parse import urlparse
import requests

from .generic_parser import parse_generic_site
from .yandex_market import parse_yandex_market
from .wildberries import parse_wildberries
from .ozon import parse_ozon


def is_direct_image_url(url):
    """
    Проверяет, является ли URL прямой ссылкой на изображение.
    Учитывает query-параметры, например:
    image.jpg?s=612x612&w=0&k=...
    """

    try:
        parsed = urlparse(url)
        path = parsed.path.lower()

        image_extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif",
            ".bmp",
            ".avif",
        )

        return path.endswith(image_extensions)

    except Exception:
        return False


def parse_direct_image(url):
    """
    Обработка прямой ссылки на изображение.

    Ничего не пытаемся парсить как HTML-страницу.
    Просто проверяем, что по URL действительно доступно изображение,
    и возвращаем его URL дальше в pipeline.
    """

    print("=" * 40)
    print("DIRECT IMAGE URL")
    print("=" * 40)
    print("IMAGE URL:", url)

    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                )
            },
        )

        print("IMAGE STATUS:", response.status_code)
        print("CONTENT TYPE:", response.headers.get("Content-Type"))
        print("IMAGE SIZE:", len(response.content))

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        if not content_type.startswith("image/"):
            print("WARNING: URL DID NOT RETURN IMAGE")
            print("CONTENT TYPE:", content_type)

            return {
                "title": "",
                "image": url,
                "specs": [],
            }

        print("DIRECT IMAGE OK")

        return {
            "title": "",
            "image": url,
            "specs": [],
        }

    except Exception as e:
        print("DIRECT IMAGE ERROR:", e)

        return {
            "title": "",
            "image": url,
            "specs": [],
        }


def parse_product_page(url):
    print("=" * 40)
    print("PRODUCT PARSER")
    print("=" * 40)

    parsed = urlparse(url)
    host = parsed.netloc.lower()

    print("HOST:", host)
    print("PATH:", parsed.path)

    # ==========================================
    # 1. ПРЯМАЯ ССЫЛКА НА ИЗОБРАЖЕНИЕ
    # ==========================================

    if is_direct_image_url(url):
        print("TYPE: DIRECT IMAGE")

        return parse_direct_image(url)

    # ==========================================
    # 2. ЯНДЕКС МАРКЕТ
    # ==========================================

    if "market.yandex.ru" in host:
        print("TYPE: YANDEX MARKET")

        return parse_yandex_market(url)

    # ==========================================
    # 3. WILDBERRIES
    # ==========================================

    if "wildberries.ru" in host:
        print("TYPE: WILDBERRIES")

        return parse_wildberries(url)

    # ==========================================
    # 4. OZON
    # ==========================================

    if "ozon.ru" in host:
        print("TYPE: OZON")

        return parse_ozon(url)

    # ==========================================
    # 5. ОБЫЧНЫЙ САЙТ
    # ==========================================

    print("TYPE: GENERIC SITE")

    return parse_generic_site(url)