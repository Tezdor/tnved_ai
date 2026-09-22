import {
    getGeneratedQuestions,
    getVisionData,
    setConfirmedAnswers,
    setDescription
} from "./state.js";


import {
    getDisplayedRequestId,
    resetProductForm
} from "./questions.js";


import {
    sendToAI
} from "./ai.js";



export function submitAnswers() {

    console.log(
        "!!! NEW ANSWERS.JS IS RUNNING !!!"
    );


    /*
        ==========================================
        ПОЛУЧАЕМ REQUEST ID
        ==========================================
    */

    const requestId =
        getDisplayedRequestId();


    console.log(
        "=== SUBMIT ANSWERS ==="
    );


    console.log(
        "ACTIVE REQUEST ID:",
        requestId
    );


    if (!requestId) {

        console.error(
            "ACTIVE REQUEST ID NOT FOUND"
        );

        alert(
            "Не удалось определить текущий запрос."
        );

        return;
    }



    /*
        ==========================================
        ПОЛУЧАЕМ ВОПРОСЫ
        ИМЕННО ЭТОГО REQUEST ID
        ==========================================
    */

    const generatedQuestions =
        getGeneratedQuestions(
            requestId
        );


    console.log(
        "QUESTIONS FOR REQUEST:",
        requestId,
        generatedQuestions
    );



    /*
        ==========================================
        СОБИРАЕМ ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ
        ==========================================
    */

    const answers =
        generatedQuestions.map(
            (q, index) => {

                const selected =
                    document.querySelector(
                        `input[name="question_${index}"]:checked`
                    );


                return {

                    question:
                        q.question,

                    answer:
                        selected
                            ? selected.value
                            : null

                };

            }
        );



    /*
        ==========================================
        ПОЛУЧАЕМ ОПИСАНИЕ ТОВАРА
        ==========================================
    */

    const descriptionElement =
        document.getElementById(
            "description"
        );


    const description =
        descriptionElement
            ? descriptionElement.value.trim()
            : "";



    /*
        ==========================================
        ПОЛУЧАЕМ VISION DATA
        ИМЕННО ЭТОГО REQUEST ID
        ==========================================
    */

    const visionData =
        getVisionData(
            requestId
        );



    /*
        ==========================================
        ЛОГИ
        ==========================================
    */

    console.log(
        "REQUEST ID:",
        requestId
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



    /*
        ==========================================
        СОХРАНЯЕМ ОТВЕТЫ
        ДЛЯ ЭТОГО REQUEST ID
        ==========================================
        
        Несмотря на название setConfirmedAnswers,
        здесь больше нет этапа подтверждения.

        Эти данные нужны для:
        - истории запросов
        - информационного окна результата
        - последующего личного кабинета
    */

    setConfirmedAnswers(
        requestId,
        answers
    );



    /*
        ==========================================
        СОХРАНЯЕМ ОПИСАНИЕ
        ДЛЯ ЭТОГО REQUEST ID
        ==========================================
    */

    setDescription(
        requestId,
        description
    );



    /*
        ==========================================
        ЗАКРЫВАЕМ ОКНО ВОПРОСОВ
        ==========================================
    */

    const questionsModal =
        document.getElementById(
            "questionsModal"
        );


    if (questionsModal) {

        questionsModal.close();

    }



    /*
        ==========================================
        СРАЗУ ЗАПУСКАЕМ АНАЛИЗ ТН ВЭД
        ==========================================
        
        ОКНА "ВСЁ ЛИ ВЕРНО?"
        БОЛЬШЕ НЕТ.
        
        После ответа пользователя сразу
        отправляем данные четырём моделям.
    */

    console.log(
        "=== START AI ANALYSIS ==="
    );


    console.log(
        "REQUEST ID:",
        requestId
    );


    sendToAI(
        answers,
        description,
        visionData,
        requestId
    );



    /*
        ==========================================
        ОЧИЩАЕМ ОСНОВНУЮ ФОРМУ
        ==========================================
        
        Анализ уже получил свои данные выше,
        поэтому форму можно сразу очистить.

        Это позволяет пользователю сразу
        начать следующий запрос, пока
        предыдущий продолжает обрабатываться.
    */

    resetProductForm();


    console.log(
        "=== FORM RESET ==="
    );

}