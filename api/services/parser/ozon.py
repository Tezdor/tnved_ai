from bs4 import BeautifulSoup

from .playwright_utils import get_page, close_page, wait_page_loaded


def parse_ozon(url):

    print("OZON PARSER")

    p, browser, page = get_page(url)

    wait_page_loaded(page)

    html = page.content()

    soup = BeautifulSoup(html, "html.parser")

    # -------------------
    # Название товара
    # -------------------

    title = ""

    if soup.find("h1"):
        title = soup.find("h1").get_text(" ", strip=True)

    # -------------------
    # Картинка
    # -------------------

    image_url = ""

    img = soup.find("img")

    if img:
        image_url = (
            img.get("src")
            or img.get("data-src")
            or img.get("srcset", "").split(" ")[0]
        )

    # -------------------
    # Характеристики
    # -------------------

    specs = []

    section = soup.find(id="section-characteristics")

    if section:

        for dl in section.find_all("dl"):

            dt = dl.find("dt")
            dd = dl.find("dd")

            if not dt or not dd:
                continue

            key = dt.get_text(" ", strip=True)
            value = dd.get_text(" ", strip=True)

            specs.append(f"{key}: {value}")

    description = "\n".join(specs)

    close_page(p, browser)

    return {
        "title": title,
        "description": description,
        "image_url": image_url,
    }