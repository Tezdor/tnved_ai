function getCsrfToken() {
    const cookie = document.cookie
        .split("; ")
        .find(item => item.startsWith("csrftoken="));

    return cookie
        ? decodeURIComponent(cookie.substring("csrftoken=".length))
        : "";
}


export async function downloadPDF(results, button = null) {
    if (!results) {
        alert("Результат анализа недоступен.");
        return;
    }

    if (button) {
        button.disabled = true;
    }

    try {
        const response = await fetch("/api/download-pdf/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify(results)
        });

        if (!response.ok) {
            throw new Error(
                `Не удалось сформировать PDF. Код: ${response.status}`
            );
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = "tnved_result.pdf";

        document.body.appendChild(link);
        link.click();
        link.remove();

        setTimeout(() => {
            window.URL.revokeObjectURL(url);
        }, 1000);
    } catch (error) {
        console.error("Ошибка скачивания PDF:", error);
        alert(error.message || "Не удалось скачать PDF.");
    } finally {
        if (button) {
            button.disabled = false;
        }
    }
}