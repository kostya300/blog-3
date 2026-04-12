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

// Храним ссылку на текущее активное сообщение отмены
let currentUndoMessage = null;

function deleteCommentWithUndo(button) {
    // Если уже есть активное сообщение отмены — удаляем его
    if (currentUndoMessage && currentUndoMessage.parentNode) {
        currentUndoMessage.remove();
        currentUndoMessage = null;
    }

    const commentId = button.dataset.commentId;
    const deleteUrl = button.dataset.deleteUrl;
    const commentElement = button.closest('.comment');

    // Сохраняем исходное состояние кнопки и элемента
    const originalButtonText = button.textContent;
    const originalOpacity = commentElement.style.opacity;
    const originalPointerEvents = commentElement.style.pointerEvents;
    const originalElement = commentElement.cloneNode(true);

    let isCancelled = false;

    // Блокируем кнопку
    button.disabled = true;
    button.textContent = 'Удаление...';

    // Визуальное «удаление»
    commentElement.style.opacity = '0.5';
    commentElement.style.pointerEvents = 'none';

    // Создаём сообщение с кнопкой отмены
    const undoMessage = document.createElement('div');
    undoMessage.className = 'undo-message';
    undoMessage.innerHTML = `
        <span>Комментарий будет удалён. Отменить в течение 5 секунд:</span>
        <button type="button" class="undo-btn">Отменить</button>
    `;

    commentElement.parentNode.insertAdjacentElement('beforebegin', undoMessage);
    currentUndoMessage = undoMessage; // Сохраняем ссылку

    // Функция отмены
    function cancelDeletion() {
        if (isCancelled) return;

        isCancelled = true;

        // Удаляем сообщение отмены
        if (undoMessage && undoMessage.parentNode) {
            undoMessage.remove();
            currentUndoMessage = null;
        }

        // Восстанавливаем оригинальный элемент
        commentElement.replaceWith(originalElement);

        // Разблокируем кнопку и возвращаем исходный текст
        const restoredButton = originalElement.querySelector('.delete-comment-btn');
        restoredButton.disabled = false;
        restoredButton.textContent = originalButtonText;

        // Восстанавливаем стили
        originalElement.style.opacity = originalOpacity;
        originalElement.style.pointerEvents = originalPointerEvents;

        showMessage('Удаление отменено.', 'info');
    }

    // Обработчик кнопки «Отменить»
    undoMessage.querySelector('.undo-btn').addEventListener('click', cancelDeletion, { once: true });

    // Откладываем запрос на сервер
    setTimeout(() => {
        if (isCancelled) {
            return;
        }

        fetch(deleteUrl, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Ошибка сервера');
            // Окончательно удаляем комментарий
            commentElement.remove();
            showMessage('Комментарий успешно удалён.', 'success');
        })
        .catch(err => {
            // При ошибке восстанавливаем элемент
            commentElement.replaceWith(originalElement);
            const restoredButton = originalElement.querySelector('.delete-comment-btn');
            restoredButton.disabled = false;
            restoredButton.textContent = originalButtonText;
            // Восстанавливаем стили при ошибке
            originalElement.style.opacity = originalOpacity;
            originalElement.style.pointerEvents = originalPointerEvents;
            showMessage('Не удалось удалить комментарий: ' + err.message, 'error');
        })
        .finally(() => {
            // Всегда очищаем сообщение отмены
            if (currentUndoMessage && currentUndoMessage.parentNode) {
                currentUndoMessage.remove();
                currentUndoMessage = null;
            }
        });
    }, 5000);
}

// Обработчик для кнопки удаления
document.querySelectorAll('.delete-comment-btn').forEach(button => {
    button.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation(); // Предотвращаем всплытие события
        deleteCommentWithUndo(this);
    });
});

// Обработчик для кнопки лайка
document.querySelectorAll('.like-comment-btn').forEach(button => {
    button.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation(); // Предотвращаем всплытие события

        const commentId = this.dataset.commentId;
        const isLiked = this.dataset.liked === 'true';

        fetch('/toggle-comment-like/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ comment_id: commentId })
        })
        .then(response => response.json())
        .then(data => {
            // Обновляем интерфейс
            this.dataset.liked = data.liked ? 'true' : 'false';
            this.querySelector('.heart-icon').textContent = data.liked ? '❤' : '♡';
            this.querySelector('.likes-count').textContent = data.likes_count;
        })
        .catch(error => {
            console.error('Ошибка при лайке:', error);
            showMessage('Ошибка при постановке лайка', 'error');
        });
    });
});
});
