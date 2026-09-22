from .wb_api import WildberriesAPI


def parse_wildberries(url):

    print("=" * 50)
    print("WILDBERRIES API")
    print("=" * 50)

    # Получаем основные данные товара
    data = WildberriesAPI.get_card(url)

    nm_id = data.get("nm_id")

    # Получаем detail
    detail_data = WildberriesAPI.get_detail(nm_id)

    # Ищем реально существующий image host
    test_image = WildberriesAPI.test_image_hosts(nm_id)

    print(
        "TEST IMAGE RESULT:",
        test_image
    )

    # Получаем изображение.
    # ВАЖНО: передаём найденный test_image.
    image_url = get_wb_image(
        data,
        nm_id,
        test_image
    )

    return {

        "imt_name":
            data.get("imt_name"),

        "subj_name":
            data.get("subj_name"),

        "subj_root_name":
            data.get("subj_root_name"),

        "vendor_code":
            data.get("vendor_code"),

        "options":
            data.get("options", []),

        "compositions":
            data.get("compositions", []),

        "image_url":
            image_url,
    }


def get_wb_image(data, nm_id, verified_image_url=None):

    print("\n========== WB IMAGE DEBUG ==========")

    print("NM ID:", nm_id)

    print(
        "MEDIA FILES:",
        data.get("mediaFiles")
    )

    print(
        "PHOTOS:",
        data.get("photos")
    )

    print(
        "PHOTO:",
        data.get("photo")
    )

    print(
        "MEDIA:",
        repr(data.get("media"))
    )

    print(
        "DATA:",
        repr(data.get("data"))
    )

    print(
        "DATA KEYS:",
        list(data.keys())
    )

    print(
        "VERIFIED IMAGE:",
        verified_image_url
    )

    print("====================================\n")


    # =====================================================
    # 1. Если test_image_hosts уже нашёл рабочую картинку
    # =====================================================

    if verified_image_url:

        verified_image_url = str(
            verified_image_url
        ).strip()

        if verified_image_url.startswith("http"):

            print(
                "WB VERIFIED IMAGE:",
                verified_image_url
            )

            return verified_image_url


    # =====================================================
    # 2. Пытаемся получить готовую ссылку из API
    # =====================================================

    candidates = []


    if data.get("mediaFiles"):

        candidates.extend(
            data["mediaFiles"]
        )


    if data.get("photos"):

        candidates.extend(
            data["photos"]
        )


    if data.get("photo"):

        candidates.append(
            data["photo"]
        )


    for item in candidates:

        if isinstance(item, dict):

            item = (
                item.get("big")
                or item.get("url")
                or item.get("c516x688")
            )


        if not item:
            continue


        item = str(item).strip()


        if not item:
            continue


        if item.startswith("http"):

            print(
                "WB IMAGE FROM API:",
                item
            )

            return item


    # =====================================================
    # 3. НЕ вычисляем basket через vol % 100
    # =====================================================
    #
    # Старый код:
    #
    # vol = nm_id // 100000
    # basket = vol % 100
    #
    # Для 29360157 получалось:
    #
    # basket-93
    #
    # Это НЕ является надёжным способом определения
    # WB image host.
    #
    # Поэтому здесь больше ничего не генерируем.
    # =====================================================

    print(
        "WB IMAGE: NOT FOUND"
    )

    return None