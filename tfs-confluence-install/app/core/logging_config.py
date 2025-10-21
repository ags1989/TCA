import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Настройка системы логирования для приложения
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов (по умолчанию logs/app.log)
    """
    
    # Создаем директорию для логов, если её нет
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = str(log_dir / "app.log")
    
    # Настройка форматирования
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 1. Консольный обработчик (все уровни)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # 2. Файловый обработчик (все уровни)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # 3. Обработчик для ошибок (только ERROR и CRITICAL)
    error_file = str(Path(log_file).parent / "errors.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # 4. Обработчик для аудита действий (только INFO с определенными тегами)
    audit_file = str(Path(log_file).parent / "audit.log")
    audit_handler = logging.handlers.RotatingFileHandler(
        audit_file,
        maxBytes=20*1024*1024,  # 20MB
        backupCount=10,
        encoding='utf-8'
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(detailed_formatter)
    
    # Создаем фильтр для аудита
    class AuditFilter(logging.Filter):
        def filter(self, record):
            # Логируем только сообщения с определенными тегами
            message = record.getMessage()
            audit_keywords = [
                "✅", "❌", "🔄", "📄", "🔗", "👤", "🏷️", "⭐", "📊", 
                "⏱️", "💼", "🎯", "🏢", "💬", "🚀", "📅", "🔍"
            ]
            return any(keyword in message for keyword in audit_keywords)
    
    audit_handler.addFilter(AuditFilter())
    root_logger.addHandler(audit_handler)
    
    # Настройка логгеров для внешних библиотек
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Подавляем служебные сообщения uvicorn (оставляем только access и error)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.asgi").setLevel(logging.WARNING)
    
    # Подавляем сообщения о изменениях файлов
    logging.getLogger("uvicorn.reload").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.reloaders").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.reloaders.watchfiles").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.reloaders.stat").setLevel(logging.CRITICAL)
    
    # Дополнительно подавляем все возможные источники сообщений о изменениях
    logging.getLogger("watchdog").setLevel(logging.CRITICAL)
    logging.getLogger("watchdog.observers").setLevel(logging.CRITICAL)
    logging.getLogger("watchdog.observers.polling").setLevel(logging.CRITICAL)
    logging.getLogger("watchdog.observers.inotify").setLevel(logging.CRITICAL)
    logging.getLogger("watchdog.observers.fsevents").setLevel(logging.CRITICAL)
    logging.getLogger("watchdog.observers.kqueue").setLevel(logging.CRITICAL)
    
    # Подавляем все uvicorn компоненты на CRITICAL уровень
    logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.server").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.lifespan").setLevel(logging.CRITICAL)
    
    # Создаем фильтр для полного подавления сообщений о изменениях файлов
    class ChangeDetectionFilter(logging.Filter):
        def filter(self, record):
            message = record.getMessage()
            # Подавляем сообщения о изменениях файлов
            if "change detected" in message.lower() or "file changed" in message.lower():
                return False
            return True
    
    # Применяем фильтр к root logger
    root_logger.addFilter(ChangeDetectionFilter())
    
    # Подавляем сообщения от FastAPI
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    # Логируем начало работы
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("🚀 Система логирования инициализирована")
    logger.info(f"   📁 Основной лог: {log_file}")
    logger.info(f"   📁 Лог ошибок: {error_file}")
    logger.info(f"   📁 Аудит действий: {audit_file}")
    logger.info(f"   📊 Уровень логирования: {log_level}")
    logger.info(f"   🕐 Время инициализации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

def get_audit_logger(name: str) -> logging.Logger:
    """
    Получение логгера для аудита действий
    
    Args:
        name: Имя логгера (обычно __name__)
    
    Returns:
        Logger настроенный для аудита
    """
    logger = logging.getLogger(f"audit.{name}")
    return logger

def log_user_action(logger: logging.Logger, action: str, details: dict = None):
    """
    Логирование действий пользователя
    
    Args:
        logger: Логгер для записи
        action: Описание действия
        details: Дополнительные детали
    """
    message = f"👤 Действие пользователя: {action}"
    if details:
        detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
        message += f" | {detail_str}"
    
    logger.info(message)

def log_system_action(logger: logging.Logger, action: str, details: dict = None):
    """
    Логирование системных действий
    
    Args:
        logger: Логгер для записи
        action: Описание действия
        details: Дополнительные детали
    """
    message = f"⚙️ Системное действие: {action}"
    if details:
        detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
        message += f" | {detail_str}"
    
    logger.info(message)

def log_api_request(logger: logging.Logger, method: str, endpoint: str, user_id: str = None, details: dict = None):
    """
    Логирование API запросов
    
    Args:
        logger: Логгер для записи
        method: HTTP метод
        endpoint: API endpoint
        user_id: ID пользователя (опционально)
        details: Дополнительные детали
    """
    message = f"🌐 API запрос: {method} {endpoint}"
    if user_id:
        message += f" | Пользователь: {user_id}"
    if details:
        detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
        message += f" | {detail_str}"
    
    logger.info(message)

def log_tfs_operation(logger: logging.Logger, operation: str, work_item_id: int = None, details: dict = None):
    """
    Логирование операций с TFS
    
    Args:
        logger: Логгер для записи
        operation: Описание операции
        work_item_id: ID рабочего элемента (опционально)
        details: Дополнительные детали
    """
    message = f"🔧 TFS операция: {operation}"
    if work_item_id:
        message += f" | ID: {work_item_id}"
    if details:
        detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
        message += f" | {detail_str}"
    
    logger.info(message)

def log_confluence_operation(logger: logging.Logger, operation: str, page_id: str = None, details: dict = None):
    """
    Логирование операций с Confluence
    
    Args:
        logger: Логгер для записи
        operation: Описание операции
        page_id: ID страницы (опционально)
        details: Дополнительные детали
    """
    message = f"📚 Confluence операция: {operation}"
    if page_id:
        message += f" | ID страницы: {page_id}"
    if details:
        detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
        message += f" | {detail_str}"
    
    logger.info(message)
