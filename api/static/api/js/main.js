import {initImageUpload, initPasteImage} from "./images.js";
import {initMarketplace} from "./marketplaces.js";
import {generateQuestions, resumePendingQuestions} from "./questions.js";
import {submitAnswers} from "./answers.js";
import { resumePendingAnalysis } from "./ai.js";

document.addEventListener(
    "DOMContentLoaded",
    ()=>{


        initImageUpload();


        initPasteImage();


        initMarketplace();
        Promise.resolve(resumePendingAnalysis()).then(() => {
            if (!document.getElementById("resultsHistory")?.childElementCount) {
                return resumePendingQuestions();
            }
        });

        document
        .getElementById(
            "generateBtn"
        )
        ?.addEventListener(
            "click",
            generateQuestions
        );

        document
        .getElementById(
            "submitAnswersBtn"
        )
        ?.addEventListener(
            "click",
            submitAnswers
        );

        document
        .getElementById(
            "closeModalBtn"
        )
        ?.addEventListener(
            "click",
            ()=>{


                document
                .getElementById(
                    "questionsModal"
                )
                .close();



            }
        );

        document
        .getElementById(
            "closeRequestInfoModalBtn"
        )
        ?.addEventListener(
            "click",
            ()=>{


                document
                .getElementById(
                    "requestInfoModal"
                )
                ?.close();


            }
        );


    }
);