import { downloadPDF } from "./pdf.js";

document.addEventListener('DOMContentLoaded', loadHistory);

async function loadHistory() {

    const container = document.getElementById('historyContainer');

    try {
        const response = await fetch('/api/history/');
        const data = await response.json();

        container.innerHTML = '';

        data.forEach((item, index) => {

            const card = document.createElement('article');

            card.innerHTML = `
                <header>
                    <strong>Запрос №${data.length - index}</strong>
                    <small>${new Date(item.created_at).toLocaleString()}</small>
                </header>

                <p><strong>Описание:</strong> ${item.description || '-'}</p>

                <details>
                    <summary>🔎 Результаты моделей</summary>

                    ${item.results.map(r => `
                        <div style="margin-top:10px;">
                            <strong>${r.model}</strong><br>
                            Код: ${r.tnved_code}<br>
                            Уверенность: ${r.confidence}<br>
                            ${r.reasoning}
                        </div>
                        <hr>
                    `).join('')}
                </details>

                ${
                    item.final
                    ? `
                    <footer>
                        <strong> Итог:</strong><br>
                        Код: ${item.final.recommended_code}<br>
                        Уверенность: ${item.final.confidence}<br>
                        Поддержка: ${item.final.supported_by.join(', ')}
                    </footer>
                    `
                    : ''
                }
            `;

            const pdfButton = document.createElement("button");

            pdfButton.type = "button";
            pdfButton.className = "secondary outline download-pdf-btn";
            pdfButton.textContent = "Скачать PDF";

            pdfButton.addEventListener("click", () => {
                const results = {
                    final: item.final
                };

                for (const modelResult of item.results) {
                    results[modelResult.model] = {
                        tnved_code: modelResult.tnved_code,
                        title: modelResult.title,
                        confidence: modelResult.confidence,
                        reasoning: modelResult.reasoning
                    };
                }

                downloadPDF(results, pdfButton);
            });

            card.appendChild(pdfButton);
            container.appendChild(card);
        });

    } catch (err) {
        container.innerHTML = 'Ошибка загрузки истории: ' + err;
    }
}