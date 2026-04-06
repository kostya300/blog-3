document.addEventListener('DOMContentLoaded', function () {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showMessage(text, type) {
        const messageBox = document.createElement('div');
        messageBox.textContent = text;
        messageBox.style.position = 'fixed';
        messageBox.style.top = '20px';
        messageBox.style.right = '20px';
        messageBox.style.padding = '10px 20px';
        messageBox.style.borderRadius = '4px';
        messageBox.style.color = '#fff';
        messageBox.style.backgroundColor = type === 'error' ? '#dc3545' : '#28a745';
        messageBox.style.zIndex = '9999';
        document.body.appendChild(messageBox);

        setTimeout(() => {
            messageBox.remove();
        }, 3000);
    }

    function deleteCommentWithUndo(button) {
        const commentId = button.dataset.commentId;
        const deleteUrl = button.dataset.deleteUrl;
        const commentElement = button.closest('.comment');

        // Блокируем кнопку и показываем статус
        button.disabled = true;
        button.textContent = 'Удаление...';

        // Сохраняем элемент на случай отмены
        const originalElement = commentElement.cloneNode(true);

        // Визуально «удаляем» комментарий
        commentElement.style.opacity = '0.5';
        commentElement.style.pointerEvents = 'none';

        // Показываем сообщение с кнопкой отмены
        const undoMessage = document.createElement('div');
        undoMessage.className = 'undo-message';
        undoMessage.innerHTML = `
            <span>Комментарий удалён</span>
            <button type="button" class="undo-btn">Отменить</button>
        `;

        commentElement.parentNode.insertAdjacentElement('beforebegin', undoMessage);

        fetch(deleteUrl, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            }
        })
            .then(response => {
                if (!response.ok) throw new Error('Ошибка сервера');

                // Успешное удаление: убираем сообщение и окончательно удаляем элемент
                undoMessage.remove();
                commentElement.remove();
                showMessage('Комментарий успешно удалён.', 'success');
            })
            .catch(err => {
                // Ошибка: восстанавливаем элемент, разблокируем кнопку
                undoMessage.remove();
                commentElement.replaceWith(originalElement);
                button.disabled = false;
                button.textContent = '×';
                showMessage('Ошибка удаления: ' + err.message, 'error');
            });

        // Обработчик кнопки «Отменить»
        undoMessage.querySelector('.undo-btn').addEventListener('click', function () {
            undoMessage.remove();
            commentElement.replaceWith(originalElement);
            button.disabled = false;
            button.textContent = '×';
            showMessage('Удаление отменено.', 'info');
        });

        // Автоматическое удаление сообщения через 5 секунд
        setTimeout(() => {
            if (undoMessage.parentNode) {
                undoMessage.remove();
            }
        }, 5000);
    }

    // Основной обработчик кликов
    document.querySelectorAll('.delete-comment-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            deleteCommentWithUndo(this);
        });
    });
});