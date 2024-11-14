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

window.MathJax = {
    tex: {
        inlineMath: [['$', '$']],
        displayMath: [['$$', '$$']],
        packages: {'[+]': ['ams', 'newcommand', 'noerrors', 'noundefined']},
        tags: 'ams',
        processEnvironments: true,
        processRefs: true,
        macros: {
            matrix: ['{\\begin{pmatrix}#1\\end{pmatrix}}', 1],
            vector: ['{\\begin{pmatrix}#1\\end{pmatrix}}', 1]
        }
    },
    options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
        processHtmlClass: 'math-tex'
    },
    loader: {
        load: ['[tex]/ams', '[tex]/newcommand', '[tex]/noerrors', '[tex]/noundefined']
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
    console.error('Error:', message);
    alert(message);
};

// Функции для работы с темой
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) {
        console.error('Theme toggle button not found');
        return;
    }

    // Определяем предпочтительную системную тему
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');
    
    applyTheme(savedTheme);
    setupThemeListeners(themeToggle);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    console.log(`Applied theme: ${theme}`);
}

function setupThemeListeners(themeToggle) {
    // Слушатель для кнопки переключения
    themeToggle.addEventListener('click', toggleTheme);
    
    // Слушатель для системных изменений темы
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
}

function toggleTheme() {
    try {
        const root = document.documentElement;
        const currentTheme = root.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        console.log(`Switching theme from ${currentTheme} to ${newTheme}`);
        
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        
        animateThemeToggle();
    } catch (error) {
        console.error('Error switching theme:', error);
        showError('Failed to switch theme');
    }
}

function animateThemeToggle() {
    const button = document.getElementById('themeToggle');
    if (button) {
        button.style.transform = 'scale(0.9)';
        setTimeout(() => button.style.transform = 'scale(1)', 200);
    }
}

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
    if (!categoriesList) {
        console.error('Categories list element not found');
        return;
    }

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
    
    if (!createSelect || !filterSelect) {
        console.error('Category select elements not found');
        return;
    }
    
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
    
    if (!nameInput || !descInput) {
        showError('Category form elements not found');
        return;
    }

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
        const frontInput = document.getElementById('frontInput');
        const backInput = document.getElementById('backInput');
        const categorySelect = document.getElementById('categorySelect');

        if (!frontInput || !backInput || !categorySelect) {
            throw new Error('Card form elements not found');
        }

        const frontContent = frontInput.value.trim();
        const backContent = backInput.value.trim();
        const categoryId = categorySelect.value;

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
        frontInput.value = '';
        backInput.value = '';

        // Обновляем список категорий и показываем новую карточку
        await loadCategories();
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
        if (!cardElement) {
            throw new Error('Card element not found');
        }

        // Сброс анимации
        cardElement.style.animation = 'none';
        cardElement.offsetHeight; // Trigger reflow

        const categoryId = document.getElementById('filterCategory')?.value;
        const url = categoryId ? 
            `/api/categories/${categoryId}/cards/random` : 
            '/api/cards/random';
        
        const response = await fetch(url);
        
        if (!response.ok) {
            if (response.status === 404) {
                currentCard = null;
                const frontContent = document.getElementById('frontContent');
                const backContent = document.getElementById('backContent');
                
                if (frontContent && backContent) {
                    frontContent.innerHTML = '<p class="empty-state">No cards available in this category.<br>Add some cards first!</p>';
                    backContent.innerHTML = '';
                }
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

        await loadCategories();
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

async function renderCard() {
    if (!currentCard) return;

    const frontContent = document.getElementById('frontContent');
    const backContent = document.getElementById('backContent');
    
    if (!frontContent || !backContent) {
        console.error('Card content elements not found');
        return;
    }

    try {
        // Защищаем LaTeX выражения и обрабатываем переносы строк в матрицах
        const protectTeX = (text) => {
            return text.replace(/(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)/g, (match) => {
                // Сохраняем переносы строк в матрицах
                const preserved = match.replace(/\\\\/g, '\\newline');
                return `<span class="math-tex">${preserved}</span>`;
            });
        };

        // Рендерим с защитой LaTeX
        const frontHtml = marked.parse(protectTeX(currentCard.front));
        const backHtml = marked.parse(protectTeX(currentCard.back));
        
        frontContent.innerHTML = frontHtml;
        backContent.innerHTML = backHtml;
        
        // Очищаем предыдущий рендеринг MathJax
        const mathElements = [...frontContent.getElementsByClassName('math-tex'), 
                            ...backContent.getElementsByClassName('math-tex')];
        mathElements.forEach(el => MathJax.typesetClear([el]));
        
        // Запускаем MathJax с обновленной конфигурацией
        await MathJax.typesetPromise([frontContent, backContent]);

    } catch (error) {
        console.error('Error rendering card:', error);
        frontContent.innerHTML = '<p class="error">Error rendering content</p>';
        backContent.innerHTML = '<p class="error">Error rendering content</p>';
    }
}

function flipCard(cardElement) {
    if (!currentCard || isLoading || !cardElement) return;
    cardElement.classList.toggle('flipped');
}

// Обработка клавиатурных сокращений
document.addEventListener('keydown', (event) => {
    if (isLoading) return;

    if (event.target.matches('textarea')) return;

    switch(event.key) {
        case ' ':  // Space
        case 'Enter':
            event.preventDefault();
            const card = document.querySelector('.card');
            if (card) flipCard(card);
            break;
            
        case 'ArrowRight':
        case 'n':
            event.preventDefault();
            nextCard();
            break;
            
        case 'Delete':
            event.preventDefault();
            deleteCurrentCard();
            break;
    }
});

// Предотвращаем случайное закрытие страницы при редактировании
window.addEventListener('beforeunload', (event) => {
    const frontInput = document.getElementById('frontInput');
    const backInput = document.getElementById('backInput');
    const categoryName = document.getElementById('categoryName');
    
    if (frontInput?.value.trim() || backInput?.value.trim() || categoryName?.value.trim()) {
        event.preventDefault();
        event.returnValue = '';
    }
});

// Инициализация приложения
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Инициализация темы
        initTheme();
        
        // Настройка marked
        marked.setOptions({
            gfm: true,
            breaks: true,
            sanitize: false,
            smartLists: true,
            smartypants: true,
            pedantic: false,
            mangle: false,
            headerIds: false
        });

        // Ждем загрузки MathJax
        await MathJax.startup.promise;
        
        // Загружаем категории и первую карточку
        await loadCategories();
        await nextCard();
        
        console.log('Application initialized successfully');
    } catch (error) {
        console.error('Error initializing application:', error);
        showError('Failed to initialize application');
    }
});