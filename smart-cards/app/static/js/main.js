// main.js

// Глобальные переменные
let currentCard = null;
let isLoading = false;

// Массив доступных анимаций
const animations = [
    'slideFromRight',
    'slideFromLeft',
    'fadeIn',
    'zoomIn',
    'slideFromTop'
];

// Конфигурация MathJax
window.MathJax = {
    tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        processEscapes: true,
        processEnvironments: true
    },
    options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
    }
};

// Функция для получения случайной анимации
function getRandomAnimation() {
    const index = Math.floor(Math.random() * animations.length);
    return animations[index];
}

// Утилиты
const showLoading = () => {
    isLoading = true;
    document.body.style.cursor = 'wait';
};

const hideLoading = () => {
    isLoading = false;
    document.body.style.cursor = 'default';
};

const showError = (message) => {
    alert(message);
};

// Функции для работы с карточками
async function addCard() {
    if (isLoading) return;

    try {
        const frontContent = document.getElementById('frontInput').value.trim();
        const backContent = document.getElementById('backInput').value.trim();

        // Валидация
        if (!frontContent || !backContent) {
            showError('Both front and back content are required');
            return;
        }

        showLoading();

        const response = await fetch('/api/cards/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                front: frontContent,
                back: backContent
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to add card');
        }

        // Очищаем форму
        document.getElementById('frontInput').value = '';
        document.getElementById('backInput').value = '';

        // Показываем новую карточку
        await nextCard();
        
    } catch (error) {
        console.error('Error adding card:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
}

async function nextCard() {
    if (isLoading) return;

    try {
        showLoading();

        const cardElement = document.querySelector('.card');
        
        // Удаляем предыдущую анимацию
        cardElement.style.animation = 'none';
        cardElement.offsetHeight; // trigger reflow
        
        const response = await fetch('/api/cards/random');
        
        if (!response.ok) {
            if (response.status === 404) {
                currentCard = null;
                document.getElementById('frontContent').innerHTML = 
                    '<p class="empty-state">No cards available.<br>Add some cards first!</p>';
                document.getElementById('backContent').innerHTML = '';
                return;
            }
            throw new Error('Failed to fetch card');
        }

        currentCard = await response.json();
        
        // Добавляем новую случайную анимацию
        const animation = getRandomAnimation();
        cardElement.style.animation = `${animation} 0.5s ease-out`;
        
        renderCard();
        
        // Сбрасываем состояние переворота
        cardElement.classList.remove('flipped');

    } catch (error) {
        console.error('Error fetching card:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
}

async function deleteCurrentCard() {
    if (!currentCard || isLoading) return;

    if (!confirm('Are you sure you want to delete this card?')) {
        return;
    }

    try {
        showLoading();

        const response = await fetch(`/api/cards/${currentCard.id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to delete card');
        }

        await nextCard();

    } catch (error) {
        console.error('Error deleting card:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function renderCard() {
    if (!currentCard) return;

    const frontContent = document.getElementById('frontContent');
    const backContent = document.getElementById('backContent');
    
    try {
        // Рендерим markdown
        frontContent.innerHTML = marked.parse(currentCard.front);
        backContent.innerHTML = marked.parse(currentCard.back);
        
        // Рендерим формулы
        MathJax.typesetPromise([frontContent, backContent]).catch(err => {
            console.error('MathJax error:', err);
        });

    } catch (error) {
        console.error('Error rendering card:', error);
        frontContent.innerHTML = '<p class="error">Error rendering content</p>';
        backContent.innerHTML = '<p class="error">Error rendering content</p>';
    }
}

function flipCard(cardElement) {
    if (!currentCard || isLoading) return;
    cardElement.classList.toggle('flipped');
}

// Keyboard shortcuts
document.addEventListener('keydown', (event) => {
    if (isLoading) return;

    switch(event.key) {
        case ' ':  // Space
        case 'Enter':
            if (!event.target.matches('textarea')) {
                event.preventDefault();
                document.querySelector('.card').classList.toggle('flipped');
            }
            break;
        case 'ArrowRight':
        case 'n':
            if (!event.target.matches('textarea')) {
                event.preventDefault();
                nextCard();
            }
            break;
        case 'Delete':
            if (!event.target.matches('textarea')) {
                event.preventDefault();
                deleteCurrentCard();
            }
            break;
    }
});

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Настраиваем marked для безопасного рендеринга markdown
    marked.setOptions({
        gfm: true,
        breaks: true,
        sanitize: false,
        smartLists: true,
        smartypants: true
    });

    // Загружаем первую карточку
    nextCard();
});

// Предотвращаем случайное закрытие страницы при редактировании
window.addEventListener('beforeunload', (event) => {
    const frontInput = document.getElementById('frontInput');
    const backInput = document.getElementById('backInput');
    
    if (frontInput.value.trim() || backInput.value.trim()) {
        event.preventDefault();
        event.returnValue = '';
    }
});