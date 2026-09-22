import {
    setLatestResults,
    getVisionData,
    getConfirmedAnswers,
    getDescription
} from "./state.js";


function createModelsTable(data) {

    const models = [
        {
            name: "OpenAI GPT",
            key: "openai",
            data: data.openai
        },
        {
            name: "DeepSeek",
            key: "deepseek",
            data: data.deepseek
        },
        {
            name: "GigaChat",
            key: "gigachat",
            data: data.gigachat
        },
        {
            name: "YandexGPT",
            key: "yandex",
            data: data.yandex
        }
    ];


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "models-table-wrapper";


    wrapper.innerHTML = `

        <h3 class="models-table-title">
            Сравнение результатов моделей
        </h3>

        <div class="models-table-container">

            <table class="models-table">

                <thead>

                    <tr>

                        <th></th>

                        <th>Модель</th>

                        <th>ТН ВЭД</th>

                        <th>Уверенность</th>

                        <th>НДС</th>

                        <th>Пошлина</th>

                    </tr>

                </thead>

                <tbody>

                    ${models.map(model => {

                        const item =
                            model.data || {};

                        return `

                            <tr
                                class="model-row"
                                data-model="${model.key}"
                            >

                                <td class="model-expand-icon">
                                    ▶
                                </td>

                                <td>
                                    <strong>
                                        ${model.name}
                                    </strong>
                                </td>

                                <td>
                                    ${item.tnved_code || "-"}
                                </td>

                                <td>
                                    ${item.confidence ?? 0}%
                                </td>

                                <td>
                                    ${item.vat ?? "-"}
                                </td>

                                <td>
                                    ${item.duty ?? "-"}
                                </td>

                            </tr>

                            <tr
                                class="model-details-row"
                                data-details-for="${model.key}"
                                style="display: none;"
                            >

                                <td colspan="6">

                                    <div class="model-details">

                                        <p>
                                            <strong>
                                                Категория:
                                            </strong>

                                            ${item.title || "-"}
                                        </p>

                                        <p>
                                            <strong>
                                                Уверенность:
                                            </strong>

                                            ${item.confidence ?? 0}%
                                        </p>

                                        <p>
                                            <strong>
                                                Ставка НДС:
                                            </strong>

                                            ${item.vat ?? "-"}
                                        </p>

                                        <p>
                                            <strong>
                                                Импортная пошлина:
                                            </strong>

                                            ${item.duty ?? "-"}
                                        </p>

                                        <p>
                                            <strong>
                                                Обоснование НДС и пошлины:
                                            </strong>
                                        </p>

                                        <div class="model-details-text">
                                            ${item.customs_reasoning || "-"}
                                        </div>

                                        <p>
                                            <strong>
                                                Обоснование:
                                            </strong>
                                        </p>

                                        <div class="model-details-text">
                                            ${item.reasoning || "-"}
                                        </div>

                                    </div>

                                </td>

                            </tr>

                        `;

                    }).join("")}

                </tbody>

            </table>

        </div>
    `;

    const modelRows =
        wrapper.querySelectorAll(
            ".model-row"
        );


    modelRows.forEach(row => {

        row.addEventListener(
            "click",
            () => {

                const modelKey =
                    row.dataset.model;

                const detailsRow =
                    wrapper.querySelector(
                        `.model-details-row[data-details-for="${modelKey}"]`
                    );


                if (!detailsRow) {
                    return;
                }


                const icon =
                    row.querySelector(
                        ".model-expand-icon"
                    );


                const isOpen =
                    detailsRow.style.display !== "none";


                if (isOpen) {

                    detailsRow.style.display =
                        "none";

                    row.classList.remove(
                        "model-row-open"
                    );

                    if (icon) {
                        icon.textContent =
                            "▶";
                    }

                }
                else {

                    detailsRow.style.display =
                        "table-row";

                    row.classList.add(
                        "model-row-open"
                    );

                    if (icon) {
                        icon.textContent =
                            "▼";
                    }

                }

            }
        );

    });


    return wrapper;
}


function getResultTitle(
    data,
    requestId
) {

    console.log(
        "=== GET RESULT TITLE ==="
    );

    console.log(
        "RESULT TITLE REQUEST ID:",
        requestId
    );

    const visionData =
        getVisionData(requestId);

    console.log(
        "RESULT TITLE VISION DATA:",
        visionData
    );

    if (
        visionData &&
        visionData.detected_product &&
        visionData.detected_product.trim()
    ) {

        console.log(
            "RESULT TITLE FROM DETECTED PRODUCT:",
            visionData.detected_product
        );

        return visionData.detected_product.trim();
    }


    const description =
        getDescription(requestId);

    console.log(
        "RESULT TITLE FALLBACK DESCRIPTION:",
        description
    );

    if (
        description &&
        description.trim()
    ) {

        return description.trim();
    }


    return "Результат анализа";
}


export function displayResults(
    data,
    requestId
) {

    console.log(
        "=== DISPLAY RESULTS ==="
    );

    console.log(
        "RESULT DATA:",
        data
    );

    console.log(
        "RESULT REQUEST ID:",
        requestId
    );


    const resultTitle =
        getResultTitle(
            data,
            requestId
        );


    const container =
        document.getElementById(
            "resultsHistory"
        );


    if (!container) {

        console.error(
            "resultsHistory not found"
        );

        return;
    }


    setLatestResults(
        data
    );

    const visionData =
        getVisionData(
            requestId
        );


    const confirmedAnswers =
        getConfirmedAnswers(
            requestId
        );


    const description =
        getDescription(
            requestId
        );


    console.log(
        "RESULT DESCRIPTION:",
        description
    );

    console.log(
        "RESULT VISION DATA:",
        visionData
    );

    console.log(
        "RESULT CONFIRMED ANSWERS:",
        confirmedAnswers
    );


    const block =
        document.createElement(
            "article"
        );


    block.className =
        "request-block";


    block.dataset.requestId =
        requestId;


    block.innerHTML = `

        <div class="request-header">

            <h2>
                ${resultTitle}
            </h2>

            <button
                type="button"
                class="secondary result-info-btn"
                title="Данные запроса"
            >
                ⓘ
            </button>

        </div>


        <!--
            Здесь будет компактная таблица
            с результатами всех моделей.
        -->


        <!-- FINAL -->

        <div class="final-card">

            <h3>
                Итоговая рекомендация
            </h3>

            <p>
                <strong>Код:</strong>
                ${data.final?.recommended_code || "-"}
            </p>

            <p>
                <strong>НДС:</strong>
                ${data.final?.vat || "-"}
            </p>

            <p>
                <strong>Импортная пошлина:</strong>
                ${data.final?.duty || "-"}
            </p>

            <p>
                <strong>Уверенность:</strong>
                ${data.final?.confidence ?? 0}%
            </p>

            <p>
                <strong>Поддерживается:</strong>
                ${
                    (data.final?.supported_by || [])
                    .join(", ")
                    || "-"
                }
            </p>

            <p>
                <strong>Обоснование НДС и пошлины:</strong>
                ${data.final?.customs_reasoning || "-"}
            </p>

            <p>
                <strong>Обоснование:</strong>
                ${data.final?.reasoning || "-"}
            </p>

        </div>

    `;


    const modelsTable =
        createModelsTable(data);


    const finalCard =
        block.querySelector(
            ".final-card"
        );


    if (finalCard) {

        finalCard.parentNode.insertBefore(
            modelsTable,
            finalCard
        );

    }


    const infoButton =
        block.querySelector(
            ".result-info-btn"
        );


    if (infoButton) {

        infoButton.addEventListener(
            "click",
            () => {

                showRequestInfo(
                    requestId,
                    description,
                    visionData,
                    confirmedAnswers
                );

            }
        );

    }


    container.prepend(
        block
    );

    const resultsSection =
        document.getElementById(
            "resultsSection"
        );


    if (resultsSection) {

        resultsSection.style.display =
            "block";

    }

}


function showRequestInfo(
    requestId,
    description,
    visionData,
    answers
) {

    const modal =
        document.getElementById(
            "requestInfoModal"
        );


    if (!modal) {

        console.error(
            "requestInfoModal not found"
        );

        return;
    }


    const descriptionElement =
        document.getElementById(
            "requestInfoDescription"
        );


    if (descriptionElement) {

        descriptionElement.textContent =
            description || "-";

    }


    const productElement =
        document.getElementById(
            "requestInfoProduct"
        );


    if (productElement) {

        productElement.textContent =
            visionData?.detected_product
            || "-";

    }


    const materialElement =
        document.getElementById(
            "requestInfoMaterial"
        );


    if (materialElement) {

        materialElement.textContent =
            visionData?.material
            || "-";

    }


    const answersContainer =
        document.getElementById(
            "requestInfoAnswersContainer"
        );


    if (answersContainer) {

        answersContainer.innerHTML =
            "";


        if (
            !answers ||
            answers.length === 0
        ) {

            answersContainer.innerHTML =
                "<p>Ответы отсутствуют.</p>";

        }
        else {

            answers.forEach(
                (item) => {

                    const answerBlock =
                        document.createElement(
                            "div"
                        );


                    answerBlock.className =
                        "request-info-answer";


                    const question =
                        document.createElement(
                            "strong"
                        );


                    question.textContent =
                        item.question;


                    const answer =
                        document.createElement(
                            "p"
                        );


                    answer.textContent =
                        item.answer
                        || "Не указано";


                    answerBlock.appendChild(
                        question
                    );

                    answerBlock.appendChild(
                        answer
                    );


                    answersContainer.appendChild(
                        answerBlock
                    );

                }
            );

        }

    }


    const requestIdElement =
        document.getElementById(
            "requestInfoRequestId"
        );


    if (requestIdElement) {

        requestIdElement.textContent =
            requestId;

    }


    modal.showModal();
}