export let latestResults = null;

const requestStates = new Map();

let requestCount = 0;


export function createRequestState() {

    requestCount++;

    const requestId =
        requestCount;

    requestStates.set(
        requestId,
        {
            visionData: null,
            generatedQuestions: [],
            imageFromUrl: null,

            description: "",
            confirmedAnswers: []
        }
    );

    console.log(
        "REQUEST STATE CREATED:",
        requestId
    );

    return requestId;
}


export function getRequestState(
    requestId
) {

    if (!requestStates.has(requestId)) {

        console.warn(
            "REQUEST STATE NOT FOUND:",
            requestId
        );

        return null;
    }

    return requestStates.get(
        requestId
    );
}


/* =========================
   VISION DATA
========================= */

export function setVisionData(
    requestId,
    data
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return;
    }

    state.visionData =
        data;

    console.log(
        "VISION DATA SAVED FOR REQUEST:",
        requestId
    );
}


export function getVisionData(
    requestId
) {
    console.log(
        "GET VISION DATA REQUEST ID:",
        requestId
    );

    const state =
        getRequestState(requestId);

    console.log(
        "GET VISION DATA STATE:",
        state
    );

    if (!state) {
        console.warn(
            "GET VISION DATA: STATE NOT FOUND"
        );
        return null;
    }

    console.log(
        "GET VISION DATA RESULT:",
        state.visionData
    );

    return state.visionData;
}


/* =========================
   QUESTIONS
========================= */

export function setGeneratedQuestions(
    requestId,
    data
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return;
    }

    state.generatedQuestions =
        data || [];

    console.log(
        "QUESTIONS SAVED FOR REQUEST:",
        requestId
    );
}


export function getGeneratedQuestions(
    requestId
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return [];
    }

    return state.generatedQuestions;
}


/* =========================
   IMAGE URL
========================= */

export function setImageFromUrl(
    requestId,
    url
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return;
    }

    state.imageFromUrl =
        url;

    console.log(
        "IMAGE URL SAVED FOR REQUEST:",
        requestId,
        url
    );
}


export function getImageFromUrl(
    requestId
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return null;
    }

    return state.imageFromUrl;
}


/* =========================
   DESCRIPTION
========================= */

export function setDescription(
    requestId,
    description
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return;
    }

    state.description =
        description || "";

    console.log(
        "DESCRIPTION SAVED FOR REQUEST:",
        requestId
    );
}


export function getDescription(
    requestId
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return "";
    }

    return state.description;
}


/* =========================
   CONFIRMED ANSWERS
========================= */

export function setConfirmedAnswers(
    requestId,
    answers
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return;
    }

    state.confirmedAnswers =
        answers || [];

    console.log(
        "CONFIRMED ANSWERS SAVED FOR REQUEST:",
        requestId
    );
}


export function getConfirmedAnswers(
    requestId
) {

    const state =
        getRequestState(requestId);

    if (!state) {
        return [];
    }

    return state.confirmedAnswers;
}


/* =========================
   LATEST RESULTS
========================= */

export function setLatestResults(
    data
) {

    latestResults =
        data;
}


export function getLatestResults() {

    return latestResults;
}


/* =========================
   REQUEST COUNTER
========================= */

export function getNextRequestCount() {

    return createRequestState();
}


/* =========================
   REMOVE REQUEST
========================= */

export function removeRequestState(
    requestId
) {

    if (!requestStates.has(requestId)) {
        return;
    }

    requestStates.delete(
        requestId
    );

    console.log(
        "REQUEST STATE REMOVED:",
        requestId
    );
}