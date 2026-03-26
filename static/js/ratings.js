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

const csrftoken = getCookie('csrftoken');

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.like-btn, .dislike-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const postId = this.getAttribute('data-post');
            const value = parseInt(this.getAttribute('data-value'));

            fetch('{% url "blog:rating" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
                },
                body: `post_id=${postId}&value=${value}`
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Обновляем счётчики для конкретного поста
                const postControls = document.querySelector(`.rating-controls[data-post-id="${postId}"]`);
                if (postControls) {
                    const likeCountEl = postControls.querySelector('.like-count');
                    const dislikeCountEl = postControls.querySelector('.dislike-count');
            const ratingValueEl = postControls.querySelector('.rating-value');

            if (likeCountEl) likeCountEl.textContent = data.likes;
            if (dislikeCountEl) dislikeCountEl.textContent = data.dislikes;
            if (ratingValueEl) ratingValueEl.textContent = data.rating_sum;
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке рейтинга:', error);
                alert('Произошла ошибка при оценке поста. Попробуйте ещё раз.');
            });
        });
    });
});
