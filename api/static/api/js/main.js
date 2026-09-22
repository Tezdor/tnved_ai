import {
    initImageUpload,
    initPasteImage
}
from "./images.js";


import {
    initMarketplace
}
from "./marketplaces.js";


import {
    generateQuestions
}
from "./questions.js";


import {
    submitAnswers
}
from "./answers.js";


import {
    downloadPDF
}
from "./pdf.js";




document.addEventListener(
    "DOMContentLoaded",
    ()=>{


        initImageUpload();


        initPasteImage();


        initMarketplace();



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
            "downloadPdfBtn"
        )
        ?.addEventListener(
            "click",
            downloadPDF
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