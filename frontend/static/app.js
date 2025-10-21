/**
 * TFS-Confluence Automation Frontend JavaScript
 * Chat Interface with Service Status Monitoring
 */

class TFSConfluenceApp {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.projects = [];
        this.recentActivity = [];
        this.serviceStatus = {};
        
        this.init();
    }

    async init() {
        console.log('Initializing TFS-Confluence Automation App...');
        
        // Load projects
        await this.loadProjects();
        
        // Check service status
        await this.checkServiceStatus();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load recent activity
        this.loadRecentActivity();
        
        // Start periodic service status updates
        this.startServiceStatusUpdates();
        
        console.log('App initialized successfully');
    }

    setupEventListeners() {
        // Chat form
        const chatForm = document.getElementById('chatForm');
        chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        
        // Chat input enter key
        const chatInput = document.getElementById('chatInput');
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    async loadProjects() {
        // Временно отключаем загрузку проектов TFS
        // try {
        //     console.log('Loading TFS projects...');
        //     const response = await fetch(`${this.apiBaseUrl}/tfs/projects`);
        //     const data = await response.json();
        //     
        //     if (data.success && data.projects) {
        //         this.projects = data.projects;
        //         console.log(`Loaded ${this.projects.length} projects`);
        //     } else {
        //         console.error('Failed to load projects:', data.error);
        //     }
        // } catch (error) {
        //     console.error('Error loading projects:', error);
        // }
        
        // Временно отключаем
        this.projects = [];
        console.log('TFS projects loading disabled');
    }

    async checkServiceStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/status`);
            const data = await response.json();
            
            this.serviceStatus = data.services || {};
            this.updateServiceStatusDisplay();
            
        } catch (error) {
            console.error('Error checking service status:', error);
            this.serviceStatus = {};
            this.updateServiceStatusDisplay();
        }
    }

    updateServiceStatusDisplay() {
        const container = document.getElementById('serviceStatus');
        
        if (!container) {
            console.warn('Service status container not found');
            return;
        }
        
        if (!this.serviceStatus || Object.keys(this.serviceStatus).length === 0) {
            container.innerHTML = `
                <div class="d-flex align-items-center mb-2">
                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                    <span>Проверка сервисов...</span>
                </div>
            `;
            return;
        }
        
        let html = '';
        Object.entries(this.serviceStatus).forEach(([serviceName, serviceInfo]) => {
            const isAvailable = serviceInfo.available;
            const statusIcon = isAvailable ? 'check-circle text-success' : 'times-circle text-danger';
            const statusText = isAvailable ? 'Доступен' : 'Недоступен';
            const statusClass = isAvailable ? 'text-success' : 'text-danger';
            
            html += `
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-${statusIcon} me-2"></i>
                        <div>
                            <div class="fw-bold">${serviceInfo.name}</div>
                            <small class="text-muted">${serviceInfo.description}</small>
                        </div>
                    </div>
                    <span class="badge ${isAvailable ? 'bg-success' : 'bg-danger'}">${statusText}</span>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    startServiceStatusUpdates() {
        // Service status is now checked only at startup and before processing requests
        // No more periodic updates to reduce server load
        console.log('Service status updates disabled - checking only on startup and request processing');
        // Никаких периодических проверок не проводим
    }

    async handleChatSubmit(event) {
        event.preventDefault();
        
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();
        
        if (!message) {
            return;
        }
        
        // Check service status before processing request
        await this.checkServiceStatus();
        
        // Clear input
        chatInput.value = '';
        
        // Add user message to chat
        this.addMessageToChat(message, 'user');
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Determine which API to call based on message content
            let response;
            const lowerMessage = message.toLowerCase();
            
            console.log('Processing message:', message);
            console.log('Lower message:', lowerMessage);
            
            // First check for change chain keywords (higher priority)
            if (lowerMessage.includes('цепочку') || lowerMessage.includes('связанных тикетов') || lowerMessage.includes('связанных') || lowerMessage.includes('цепочка')) {
                console.log('Routing to change chain service');
                response = await this.sendChangeChainRequest(message);
            }
            // Then check for checklist keywords
            else if (lowerMessage.includes('чек-лист') || lowerMessage.includes('бдк')) {
                console.log('Routing to checklist service');
                response = await this.sendChecklistRequest(message);
            } 
            // Default to change chain for other requests
            else {
                console.log('Routing to change chain service (default)');
                response = await this.sendChangeChainRequest(message);
            }
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add bot response
            this.addBotResponse(response);
            
            // Add to recent activity
            this.addToRecentActivity(message, response);
            
        } catch (error) {
            console.error('Chat request failed:', error);
            this.hideTypingIndicator();
            this.addMessageToChat(`Ошибка: ${error.message}`, 'error');
        }
    }

    async sendChangeChainRequest(message) {
        const response = await fetch(`${this.apiBaseUrl}/change-chain-chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        return await response.json();
    }

    async sendChecklistRequest(message) {
        const response = await fetch(`${this.apiBaseUrl}/checklist-chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        return await response.json();
    }

    addMessageToChat(message, type = 'user') {
        const chatMessages = document.getElementById('chatMessages');
        
        if (!chatMessages) {
            console.warn('Chat messages container not found');
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = message;
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    addBotResponse(response) {
        const chatMessages = document.getElementById('chatMessages');
        
        if (!chatMessages) {
            console.warn('Chat messages container not found');
            return;
        }
        
        const messageDiv = document.createElement('div');
        
        if (response.success) {
            messageDiv.className = 'message success-message';
            
            let content = '';
            if (response.needs_confirmation) {
                // User Story preview response
                content = this.formatUserStoryPreview(response);
            } else if (response.created_stories) {
                // User Story creation response
                content = this.formatUserStoryCreationResponse(response);
            } else if (response.data && !response.created_stories) {
                // Change chain response
                content = this.formatChangeChainResponse(response);
            } else if (response.checklist) {
                // Checklist response
                content = this.formatChecklistResponse(response);
            } else {
                content = response.message || 'Операция выполнена успешно';
            }
            
            messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
        } else {
            messageDiv.className = 'message error-message';
            messageDiv.innerHTML = `<div class="message-content">${response.message || response.error || 'Произошла ошибка'}</div>`;
        }
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    formatUserStoryPreview(response) {
        const message = response.message || 'Требуется подтверждение';
        
        // Если есть данные preview, форматируем их
        const preview = response.data?.preview || response.preview;
        if (preview) {
            let content = `
                <div class="mb-3">
                    <i class="fas fa-eye text-info me-2"></i>
                    <strong>Найдено ${preview.user_stories_count} User Stories для создания</strong>
                </div>
                <div class="mb-3 p-2 bg-info bg-opacity-10 rounded">
                    <i class="fas fa-map-marker-alt text-info me-2"></i>
                    <strong>Пространство создания:</strong><br>
                    <span class="text-muted">Команда:</span> <code>${preview.team || 'Foxtrot'}</code><br>
                    <span class="text-muted">Область:</span> <code>${preview.area_path || 'Houston\\Foxtrot'}</code><br>
                    <span class="text-muted">Итерация:</span> <code>${preview.iteration_path || 'Houston\\Foxtrot'}</code><br>
                    <span class="text-muted">Родительский тикет:</span> <code>${preview.parent_ticket || 'Не указан'}</code><br>
                    <span class="text-muted">Ссылка на Wiki:</span> <a href="${preview.wiki_link || preview.confluence_url || '#'}" target="_blank" class="text-decoration-none"><i class="fas fa-external-link-alt me-1"></i>Открыть статью</a>
                </div>
            `;
            
            if (preview.user_stories && preview.user_stories.length > 0) {
                preview.user_stories.forEach((us, index) => {
                    content += `
                        <div class="mb-4 p-3 border rounded">
                            <h5 class="mb-3">${us.title}</h5>
                            <div class="mb-3">
                                ${this.formatUserStoryText(us.description)}
                            </div>
                            <div class="mb-3">
                                <strong>Критерии приёмки:</strong>
                                ${this.formatAcceptanceCriteria(us)}
                            </div>
                        </div>
                    `;
                });
            }
            
            content += `
                <div class="mt-4 p-3 bg-light rounded">
                    <strong>Для подтверждения создания отправьте:</strong> 'Да' или 'Создать'<br>
                    <strong>Для отмены отправьте:</strong> 'Нет' или 'Отмена'
                </div>
            `;
            
            return content;
        }
        
        // Fallback на обычное сообщение
        return message;
    }

    formatUserStoryCreationResponse(response) {
        const createdStories = response.created_stories || [];
        let content = `
            <div class="mb-3">
                <i class="fas fa-check-circle text-success me-2"></i>
                <strong>User Stories созданы успешно!</strong>
            </div>
        `;
        
        if (createdStories.length > 0) {
            content += `
                <div class="mb-3">
                    <strong>Создано User Stories:</strong>
                </div>
            `;
            
            createdStories.forEach((story, index) => {
                content += `
                    <div class="mb-2 p-2 border rounded">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <strong>${story.title}</strong>
                                <br><small class="text-muted">ID: ${story.id}</small>
                            </div>
                            <a href="${story.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-external-link-alt me-1"></i>Открыть
                            </a>
                        </div>
                    </div>
                `;
            });
        }
        
        if (response.parent_ticket) {
            content += `
                <div class="mt-3 p-2 bg-light rounded">
                    <small class="text-muted">
                        <i class="fas fa-link me-1"></i>
                        Родительский тикет: <strong>${response.parent_ticket}</strong>
                    </small>
                </div>
            `;
        }
        
        if (response.confluence_url) {
            content += `
                <div class="mt-2">
                    <a href="${response.confluence_url}" target="_blank" class="text-decoration-none">
                        <i class="fas fa-external-link-alt me-1"></i>Открыть статью Confluence
                    </a>
                </div>
            `;
        }
        
        return content;
    }

    formatUserStoryText(text) {
        if (!text) return '';
        
        // Сначала обрабатываем HTML теги и переносы строк
        let processedText = text
            .replace(/<br\s*\/?>/gi, '\n')  // Заменяем <br> на переносы строк
            .replace(/<\/p>/gi, '\n')       // Заменяем закрывающие </p> на переносы
            .replace(/<p[^>]*>/gi, '')      // Удаляем открывающие <p>
            .replace(/<[^>]*>/g, '')        // Удаляем остальные HTML теги
            .replace(/&nbsp;/g, ' ')        // Заменяем неразрывные пробелы
            .replace(/&lt;/g, '<')          // Декодируем HTML entities
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
        
        // Разделяем текст на части по ключевым словам
        const parts = processedText.split(/(я,?\s*как|хочу|чтобы)/i);
        let formatted = '';
        
        for (let i = 0; i < parts.length; i++) {
            const part = parts[i].trim();
            if (part.toLowerCase().match(/^я,?\s*как/i)) {
                formatted += `<div class="mb-2"><strong>${part}</strong>`;
            } else if (part.toLowerCase() === 'хочу') {
                formatted += ` <strong>${part}</strong>`;
            } else if (part.toLowerCase() === 'чтобы') {
                formatted += ` <strong>${part}</strong>`;
                if (i < parts.length - 1) {
                    formatted += ` ${parts[i + 1]}`;
                    i++; // Пропускаем следующий элемент, так как мы его уже обработали
                }
                formatted += `</div>`;
            } else if (part) {
                formatted += ` ${part}`;
            }
        }
        
        // Конвертируем переносы строк в HTML
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted || processedText;
    }

    formatAcceptanceCriteria(us) {
        // Проверяем, есть ли HTML таблица в acceptance_criteria
        if (us.acceptance_criteria && us.acceptance_criteria.length > 0) {
            const criteria = us.acceptance_criteria[0];
            
            // Проверяем, если это объект с HTML
            if (criteria && typeof criteria === 'object' && criteria.html) {
                return `
                    <div class="mt-2">
                        ${criteria.html}
                    </div>
                `;
            }
            
            // Проверяем, если это строка с HTML таблицей
            if (criteria && typeof criteria === 'string' && criteria.startsWith('<table')) {
                return `
                    <div class="mt-2">
                        ${criteria}
                    </div>
                `;
            }
            
            // Если это не HTML таблица, отображаем как обычный список
            return `
                <ul class="mt-2">
                    ${us.acceptance_criteria.map(criteria => `<li>${criteria}</li>`).join('')}
                </ul>
            `;
        }
        
        // Проверяем, есть ли структурированные данные Дано/Когда/Тогда
        if (us.given_conditions || us.when_actions || us.then_results) {
            return `
                <div class="mt-2">
                    <table class="table table-bordered table-sm" style="border-collapse: collapse;">
                        <thead class="table-light">
                            <tr>
                                <th style="width: 20%; border: 1px solid #000;">Дано</th>
                                <th style="width: 20%; border: 1px solid #000;">Когда</th>
                                <th style="width: 60%; border: 1px solid #000;">Тогда</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="border: 1px solid #000;">${us.given_conditions || ''}</td>
                                <td style="border: 1px solid #000;">${us.when_actions || ''}</td>
                                <td style="border: 1px solid #000;">${us.then_results || ''}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        
        return '<p class="text-muted mt-2">Критерии приемки не указаны</p>';
    }

    formatChangeChainResponse(response) {
        const data = response.data;
        let content = `
            <div class="mb-3">
                <i class="fas fa-check-circle text-success me-2"></i>
                <strong>Цепочка изменений создана успешно!</strong>
            </div>
        `;
        
        if (data.Epic) {
            content += `
                <div class="mb-2">
                    <strong>Epic:</strong> 
                    <a href="${data.Epic.url}" target="_blank" class="work-item-link">#${data.Epic.id}</a>
                    <br><small class="text-muted">${data.Epic.title}</small>
                </div>
            `;
        }
        
        if (data.Feature) {
            content += `
                <div class="mb-2">
                    <strong>Feature:</strong> 
                    <a href="${data.Feature.url}" target="_blank" class="work-item-link">#${data.Feature.id}</a>
                    <br><small class="text-muted">${data.Feature.title}</small>
                </div>
            `;
        }
        
        if (data.BacklogItem) {
            content += `
                <div class="mb-2">
                    <strong>Product Backlog Item:</strong> 
                    <a href="${data.BacklogItem.url}" target="_blank" class="work-item-link">#${data.BacklogItem.id}</a>
                    <br><small class="text-muted">${data.BacklogItem.title}</small>
                    <br><small class="text-info">Связан с родительским элементом #${data.BacklogItem.parent}</small>
                </div>
            `;
        }
        
        return content;
    }

    formatChecklistResponse(response) {
        let content = `
            <div class="mb-3">
                <i class="fas fa-list-check text-success me-2"></i>
                <strong>Чек-лист БДК ЗЗЛ для элемента #${response.work_item_id}</strong>
            </div>
            <div class="checklist-content">
                <pre style="white-space: pre-wrap; font-family: inherit; background: #f8f9fa; padding: 1rem; border-radius: 0.25rem; border: 1px solid #dee2e6;">${response.checklist}</pre>
            </div>
        `;
        
        return content;
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-robot me-2"></i>
                Обрабатываю запрос
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    addToRecentActivity(message, response) {
        const lowerMessage = message.toLowerCase();
        let activityType = 'change-chain'; // default
        
        // Determine activity type using same logic as message processing
        if (lowerMessage.includes('цепочку') || lowerMessage.includes('связанных тикетов') || lowerMessage.includes('связанных') || lowerMessage.includes('цепочка')) {
            activityType = 'change-chain';
        } else if (lowerMessage.includes('чек-лист') || lowerMessage.includes('бдк')) {
            activityType = 'checklist';
        }
        
        const activity = {
            timestamp: new Date(),
            message: message,
            success: response.success,
            type: activityType
        };
        
        this.recentActivity.unshift(activity);
        
        // Keep only last 5 activities
        if (this.recentActivity.length > 5) {
            this.recentActivity = this.recentActivity.slice(0, 5);
        }
        
        this.updateRecentActivityDisplay();
        this.saveRecentActivity();
    }

    updateRecentActivityDisplay() {
        const container = document.getElementById('recentActivity');
        
        if (!container) {
            console.warn('Recent activity container not found');
            return;
        }
        
        if (this.recentActivity.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Нет недавних операций</p>';
            return;
        }
        
        let html = '';
        this.recentActivity.forEach(activity => {
            const timeAgo = this.getTimeAgo(activity.timestamp);
            const statusIcon = activity.success ? 'check-circle text-success' : 'times-circle text-danger';
            const typeIcon = activity.type === 'checklist' ? 'list-check' : 'link';
            
            html += `
                <div class="d-flex align-items-center mb-2">
                    <i class="fas fa-${statusIcon} me-2"></i>
                    <div class="flex-grow-1">
                        <div class="small">
                            <i class="fas fa-${typeIcon} me-1"></i>
                            ${activity.message.substring(0, 40)}${activity.message.length > 40 ? '...' : ''}
                        </div>
                        <small class="text-muted">${timeAgo}</small>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    getTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'только что';
        if (minutes < 60) return `${minutes} мин назад`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} ч назад`;
        
        const days = Math.floor(hours / 24);
        return `${days} дн назад`;
    }

    saveRecentActivity() {
        localStorage.setItem('tfsConfluenceRecentActivity', JSON.stringify(this.recentActivity));
    }

    loadRecentActivity() {
        const saved = localStorage.getItem('tfsConfluenceRecentActivity');
        if (saved) {
            try {
                this.recentActivity = JSON.parse(saved);
                this.updateRecentActivityDisplay();
            } catch (error) {
                console.error('Error loading recent activity:', error);
            }
        }
    }
}

// Global functions for quick actions
function showChangeChainExample() {
    const chatInput = document.getElementById('chatInput');
    chatInput.value = 'Создай цепочку связанных тикетов для ЗЗЛ #';
    chatInput.focus();
}

function showChecklistExample() {
    const chatInput = document.getElementById('chatInput');
    chatInput.value = 'Создай чек-лист БД для ЗЗЛ #';
    chatInput.focus();
}

function showUserStoryExample() {
    const chatInput = document.getElementById('chatInput');
    chatInput.value = 'Создай UserStory в TFS по статье TDD';
    chatInput.focus();
}

// Функция для открытия TFS тикета
function openTfsTicket(ticketId) {
    if (ticketId && ticketId.trim()) {
        // Получаем базовый URL TFS из настроек или используем значение по умолчанию
        const tfsBaseUrl = window.tfsConfluenceApp?.tfsBaseUrl || 'https://dev.azure.com/yourorganization';
        const project = window.tfsConfluenceApp?.project || 'yourproject';
        const ticketUrl = `${tfsBaseUrl}/${project}/_workitems/edit/${ticketId}`;
        window.open(ticketUrl, '_blank');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.tfsConfluenceApp = new TFSConfluenceApp();
});