const draftKey = "tnved.pending-questions";
const attemptedKey = "tnved.pending-questions-attempted";

async function withDraftStore(mode, operation) {
    const db = await new Promise((resolve, reject) => {
        const request = indexedDB.open("tnved-analysis-drafts", 1);

        request.onupgradeneeded = () => {
            request.result.createObjectStore("questions");
        };

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });

    try {
        return await new Promise((resolve, reject) => {
            const transaction = db.transaction("questions", mode);
            const request = operation(transaction.objectStore("questions"));

            transaction.oncomplete = () => resolve(request.result);
            transaction.onabort = () => reject(transaction.error);
        });
    } finally {
        db.close();
    }
}

export async function savePendingQuestions(formData) {
    const previousId = sessionStorage.getItem(draftKey);
    const id = crypto.randomUUID();

    await withDraftStore("readwrite", store => {
        if (previousId) {
            store.delete(previousId);
        }

        return store.put(Array.from(formData.entries()), id);
    });

    sessionStorage.setItem(draftKey, id);
    sessionStorage.removeItem(attemptedKey);
}

export async function takePendingQuestionsForResume() {
    const id = sessionStorage.getItem(draftKey);

    if (!id || sessionStorage.getItem(attemptedKey) === id) {
        return null;
    }

    const entries = await withDraftStore("readonly", store => store.get(id));

    if (!entries) {
        return null;
    }

    sessionStorage.setItem(attemptedKey, id);
    return {id, entries};
}

export async function clearPendingQuestions(id) {
    await withDraftStore("readwrite", store => store.delete(id));

    if (sessionStorage.getItem(draftKey) === id) {
        sessionStorage.removeItem(draftKey);
        sessionStorage.removeItem(attemptedKey);
    }
}