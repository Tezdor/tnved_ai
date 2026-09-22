import {
setLatestResults
} from "./state.js";

import {
displayResults
} from "./results.js";

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
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

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


    if (data.error) {

        alert(
            "Ошибка: " +
            data.error
        );

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
