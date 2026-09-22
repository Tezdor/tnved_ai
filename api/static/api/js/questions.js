import {
    createRequestState,
    setVisionData,
    setGeneratedQuestions,
    setImageFromUrl,
    getImageFromUrl,
    setDescription
} from "./state.js";

import { sendToAI } from "./ai.js";


let activeRequestId = null;
let displayedRequestId = null;


export function getActiveRequestId() {
    return activeRequestId;
}


export function getDisplayedRequestId() {
    return displayedRequestId;
}


function getDescription() {

    const element =
        document.getElementById("description");

    if (!element)
        return "";

    return element.value.trim();

}

function getImageFiles() {

    const inputs = [
        document.getElementById("productImage"),
        document.getElementById("productFiles")
    ];


    const files = [];
    const seen = new Set();


    inputs.forEach(input => {

        if (
            !input ||
            !input.files ||
            !input.files.length
        ) {

            return;

        }


        Array.from(input.files).forEach(file => {

            if (
                !file ||
                !file.type ||
                !file.type.startsWith("image/")
            ) {

                return;

            }


            const key =
                `${file.name}_${file.size}_${file.lastModified}`;


            if (seen.has(key)) {

                return;

            }


            seen.add(key);

            files.push(file);

        });

    });


    console.log(
        "TOTAL IMAGE FILES:",
        files.length
    );


    return files;

}


function getInputUrl() {

    const element =
        document.getElementById("imageUrl");

    if (!element) {

        return "";

    }


    return normalizeInputUrl(
        element.value
    );

}


function normalizeInputUrl(url) {

    if (!url) {

        return "";

    }


    url =
        String(url).trim();


    const markdownMatch =
        url.match(
            /^\[.*?\]\((https?:\/\/.+?)\)$/
        );


    if (markdownMatch) {

        url =
            markdownMatch[1];

    }


    url =
        url
            .replace(/^<|>$/g, "")
            .trim();


    return url;

}


function isImageUrl(url) {

    if (!url) {

        return false;

    }


    url =
        normalizeInputUrl(url);


    if (
        url.includes(
            "/api/wb-image-proxy/"
        )
    ) {

        return true;

    }


    const cleanUrl =
        url
            .split("?")[0]
            .toLowerCase();


    return (
        /\.(jpg|jpeg|png|gif|webp|bmp|avif)$/i
            .test(cleanUrl)
    );

}


function isWildberriesUrl(url) {

    if (!url)
        return false;


    return (
        url.includes("wildberries.ru/catalog/") ||
        url.includes("www.wildberries.ru/catalog/") ||
        url.includes("wb.ru/catalog/")
    );

}


function isYandexMarketUrl(url) {

    if (!url) {

        return false;

    }


    return (
        url.includes("market.yandex.ru/") ||
        url.includes("market.yandex.com/")
    );

}


function showImagePreview(imageUrl) {

    if (!imageUrl)
        return;


    const container =
        document.getElementById(
            "previewImages"
        );


    const previewContainer =
        document.getElementById(
            "previewContainer"
        );


    if (!container) {

        console.warn(
            "previewImages не найден"
        );

        return;

    }


    if (previewContainer) {

        previewContainer.style.display =
            "block";

    }


    const img =
        document.createElement(
            "img"
        );

    let previewUrl =
        imageUrl;


    if (
        !imageUrl.includes(
            "/api/wb-image-proxy/"
        )
    ) {

        previewUrl =
            "/api/wb-image-proxy/?url=" +
            encodeURIComponent(
                imageUrl
            );

    }


    img.src =
        previewUrl;

    img.className =
        "preview-image";

    img.alt =
        "Изображение товара";


    img.onload =
        function () {

            console.log(
                "PREVIEW IMAGE LOADED:",
                previewUrl
            );

        };


    img.onerror =
        function () {

            console.error(
                "PREVIEW IMAGE LOAD ERROR:",
                previewUrl
            );

        };


    container.appendChild(
        img
    );


    console.log(
        "IMAGE PREVIEW ADDED:",
        previewUrl
    );

}


async function loadMarketplaceProduct(
    url,
    requestId
) {

    console.trace(
        "🔥 LOAD MARKETPLACE PRODUCT CALLED:",
        url
    );


    console.log(
        "MARKETPLACE URL:",
        url
    );


    console.log(
        "MARKETPLACE REQUEST ID:",
        requestId
    );


    try {

        console.trace(
            "🚨 QUESTIONS.JS → POST /api/parse_product/"
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

                    body: JSON.stringify({
                        url: url,
                        image_url: url
                    })
                }
            );


        const data =
            await response.json();


        console.log(
            "MARKETPLACE RESPONSE:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.error ||
                `HTTP ${response.status}`
            );

        }


        if (data.error) {

            throw new Error(
                data.error
            );

        }


        if (data.image_url) {

            setImageFromUrl(
                requestId,
                data.image_url
            );


            console.log(
                "RESOLVED IMAGE URL FOR REQUEST:",
                requestId,
                data.image_url
            );


            showImagePreview(
                data.image_url
            );

        }


        const descriptionElement =
            document.getElementById(
                "description"
            );


        if (descriptionElement) {

            const marketplaceDescription =
                formatMarketplaceData(data);


            if (marketplaceDescription) {

                descriptionElement.value =
                    marketplaceDescription;


                setDescription(
                    requestId,
                    marketplaceDescription
                );


                console.log(
                    "DESCRIPTION UPDATED:",
                    marketplaceDescription
                );


                console.log(
                    "DESCRIPTION SAVED FOR REQUEST:",
                    requestId
                );

            }

        }


        return data;

    }

    catch (error) {

        console.error(
            "MARKETPLACE LOAD ERROR:",
            error
        );


        throw error;

    }

}


function formatMarketplaceData(data) {

    let text = "";


    if (data.title) {

        text +=
            `Название: ${data.title}\n\n`;

    }


    if (
        data.specifications &&
        typeof data.specifications === "object"
    ) {

        text +=
            "Характеристики:\n";


        Object.entries(
            data.specifications
        ).forEach(
            ([key, value]) => {

                if (
                    key &&
                    value !== undefined &&
                    value !== null &&
                    String(value).trim()
                ) {

                    text +=
                        `${key}: ${value}\n`;

                }

            }
        );

    }


    if (data.imt_name) {

        text +=
            `Название: ${data.imt_name}\n\n`;

    }


    if (data.subj_root_name) {

        text +=
            `Категория: ${data.subj_root_name}\n\n`;

    }


    if (data.subj_name) {

        text +=
            `Подкатегория: ${data.subj_name}\n\n`;

    }


    if (data.vendor_code) {

        text +=
            `Артикул продавца: ${data.vendor_code}\n\n`;

    }


    if (
        data.options &&
        Array.isArray(data.options) &&
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


    if (
        data.compositions &&
        Array.isArray(data.compositions) &&
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


async function resolveImageSource(
    requestId
) {

    console.log(
        "RESOLVE IMAGE SOURCE FOR REQUEST:",
        requestId
    );

    const imageFiles =
        getImageFiles();


    if (imageFiles.length) {

        console.log(
            "IMAGE SOURCE: FILES"
        );


        console.log(
            "NUMBER OF FILES:",
            imageFiles.length
        );


        imageFiles.forEach(
            (file, index) => {

                console.log(
                    `IMAGE FILE ${index + 1}:`,
                    file.name,
                    file.size,
                    file.type
                );

            }
        );


        return {

            type: "files",

            files: imageFiles

        };

    }

    const savedImageUrl =
        getImageFromUrl(
            requestId
        );


    if (savedImageUrl) {

        const url =
            normalizeInputUrl(
                savedImageUrl
            );


        if (url) {

            console.log(
                "IMAGE SOURCE: SAVED REQUEST URL"
            );


            console.log(
                "SAVED IMAGE:",
                url
            );


            return {

                type: "url",

                url: url

            };

        }

    }

    const inputUrl =
        getInputUrl();


    if (!inputUrl) {

        return null;

    }


    console.log(
        "INPUT URL:",
        inputUrl
    );

    if (isImageUrl(inputUrl)) {

        console.log(
            "IMAGE SOURCE: DIRECT IMAGE URL"
        );


        setImageFromUrl(
            requestId,
            inputUrl
        );


        showImagePreview(
            inputUrl
        );


        return {

            type: "url",

            url: inputUrl

        };

    }

    if (
        isWildberriesUrl(inputUrl) ||
        isYandexMarketUrl(inputUrl)
    ) {

        console.log(
            "IMAGE SOURCE: MARKETPLACE FALLBACK"
        );


        const data =
            await loadMarketplaceProduct(
                inputUrl,
                requestId
            );


        if (
            data &&
            data.image_url
        ) {

            setImageFromUrl(
                requestId,
                data.image_url
            );


            console.log(
                "MARKETPLACE IMAGE SAVED FOR REQUEST:",
                requestId,
                data.image_url
            );


            return {

                type: "url",

                url: data.image_url

            };

        }


        throw new Error(
            "Маркетплейс не вернул image_url"
        );

    }


    console.warn(
        "Не удалось определить источник изображения:",
        inputUrl
    );


    return null;

}


export async function generateQuestions() {

    const existingImageUrl =
        window.imageFromUrl || null;


    const requestId =
        createRequestState();


    if (existingImageUrl) {

        setImageFromUrl(
            requestId,
            existingImageUrl
        );


        console.log(
            "EXISTING MARKETPLACE IMAGE SAVED FOR REQUEST:",
            requestId,
            existingImageUrl
        );

    }


    console.log(
        "================================"
    );


    console.log(
        "=== GENERATE QUESTIONS ==="
    );


    console.log(
        "REQUEST ID:",
        requestId
    );


    activeRequestId =
        requestId;


    let description =
        getDescription();


    console.log(
        "DESCRIPTION:",
        description
    );


    let imageSource = null;


    try {

        imageSource =
            await resolveImageSource(
                requestId
            );

    }

    catch (error) {

        console.error(
            "IMAGE SOURCE ERROR:",
            error
        );


        alert(
            "Не удалось получить изображение товара:\n" +
            error.message
        );


        return;

    }


    description =
        getDescription();


    setDescription(
        requestId,
        description
    );


    console.log(
        "FINAL DESCRIPTION:",
        description
    );


    console.log(
        "FINAL IMAGE SOURCE:",
        imageSource
    );


    if (
        !description &&
        !imageSource
    ) {

        alert(
            "Необходимо указать описание или изображение"
        );


        return;

    }

    if (
        imageSource &&
        imageSource.type === "url"
    ) {

        setImageFromUrl(
            requestId,
            imageSource.url
        );

    }


    const formData =
        new FormData();


    formData.append(
        "description",
        description
    );

    if (
        imageSource &&
        imageSource.type === "files"
    ) {

        console.log(
            "SENDING IMAGE FILES:",
            imageSource.files
        );


        imageSource.files.forEach(
            (file, index) => {

                console.log(
                    `SENDING IMAGE ${index + 1}:`,
                    file.name
                );


                formData.append(
                    "image",
                    file
                );

            }
        );

    }

    else if (
        imageSource &&
        imageSource.type === "url"
    ) {

        console.log(
            "SENDING IMAGE URL:",
            imageSource.url
        );


        formData.append(
            "image_url",
            imageSource.url
        );

    }


    const loader =
        document.getElementById(
            "loader"
        );


    if (loader) {

        loader.style.display =
            "block";

    }


    try {

        const response =
            await fetch(
                "/api/generate-questions/",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        console.log(
            "GENERATE QUESTIONS RESPONSE:",
            data
        );


        if (!response.ok) {

            alert(
                "Ошибка сервера: " +
                (
                    data.error ||
                    response.status
                )
            );


            return;

        }


        if (data.error) {

            alert(
                "Ошибка: " +
                data.error
            );


            return;

        }

        const visionData =
            data && data.detected_product
                ? data
                : null;


        if (visionData) {

            setVisionData(
                requestId,
                visionData
            );


            const detectedBlock =
                document.getElementById(
                    "detectedProductBlock"
                );


            if (detectedBlock) {

                detectedBlock.style.display =
                    "block";

            }


            const detectedText =
                document.getElementById(
                    "detectedProductText"
                );


            if (detectedText) {

                detectedText.innerText =
                    data.detected_product;

            }

        }

        const questions =
            Array.isArray(data.questions)
                ? data.questions
                : [];


        setGeneratedQuestions(
            requestId,
            questions
        );


        console.log(
            "QUESTIONS SAVED FOR REQUEST:",
            requestId
        );

        if (questions.length === 0) {

            console.log(
                "NO ADDITIONAL QUESTIONS FOR REQUEST:",
                requestId
            );


            displayedRequestId =
                requestId;


            sendToAI(
                [],
                description,
                visionData,
                requestId
            );


            resetProductForm();


            return;

        }

        renderQuestions(
            questions,
            requestId
        );

    }

    catch (error) {

        console.error(
            "GENERATE QUESTIONS ERROR:",
            error
        );


        alert(
            "Ошибка при получении вопросов: " +
            error.message
        );

    }

    finally {

        if (loader) {

            loader.style.display =
                "none";

        }

    }

}


export function renderQuestions(
    questions,
    requestId
) {

    displayedRequestId =
        requestId;


    console.log(
        "DISPLAYING QUESTIONS FOR REQUEST:",
        requestId
    );


    const container =
        document.getElementById(
            "questionsContainer"
        );


    if (!container) {

        console.error(
            "questionsContainer не найден"
        );


        return;

    }


    container.innerHTML =
        "";


    questions.forEach(
        (q, index) => {

            let html =
                `
                <div class="mb-4">

                    <h5>
                        ${q.question}
                    </h5>
                `;


            if (
                q.options &&
                q.options.length
            ) {

                q.options.forEach(
                    option => {

                        html +=
                            `
                            <div class="form-check">

                                <input
                                    class="form-check-input"
                                    type="radio"
                                    name="question_${index}"
                                    value="${option}"
                                >

                                <label
                                    class="form-check-label"
                                >
                                    ${option}
                                </label>

                            </div>
                            `;

                    }
                );

            }


            html +=
                `
                </div>
                `;


            container.innerHTML +=
                html;

        }
    );


    const modal =
        document.getElementById(
            "questionsModal"
        );


    if (modal) {

        modal.showModal();

    }

}


export function resetProductForm() {

    console.log(
        "RESET PRODUCT FORM"
    );

    const description =
        document.getElementById(
            "description"
        );


    if (description) {

        description.value = "";

    }

    const imageUrl =
        document.getElementById(
            "imageUrl"
        );


    if (imageUrl) {

        imageUrl.value = "";

    }

    const productImage =
        document.getElementById(
            "productImage"
        );


    if (productImage) {

        productImage.value = "";

    }

    const productFiles =
        document.getElementById(
            "productFiles"
        );


    if (productFiles) {

        productFiles.value = "";

    }

    window.imageFromUrl =
        null;

    const previewImages =
        document.getElementById(
            "previewImages"
        );


    if (previewImages) {

        previewImages.innerHTML =
            "";

    }


    const previewContainer =
        document.getElementById(
            "previewContainer"
        );


    if (previewContainer) {

        previewContainer.style.display =
            "none";

    }

    const detectedProductBlock =
        document.getElementById(
            "detectedProductBlock"
        );


    if (detectedProductBlock) {

        detectedProductBlock.style.display =
            "none";

    }


    const detectedProductText =
        document.getElementById(
            "detectedProductText"
        );


    if (detectedProductText) {

        detectedProductText.innerText =
            "";

    }

    const questionsContainer =
        document.getElementById(
            "questionsContainer"
        );


    if (questionsContainer) {

        questionsContainer.innerHTML =
            "";

    }

    const modal =
        document.getElementById(
            "questionsModal"
        );


    if (modal) {

        modal.close();

    }


    console.log(
        "PRODUCT FORM RESET COMPLETE"
    );

}

