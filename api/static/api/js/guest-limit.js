export function showGuestLimitNotice() {

    const existingNotice =
        document.getElementById("guestLimitNotice");

    if (existingNotice) {
        existingNotice.remove();
    }

    const notice = document.createElement("div");
    notice.id = "guestLimitNotice";

    notice.style.cssText = `
        position: fixed;
        inset: 0;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(5px);
        box-sizing: border-box;
    `;

    const card = document.createElement("div");

    card.style.cssText = `
        position: relative;
        width: 100%;
        max-width: 440px;
        max-height: 90vh;
        overflow-y: auto;
        box-sizing: border-box;
        background: #ffffff;
        border-radius: 20px;
        padding: 36px 30px;
        text-align: center;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.25);
        font-family: Arial, sans-serif;
        color: #1e293b;
    `;

    const icon = document.createElement("div");
    icon.textContent = "🔐";

    icon.style.cssText = `
        font-size: 42px;
        margin-bottom: 18px;
        line-height: 1.2;
    `;

    const heading = document.createElement("h2");
    heading.textContent = "Бесплатные анализы закончились";

    heading.style.cssText = `
        margin: 0 0 14px;
        font-size: 24px;
        font-weight: 700;
        line-height: 1.3;
        color: #0f172a;
    `;

    const message = document.createElement("p");
    message.textContent =
        "Вы использовали 2 бесплатных анализа. " +
        "Создайте аккаунт или войдите, чтобы продолжить " +
        "определение кодов ТН ВЭД.";

    message.style.cssText = `
        margin: 0 0 28px;
        font-size: 15px;
        line-height: 1.7;
        color: #64748b;
    `;

    const actions = document.createElement("div");

    actions.style.cssText = `
        display: flex;
        flex-direction: column;
        gap: 12px;
        width: 100%;
    `;

    const registerLink = document.createElement("a");
    registerLink.href = "/api/register/";
    registerLink.textContent = "Зарегистрироваться";

    registerLink.style.cssText = `
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        min-height: 48px;
        box-sizing: border-box;
        padding: 12px 20px;
        border-radius: 10px;
        background: #2563eb;
        color: #ffffff;
        font-size: 15px;
        font-weight: 600;
        text-decoration: none;
        border: 1px solid #2563eb;
        cursor: pointer;
        transition: background 0.2s ease;
    `;

    registerLink.addEventListener("mouseenter", () => {
        registerLink.style.background = "#1d4ed8";
    });

    registerLink.addEventListener("mouseleave", () => {
        registerLink.style.background = "#2563eb";
    });

    const loginLink = document.createElement("a");
    loginLink.href = "/api/login/";
    loginLink.textContent = "Войти в аккаунт";

    loginLink.style.cssText = `
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        min-height: 48px;
        box-sizing: border-box;
        padding: 12px 20px;
        border-radius: 10px;
        background: #f1f5f9;
        color: #1e293b;
        font-size: 15px;
        font-weight: 600;
        text-decoration: none;
        border: 1px solid #e2e8f0;
        cursor: pointer;
        transition: background 0.2s ease;
    `;

    loginLink.addEventListener("mouseenter", () => {
        loginLink.style.background = "#e2e8f0";
    });

    loginLink.addEventListener("mouseleave", () => {
        loginLink.style.background = "#f1f5f9";
    });

    actions.append(registerLink, loginLink);

    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.textContent = "✕";
    closeButton.setAttribute("aria-label", "Закрыть окно");

    closeButton.style.cssText = `
        position: absolute;
        top: 14px;
        right: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        padding: 0;
        border: none;
        border-radius: 50%;
        background: transparent;
        color: #64748b;
        font-size: 20px;
        cursor: pointer;
    `;

    closeButton.addEventListener("click", () => {
        notice.remove();
    });

    card.append(
        closeButton,
        icon,
        heading,
        message,
        actions
    );

    notice.appendChild(card);
    document.body.appendChild(notice);

    notice.addEventListener("click", (event) => {
        if (event.target === notice) {
            notice.remove();
        }
    });
}