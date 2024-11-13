// Глобальные переменные
let currentCard = null;
let isLoading = false;
let currentCategory = null;
let categories = [];

// Массив доступных анимаций
const animations = [
    'slideFromRight',
    'slideFromLeft',
    'fadeIn',
    'zoomIn',
    'slideFromTop'
];

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

// Функции для работы с категориями
async function loadCategories() {
    try {
        showLoading();
        const response = await fetch('/api/categories/');
        
        if (!response.ok) {
            throw new Error('Failed to fetch categories');
        }

        categories = await response.json();
        renderCategories();
        updateCategorySelects();
        
    } catch (error) {
        console.error('Error loading categories:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function renderCategories() {
    const categoriesList = document.getElementById('categoriesList');
    categoriesList.innerHTML = categories.map(category => `
        <div class="category-item">
            <div class="category-info">
                <h3>${category.name}</h3>
                <p>${category.description || ''}</p>
                <small>${category.cards_count} cards</small>
            </div>
        </div>
    `).join('');
}

function updateCategorySelects() {
    const createSelect = document.getElementById('categorySelect');
    const filterSelect = document.getElementById('filterCategory');
    
    const options = categories.map(category => 
        `<option value="${category.id}">${category.name} (${category.cards_count})</option>`
    );
    
    createSelect.innerHTML = '<option value="">Select category</option>' + options;
    filterSelect.innerHTML = '<option value="">All categories</option>' + options;
}

async function addCategory() {
    if (isLoading) return;

    const nameInput = document.getElementById('categoryName');
    const descInput = document.getElementById('categoryDescription');
    
    const name = nameInput.value.trim();
    const description = descInput.value.trim();

    if (!name) {
        showError('Category name is required');
        return;
    }

    try {
        showLoading();
        
        const response = await fetch('/api/categories/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, description }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to add category');
        }

        // Очищаем форму
        nameInput.value = '';
        descInput.value = '';

        // Обновляем список категорий
        await loadCategories();
        
    } catch (error) {
        console.error('Error adding category:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// Функции для работы с карточками
async function addCard() {
    if (isLoading) return;

    try {
        const frontContent = document.getElementById('frontInput').value.trim();
        const backContent = document.getElementById('backInput').value.trim();
        const categoryId = document.getElementById('categorySelect').value;

        // Валидация
        if (!frontContent || !backContent) {
            showError('Both front and back content are required');
            return;
        }

        if (!categoryId) {
            showError('Please select a category');
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
                back: backContent,
                category_id: parseInt(categoryId)
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to add card');
        }

        // Очищаем форму
        document.getElementById('frontInput').value = '';
        document.getElementById('backInput').value = '';

        // Обновляем список категорий для обновления счетчиков
        await loadCategories();
        
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
        cardElement.style.animation = 'none';
        cardElement.offsetHeight;

        const categoryId = document.getElementById('filterCategory').value;
        const url = categoryId ? 
            `/api/categories/${categoryId}/cards/random` : 
            '/api/cards/random';
        
        const response = await fetch(url);
        
        if (!response.ok) {
            if (response.status === 404) {
                currentCard = null;
                document.getElementById('frontContent').innerHTML = 
                    '<p class="empty-state">No cards available in this category.<br>Add some cards first!</p>';
                document.getElementById('backContent').innerHTML = '';
                return;
            }
            throw new Error('Failed to fetch card');
        }

        currentCard = await response.json();
        
        const animation = getRandomAnimation();
        cardElement.style.animation = `${animation} 0.5s ease-out`;
        
        renderCard();
        
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

        // Обновляем список категорий для обновления счетчиков
        await loadCategories();
        
        // Переходим к следующей карточке
        await nextCard();

    } catch (error) {
        console.error('Error deleting card:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
}

async function filterByCategory() {
    await nextCard();
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
document.addEventListener('DOMContentLoaded', async () => {
    // Настройка marked
    marked.setOptions({
        gfm: true,
        breaks: true,
        sanitize: false,
        smartLists: true,
        smartypants: true
    });

    // Загружаем категории и первую карточку
    await loadCategories();
    await nextCard();
});

// Предотвращаем случайное закрытие страницы при редактировании
window.addEventListener('beforeunload', (event) => {
    const frontInput = document.getElementById('frontInput');
    const backInput = document.getElementById('backInput');
    const categoryName = document.getElementById('categoryName');
    
    if (frontInput.value.trim() || backInput.value.trim() || categoryName.value.trim()) {
        event.preventDefault();
        event.returnValue = '';
    }
});