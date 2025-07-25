document.addEventListener('DOMContentLoaded', () => {
    // --- Часть 1: Логика работы меню ---
    const menuLinks = document.querySelectorAll('.menu-list a');
    const contentPanels = document.querySelectorAll('.content-panel');
    const serviceStatusEl = document.getElementById('service-status');
    const appLogsEl = document.getElementById('app-logs');
    const errorLogsEl = document.getElementById('error-logs');

    menuLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            menuLinks.forEach(l => l.classList.remove('is-active'));
            link.classList.add('is-active');
            const target = link.dataset.target;
            contentPanels.forEach(panel => {
                panel.style.display = 'none';
            });
            const targetPanel = document.getElementById(`content-${target}`);
            if (targetPanel) {
                targetPanel.style.display = 'block';
            }
        });
    });

    // --- Часть 2: Логика для получения и обновления данных ---

    // Получаем ссылки на элементы, куда будем вставлять данные
//    const serviceStatusEl = document.querySelector('#content-overview #service-status'); // Уточняем селекторы
//    const appLogsEl = document.getElementById('app-logs');
//    const errorLogsEl = document.getElementById('error-logs');

    function updateUI(data) {
        if (!data) return;
        updateStatusIndicator(serviceStatusEl, data.fastapi_status, data.fastapi_status);
        updateLogBox(appLogsEl, data.app_logs);
        updateLogBox(errorLogsEl, data.error_logs);
    }

    function updateStatusIndicator(el, text, status) {
        if (!el || !text || !status) return;
        el.textContent = text.toUpperCase();
        el.className = 'status-indicator ' + status.toLowerCase();
    }

    function updateLogBox(el, logs) {
        if (!el) return;
        if (logs && logs.length > 0 && logs[0].startsWith('Log file not found')) {
            el.innerHTML = `<div class="log-message">${logs[0]}</div>`;
            return;
        }
        if (!logs || logs.length === 0) {
            el.innerHTML = '<div class="log-message">No logs yet.</div>';
            return;
        }

        let tableHTML = '<table class="log-table">';

        logs.forEach(line => {
            // Используем регулярное выражение для более надежного парсинга
            const match = line.match(/^([\d\- :]+)\| ([\w]+)\s*\| (.*)$/);

            if (match) {
                const timestamp = match[1].trim();
                const level = match[2].trim();
                const message = match[3].trim();

                // Превращаем уровень в класс, например, "INFO" -> "log-level-info"
                const levelClass = `log-level-${level.toLowerCase()}`;

                tableHTML += `<tr>
                    <td class="log-ts">${timestamp}</td>
                    <td class="log-level ${levelClass}">${level}</td>
                    <td class="log-msg">${message}</td>
                </tr>`;
            } else {
                // Если строка не соответствует формату, выводим ее как есть
                tableHTML += `<tr><td colspan="3">${line}</td></tr>`;
            }
        });

        tableHTML += '</table>';
        el.innerHTML = tableHTML;
        el.scrollTop = el.scrollHeight; // Прокручиваем вниз
    }

    async function initialLoad() {
        try {
            const response = await fetch('/api/dashboard/status');
            const data = await response.json();
            updateUI(data);
        } catch (e) {
            console.error("Initial load failed:", e);
            if (serviceStatusEl) updateStatusIndicator(serviceStatusEl, 'OFFLINE', 'offline');
            if (cookieStatusEl) updateStatusIndicator(cookieStatusEl, 'UNKNOWN', 'pending');
        }
    }

    function subscribeToUpdates() {
        const eventSource = new EventSource("/api/dashboard/stream");
        eventSource.addEventListener("update", (event) => {
            const data = JSON.parse(event.data);
            updateUI(data);
        });
        eventSource.onerror = () => {
            if (serviceStatusEl) updateStatusIndicator(serviceStatusEl, 'OFFLINE', 'offline');
        };
    }

    initialLoad();
    subscribeToUpdates();
});