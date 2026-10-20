import {setLatestResults, getProductRequestId} from "./state.js";
import {displayResults} from "./results.js";
import { showGuestLimitNotice } from "./guest-limit.js";


function getCsrfToken() {
    const cookie = document.cookie
        .split("; ")
        .find(item => item.startsWith("csrftoken="));

    return cookie
        ? decodeURIComponent(cookie.substring("csrftoken=".length))
        : "";
}

export async function sendToAI(
    answers,
    description,
    visionData,
    requestId
) { 
console.log("REQUEST ID IN AI:", requestId);
console.log(
    "=== SEND TO AI ==="
);

console.log(
    "DESCRIPTION:",
    description
);

console.log(
    "VISION DATA:",
    visionData
);

console.log(
    "ANSWERS:",
    answers
);


const loader =
    document.getElementById("loader");

if (loader) {
    loader.style.display = "block";
}


try {

    const response =
        await fetch(
            "/api/analyze-product/",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken()
                },

                body: JSON.stringify({
                    request_id: getProductRequestId(requestId),

                    description:
                        description,

                    vision_data:
                        visionData,

                    answers:
                        answers
                })
            }
        );


    const data =
        await response.json();


    console.log(
        "ANALYZE PRODUCT RESPONSE:",
        data
    );


    if (loader) {
        loader.style.display = "none";
    }


    if (data.code === "GUEST_LIMIT_REACHED") {

    const modal = document.getElementById("questionsModal");

    if (modal && modal.open) {
        modal.close();
    }

    showGuestLimitNotice();

    return;
}

    if (data.error) {

        alert("Ошибка: " + data.error);

        return;
    }


    // Сохраняем результаты
    setLatestResults(data);


    // Выводим результаты
    displayResults(data, requestId);


    const modal =
        document.getElementById(
            "questionsModal"
        );

    if (modal) {
        modal.close();
    }

}

catch (error) {

    if (loader) {
        loader.style.display = "none";
    }


    console.error(
        "SEND TO AI ERROR:",
        error
    );


    alert(
        "Ошибка при анализе: " +
        error
    );
}


}
