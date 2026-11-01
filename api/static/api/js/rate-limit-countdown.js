document.querySelectorAll("[data-retry-after]").forEach(message => {
    const seconds = Number(message.dataset.retryAfter);

    if (!Number.isFinite(seconds) || seconds <= 0) {
        return;
    }

    const deadline = Date.now() + seconds * 1000;
    let timer;

    function updateCountdown() {
        const remaining = Math.max(
            0,
            Math.ceil((deadline - Date.now()) / 1000)
        );

        if (remaining === 0) {
            message.textContent = "Можно попробовать снова.";
            clearInterval(timer);
            return;
        }

        const minutes = Math.floor(remaining / 60);
        const restSeconds = remaining % 60;

        const time = minutes > 0
            ? `${minutes} мин. ${restSeconds} сек.`
            : `${restSeconds} сек.`;

        message.textContent =
            `Слишком много попыток. Повторите через ${time}`;
    }

    timer = setInterval(updateCountdown, 1000);
    updateCountdown();
});