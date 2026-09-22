import requests

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

from ..image_pipeline import extract_real_image_url


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}


def load_page(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
        allow_redirects=True
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


def get_title(soup):

    og = soup.find("meta", property="og:title")
    if og:
        return og.get("content", "").strip()

    twitter = soup.find("meta", attrs={"name": "twitter:title"})
    if twitter:
        return twitter.get("content", "").strip()

    if soup.title:
        return soup.title.text.strip()

    return ""


def get_description(soup):

    meta = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    if meta:
        return meta.get("content", "")

    og = soup.find(
        "meta",
        property="og:description"
    )

    if og:
        return og.get("content", "")

    return ""


def get_image_url(soup):

    selectors = [

        ("property", "og:image"),

        ("name", "twitter:image"),

        ("property", "og:image:url"),

    ]

    for attr, value in selectors:

        tag = soup.find("meta", attrs={attr: value})

        if tag:

            url = tag.get("content")

            if url:
                return extract_real_image_url(url)
        
    return None


def parse_generic_site(url):

    print("=== parse_product_page ===")
    print(url)

    parsed = urlparse(url)

    print(parsed.netloc)
    print(parsed.path)

    parsed = urlparse(url)

    # ----------------------------------------------------
    # Яндекс.Картинки
    # ----------------------------------------------------

    if "yandex.ru" in parsed.netloc and "/images/search" in parsed.path:

        params = parse_qs(parsed.query)
        print(params)
        print(params.get("img_url"))

        img = params.get("img_url")

        if img:

            return {
                "title": "",
                "description": "",
                "image_url": unquote(img[0])
            }

    # ----------------------------------------------------
    # Прямая ссылка на картинку
    # ----------------------------------------------------

    lower = url.lower()

    if lower.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):

        return {
            "title": "",
            "description": "",
            "image_url": url
        }

    # ----------------------------------------------------
    # Любой интернет-магазин
    # ----------------------------------------------------

    soup = load_page(url)

    title = get_title(soup)

    description = get_description(soup)

    image_url = get_image_url(soup)

    return {
        "title": title,
        "description": description,
        "image_url": image_url
    }