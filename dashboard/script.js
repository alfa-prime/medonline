// dashboard/script.js
document.addEventListener('DOMContentLoaded', () => {
    const menuLinks = document.querySelectorAll('.menu-list a');
    const contentPanels = document.querySelectorAll('.content-panel');

    menuLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault(); // Отменяем стандартное поведение ссылки

            // Убираем класс 'is-active' со всех ссылок
            menuLinks.forEach(l => l.classList.remove('is-active'));
            // Добавляем класс 'is-active' только кликнутой ссылке
            link.classList.add('is-active');

            // Получаем цель из data-атрибута (например, "overview")
            const target = link.dataset.target;

            // Скрываем все панели с контентом
            contentPanels.forEach(panel => {
                panel.style.display = 'none';
            });

            // Показываем нужную панель
            const targetPanel = document.getElementById(`content-${target}`);
            if (targetPanel) {
                targetPanel.style.display = 'block';
            }
        });
    });
});