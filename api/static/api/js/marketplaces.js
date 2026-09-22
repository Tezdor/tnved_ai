export function initMarketplace() {

    const input =
        document.getElementById("imageUrl");

    if (!input)
        return;

    input.addEventListener(
        "input",
        () => {

            console.log(
                "MARKETPLACE: input event"
            );

            clearTimeout(
                window.imageTimer
            );

            window.imageTimer =
                setTimeout(
                    fetchProductInfo,
                    700
                );
        }
    );
}


export async function fetchProductInfo() {

    console.trace("🔥 FETCH PRODUCT INFO CALLED");

    const input =
        document.getElementById("imageUrl");

    const descriptionField =
        document.getElementById("description");

    const previewContainer =
        document.getElementById("previewContainer");


    if (!input) {

        console.error(
            "Элемент #imageUrl не найден"
        );

        return;
    }


    const url =
        input.value.trim();


    console.log(
        "INPUT =",
        url
    );


    if (!url) {
        return;
    }


    try {

        /*
         * =====================================
         * ОТПРАВЛЯЕМ ССЫЛКУ НА СЕРВЕР
         * =====================================
         */

        console.trace(
            "🚨 MARKETPLACES.JS → POST /api/parse_product/"
        );


        const response =
            await fetch(
                "/api/parse_product/",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            url: url
                        })

                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Ответ сервера:",
            data
        );


        /*
         * =====================================
         * ОШИБКА
         * =====================================
         */

        if (data.error) {

            console.error(
                "Ошибка marketplace:",
                data.error
            );

            alert(
                "Ошибка получения товара: " +
                data.error
            );

            return;
        }


        /*
         * =====================================
         * ОПРЕДЕЛЯЕМ МАРКЕТПЛЕЙС
         * =====================================
         */

        const isYandex =
            url.includes(
                "market.yandex.ru"
            ) ||
            url.includes(
                "market.yandex.com"
            );


        const isWildberries =
            url.includes(
                "wildberries.ru"
            ) ||
            url.includes(
                "wb.ru"
            );


        console.log(
            "YANDEX MARKET:",
            isYandex
        );


        console.log(
            "WILDBERRIES:",
            isWildberries
        );


        /*
         * =====================================
         * ФОРМИРУЕМ ОПИСАНИЕ
         * =====================================
         */

        let description = "";


        /*
         * YANDEX MARKET
         */

        if (isYandex) {

            description =
                formatYandexData(data);

        }


        /*
         * WILDBERRIES
         */

        else if (isWildberries) {

            description =
                formatMarketplaceData(data);

        }


        /*
         * ДРУГОЙ МАРКЕТПЛЕЙС
         */

        else {

            if (data.title) {

                description =
                    data.title;

            }
            else {

                description =
                    formatMarketplaceData(data);

            }

        }


        /*
         * =====================================
         * ВЫВОДИМ ОПИСАНИЕ В TEXTAREA
         * =====================================
         */

        if (
            description &&
            descriptionField
        ) {

            descriptionField.value =
                description;


            descriptionField.dispatchEvent(
                new Event(
                    "input",
                    {
                        bubbles: true
                    }
                )
            );


            descriptionField.dispatchEvent(
                new Event(
                    "change",
                    {
                        bubbles: true
                    }
                )
            );

        }


        console.log(
            "FINAL DESCRIPTION:",
            description
        );


        /*
         * =====================================
         * ПОЛУЧАЕМ КАРТИНКУ
         * =====================================
         */

        let imageUrl =
            data.image_url ||
            data.image ||
            data.photo ||
            data.picture ||
            null;


        /*
         * =====================================
         * УЛУЧШАЕМ URL ЯНДЕКСА
         * =====================================
         */

        if (
            imageUrl &&
            isYandex
        ) {

            imageUrl =
                normalizeYandexImageUrl(
                    imageUrl
                );

        }


        console.log(
            "FINAL IMAGE URL:",
            imageUrl
        );


        /*
         * =====================================
         * СОХРАНЯЕМ URL ГЛОБАЛЬНО
         * =====================================
         *
         * questions.js потом использует
         * window.imageFromUrl
         */

        window.imageFromUrl =
            imageUrl;


        /*
         * =====================================
         * ПОКАЗЫВАЕМ КАРТИНКУ
         * =====================================
         *
         * ВАЖНО:
         *
         * Старого #imagePreview больше нет.
         *
         * Сейчас HTML использует:
         *
         * #previewImages
         *
         * Поэтому создаём <img> внутри
         * этого контейнера.
         */

        if (imageUrl) {

            showMarketplaceImage(
                imageUrl
            );

        }
        else {

            console.warn(
                "Сервер не вернул image_url"
            );

            window.imageFromUrl =
                null;

            clearMarketplacePreview();

        }


        /*
         * =====================================
         * ПОКАЗЫВАЕМ CONTAINER
         * =====================================
         */

        if (
            imageUrl &&
            previewContainer
        ) {

            previewContainer.style.display =
                "block";

        }


    }
    catch (error) {

        console.error(
            "Ошибка получения товара:",
            error
        );


        alert(
            "Ошибка получения товара: " +
            error.message
        );

    }

}


/*
 * =========================================
 * ПОКАЗ ИЗОБРАЖЕНИЯ MARKETPLACE
 * =========================================
 */

function showMarketplaceImage(imageUrl) {

    const previewImages =
        document.getElementById(
            "previewImages"
        );

    const imageCounter =
        document.getElementById(
            "imageCounter"
        );

    const previewContainer =
        document.getElementById(
            "previewContainer"
        );


    if (!previewImages) {

        console.error(
            "Не найден #previewImages"
        );

        return;
    }


    /*
     * Очищаем старое изображение.
     */

    previewImages.innerHTML = "";


    /*
     * Создаём настоящий <img>.
     */

    const image =
        document.createElement("img");


    image.alt =
        "Изображение товара";


    image.style.display =
        "block";

    image.style.width =
        "100%";

    image.style.height =
        "100%";

    image.style.maxWidth =
        "100%";

    image.style.maxHeight =
        "100%";

    image.style.objectFit =
        "contain";


    /*
     * Событие успешной загрузки.
     */

    image.onload =
        function () {

            console.log(
                "IMAGE LOADED:",
                image.src
            );

        };


    /*
     * Событие ошибки.
     */

    image.onerror =
        function () {

            console.error(
                "IMAGE LOAD ERROR:",
                image.src
            );

        };


    /*
     * Для внешних изображений используем
     * наш серверный proxy.
     */

    const proxyUrl =
        "/api/wb-image-proxy/?url=" +
        encodeURIComponent(imageUrl);


    console.log(
        "TRY TO LOAD IMAGE THROUGH PROXY:",
        proxyUrl
    );


    image.src =
        proxyUrl;


    /*
     * Добавляем изображение в существующий
     * контейнер карусели.
     */

    previewImages.appendChild(
        image
    );


    /*
     * Теперь у нас одно изображение.
     */

    if (imageCounter) {

        imageCounter.textContent =
            "1 / 1";

    }


    /*
     * Показываем контейнер.
     */

    if (previewContainer) {

        previewContainer.style.display =
            "block";

    }

}


/*
 * =========================================
 * ОЧИСТКА ПРЕДПРОСМОТРА
 * =========================================
 */

function clearMarketplacePreview() {

    const previewImages =
        document.getElementById(
            "previewImages"
        );

    const imageCounter =
        document.getElementById(
            "imageCounter"
        );

    const previewContainer =
        document.getElementById(
            "previewContainer"
        );


    if (previewImages) {

        previewImages.innerHTML = "";

    }


    if (imageCounter) {

        imageCounter.textContent =
            "0 / 0";

    }


    if (previewContainer) {

        previewContainer.style.display =
            "none";

    }

}


/*
 * =========================================
 * ЯНДЕКС MARKET → ОПИСАНИЕ
 * =========================================
 */

function formatYandexData(data) {

    let result = "";


    /*
     * Название
     */

    if (data.title) {

        result +=
            "Название: " +
            data.title +
            "\n\n";

    }


    /*
     * Характеристики
     */

    if (
        data.specifications &&
        typeof data.specifications === "object"
    ) {

        result +=
            "Характеристики:\n";


        Object.entries(
            data.specifications
        ).forEach(
            ([key, value]) => {

                if (
                    value === null ||
                    value === undefined ||
                    value === ""
                ) {

                    return;

                }


                /*
                 * Если значение массив
                 */

                if (
                    Array.isArray(value)
                ) {

                    value =
                        value.join(", ");

                }


                result +=
                    `${key}: ${value}\n`;

            }
        );

    }


    return result.trim();

}


/*
 * =========================================
 * НОРМАЛИЗАЦИЯ КАРТИНКИ ЯНДЕКСА
 * =========================================
 */

function normalizeYandexImageUrl(url) {

    if (!url) {

        return null;

    }


    /*
     * Иногда сервер может вернуть markdown:
     *
     * [https://...](https://...)
     *
     * Убираем markdown.
     */

    const markdownMatch =
        url.match(
            /^\[.*?\]\((.*?)\)$/
        );


    if (markdownMatch) {

        url =
            markdownMatch[1];

    }


    /*
     * Если это миниатюра 32x32,
     * пробуем заменить размер.
     */

    if (
        url.includes(
            "/32x32"
        )
    ) {

        const originalUrl =
            url.replace(
                "/32x32",
                "/orig"
            );


        console.log(
            "YANDEX ORIGINAL IMAGE:",
            originalUrl
        );


        return originalUrl;

    }


    /*
     * Другие возможные маленькие размеры.
     */

    if (
        url.includes(
            "/50x50"
        )
    ) {

        return url.replace(
            "/50x50",
            "/orig"
        );

    }


    if (
        url.includes(
            "/100x100"
        )
    ) {

        return url.replace(
            "/100x100",
            "/orig"
        );

    }


    return url;

}


/*
 * =========================================
 * WILDBERRIES → ОПИСАНИЕ
 * =========================================
 */

function formatMarketplaceData(data) {

    let text = "";


    /*
     * Название
     */

    if (data.imt_name) {

        text +=
            `Название: ${data.imt_name}\n\n`;

    }


    /*
     * Категория
     */

    if (data.subj_root_name) {

        text +=
            `Категория: ${data.subj_root_name}\n\n`;

    }


    /*
     * Артикул продавца
     */

    if (data.vendor_code) {

        text +=
            `Артикул продавца: ${data.vendor_code}\n\n`;

    }


    /*
     * Характеристики
     */

    if (
        data.options &&
        data.options.length
    ) {

        text +=
            "Характеристики:\n";


        data.options.forEach(
            item => {

                if (
                    item.name &&
                    item.value
                ) {

                    text +=
                        `${item.name}: ${item.value}\n`;

                }

            }
        );

    }


    /*
     * Состав
     */

    if (
        data.compositions &&
        data.compositions.length
    ) {

        text +=
            "\nСостав:\n";


        data.compositions.forEach(
            item => {

                if (item.name) {

                    text +=
                        `${item.name.trim()}\n`;

                }

            }
        );

    }


    return text.trim();

}


/*
 * =========================================
 * ОЧИСТКА URL
 * =========================================
 */

function cleanUrl(value) {

    if (!value) {

        return "";

    }


    value =
        String(value).trim();


    /*
     * Если URL пришёл как Markdown:
     *
     * [https://example.com](https://example.com)
     *
     * берём URL из второй части.
     */

    const markdownMatch =
        value.match(
            /^\[([^\]]+)\]\(([^)]+)\)$/
        );


    if (markdownMatch) {

        return markdownMatch[2].trim();

    }


    /*
     * Иногда URL может быть просто
     * заключён в <>
     */

    value =
        value
        .replace(/^<|>$/g, "")
        .trim();


    return value;

}


/*
 * =========================================
 * ПРОВЕРКА YANDEX MARKET URL
 * =========================================
 */

function isYandexMarketUrl(url) {

    if (!url) {

        return false;

    }


    url =
        cleanUrl(url);


    return (
        url.includes("market.yandex.ru") ||
        url.includes("market.yandex.com")
    );

}