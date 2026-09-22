let selectedFiles = [];



export function initImageUpload(){


    const inputs = [
        document.getElementById(
            "productImage"
        ),

        document.getElementById(
            "productFiles"
        )
    ];



    inputs.forEach(input => {


        if(!input)
            return;



        input.addEventListener(
            "change",
            function(event){



                const files =
                    Array.from(
                        event.target.files
                    );



                if(!files.length)
                    return;



                selectedFiles =
                    [
                        ...selectedFiles,
                        ...files
                    ];



                showImages(
                    selectedFiles
                );



                document
                .getElementById(
                    "imageUrl"
                )
                .value = "";



            }
        );



    });



}


let currentImageIndex = 0;
let previewImageUrls = [];


function showImages(files) {

    const container =
        document.getElementById(
            "previewImages"
        );

    const previewContainer =
        document.getElementById(
            "previewContainer"
        );

    const prevButton =
        document.getElementById(
            "prevImageBtn"
        );

    const nextButton =
        document.getElementById(
            "nextImageBtn"
        );

    const counter =
        document.getElementById(
            "imageCounter"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";

    previewImageUrls = [];

    currentImageIndex = 0;


    if (!files || !files.length) {

        if (previewContainer) {
            previewContainer.style.display =
                "none";
        }

        return;

    }


    previewImageUrls =
        new Array(files.length);


    let loadedCount = 0;


    Array.from(files).forEach(
        (file, index) => {

            const reader =
                new FileReader();


            reader.onload =
                function(event) {

                    previewImageUrls[index] =
                        event.target.result;

                    loadedCount++;


                    if (
                        loadedCount ===
                        files.length
                    ) {

                        renderCurrentImage();

                    }

                };


            reader.readAsDataURL(file);

        }
    );


    if (previewContainer) {

        previewContainer.style.display =
            "block";

    }


    function renderCurrentImage() {

        container.innerHTML = "";


        if (
            !previewImageUrls.length ||
            !previewImageUrls[
                currentImageIndex
            ]
        ) {

            return;

        }


        const img =
            document.createElement(
                "img"
            );


        img.src =
            previewImageUrls[
                currentImageIndex
            ];

        img.className =
            "preview-image";

        img.alt =
            `Изображение товара ${
                currentImageIndex + 1
            }`;


        container.appendChild(
            img
        );


        if (counter) {

            counter.textContent =
                `${currentImageIndex + 1} / ${
                    previewImageUrls.length
                }`;

        }


        const multiple =
            previewImageUrls.length > 1;


        if (prevButton) {

            prevButton.style.display =
                multiple
                    ? "flex"
                    : "none";

        }


        if (nextButton) {

            nextButton.style.display =
                multiple
                    ? "flex"
                    : "none";

        }

    }


    if (prevButton) {

        prevButton.onclick =
            function() {

                currentImageIndex--;

                if (
                    currentImageIndex < 0
                ) {

                    currentImageIndex =
                        previewImageUrls.length - 1;

                }


                renderCurrentImage();

            };

    }


    if (nextButton) {

        nextButton.onclick =
            function() {

                currentImageIndex++;

                if (
                    currentImageIndex >=
                    previewImageUrls.length
                ) {

                    currentImageIndex = 0;

                }


                renderCurrentImage();

            };

    }

}


export function getSelectedFiles(){


    return selectedFiles;


}

export function initPasteImage(){


document.addEventListener(
"paste",
function(event){



    const items =
        event.clipboardData.items;




    for(
        let item of items
    ){



        if(
            item.type.includes(
                "image"
            )
        ){



            const file =
                item.getAsFile();



            selectedFiles.push(
                file
            );



            const input =
                document.getElementById(
                    "productImage"
                );



            const dt =
                new DataTransfer();




            selectedFiles.forEach(
                f =>
                dt.items.add(f)
            );



            input.files =
                dt.files;



            showImages(
                selectedFiles
            );



            break;


        }


    }



});

}


export function isImageLink(url){


    if(!url)
        return false;



    url =
        url.toLowerCase();



    return (

        url.endsWith(".jpg") ||

        url.endsWith(".jpeg") ||

        url.endsWith(".png") ||

        url.endsWith(".gif") ||

        url.endsWith(".webp")

    );


}