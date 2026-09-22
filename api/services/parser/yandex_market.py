from .playwright_utils import get_page, close_page


def parse_yandex_market(url):

    print("=" * 40)
    print("YANDEX MARKET PARSER")
    print("=" * 40)

    p, browser, page = get_page(url)

    try:

        page.wait_for_load_state(
            "domcontentloaded",
            timeout=15000
        )

        # =====================================================
        # НАЗВАНИЕ
        # =====================================================

        title = page.title()

        # =====================================================
        # КАРТИНКА
        # =====================================================

        image_url = None

        # Сначала ищем OpenGraph image.
        # Это обычно намного лучше, чем первый <img>.
        try:

            image_url = page.locator(
                'meta[property="og:image"]'
            ).get_attribute("content")

        except Exception:
            pass

        # Если og:image нет — ищем изображения товара
        if not image_url:

            try:

                images = page.locator("img")

                for i in range(
                    min(images.count(), 30)
                ):

                    src = images.nth(i).get_attribute(
                        "src"
                    )

                    if not src:
                        continue

                    # Пропускаем маленькие картинки
                    if (
                        "32x32" in src or
                        "50x50" in src or
                        "64x64" in src
                    ):
                        continue

                    if (
                        "avatars.mds.yandex.net" in src or
                        "yastatic.net" in src
                    ):

                        image_url = src
                        break

            except Exception:
                pass

        image_url = normalize_yandex_image_url(
            image_url
        )

        # =====================================================
        # ХАРАКТЕРИСТИКИ
        # =====================================================

        specifications = {}

        rows = page.locator(
            '[data-zone-name="spec"] label'
        )

        for i in range(rows.count()):

            row = rows.nth(i)

            spans = row.locator("span")

            if spans.count() < 2:
                continue

            key = spans.nth(0).inner_text().strip()

            value = spans.nth(1).inner_text().strip()

            if key and value:

                specifications[key] = value

        print(
            "TITLE:",
            title
        )

        print(
            "IMAGE:",
            image_url
        )

        print(
            "SPECS:",
            len(specifications)
        )

        return {
            "title": title,
            "specifications": specifications,
            "image_url": image_url
        }

    finally:

        close_page(
            p,
            browser
        )


# =================================================
# ПОИСК НОРМАЛЬНОЙ КАРТИНКИ
# =================================================

def get_yandex_product_image(page):

    candidates = []

    try:

        images = page.locator("img")

        count = images.count()

        print(
            "TOTAL IMAGES:",
            count
        )

        for i in range(count):

            img = images.nth(i)

            try:

                src = img.get_attribute(
                    "src"
                )

            except Exception:

                src = None

            if not src:
                continue

            src = normalize_yandex_image_url(
                src
            )

            if not src:
                continue

            # -------------------------------------
            # Отбрасываем очевидный мусор
            # -------------------------------------

            lower = src.lower()

            if (
                "favicon" in lower
                or "logo" in lower
                or "icon" in lower
                or "32x32" in lower
                or "50x50" in lower
                or "64x64" in lower
            ):
                continue

            # -------------------------------------
            # Только изображения Яндекса
            # -------------------------------------

            if (
                "avatars.mds.yandex.net"
                not in lower
            ):
                continue

            candidates.append(
                src
            )

    except Exception as e:

        print(
            "IMAGE SEARCH ERROR:",
            e
        )

    # -----------------------------------------
    # Удаляем дубликаты
    # -----------------------------------------

    unique = []

    for url in candidates:

        if url not in unique:

            unique.append(url)

    print(
        "YANDEX IMAGE CANDIDATES:",
        unique
    )

    # -----------------------------------------
    # Берём первую нормальную картинку
    # -----------------------------------------

    if unique:

        return unique[0]

    return None


# =================================================
# НОРМАЛИЗАЦИЯ URL КАРТИНКИ
# =================================================

def normalize_yandex_image_url(url):

    if not url:
        return None

    url = str(url).strip()

    # Markdown
    if url.startswith("[") and "](" in url:

        try:

            url = url.split(
                "](",
                1
            )[1]

            url = url.rsplit(
                ")",
                1
            )[0]

        except Exception:
            pass

    url = url.strip("<>")

    # Убираем параметры
    url = url.split("?")[0]

    replacements = [
        "/32x32",
        "/50x50",
        "/64x64",
        "/80x80",
        "/100x100",
        "/120x120",
        "/150x150",
        "/200x200",
        "/300x300",
    ]

    for size in replacements:

        if size in url:

            url = url.replace(
                size,
                "/600x600"
            )

            break

    return url


# =================================================
# ФОРМИРУЕМ ОПИСАНИЕ ДЛЯ AI
# =================================================

def format_yandex_description(
    title,
    specifications
):

    result = []

    if title:

        result.append(
            "Название: " +
            title
        )

    if specifications:

        result.append(
            ""
        )

        result.append(
            "Характеристики:"
        )

        for key, value in specifications.items():

            if (
                value is None
                or value == ""
            ):
                continue

            result.append(
                f"{key}: {value}"
            )

    return "\n".join(
        result
    ).strip()