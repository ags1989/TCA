import logging
import asyncio
from typing import Dict, Any
from app.services.openai_service import OpenAIService
from app.services.confluence_service import ConfluenceService
from app.services.tfs_service import TFSService
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Глобальные экземпляры сервисов
global_services: Dict[str, Any] = {}

async def initialize_extensions():
    """
    Инициализация всех расширений и сервисов системы
    """
    logger.info("🚀 Начинаем инициализацию расширений...")
    
    try:
        # 1. Инициализируем основные сервисы
        await _initialize_core_services()
        
        # 2. Тестируем подключения
        await _test_connections()
        
        # 3. Инициализируем расширения (если есть)
        await _initialize_extensions()
        
        # 4. Настраиваем логирование
        _configure_logging()
        
        logger.info("✅ Все расширения успешно инициализированы")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при инициализации: {e}")
        raise

async def _initialize_core_services():
    """Инициализация основных сервисов"""
    
    logger.info("🔧 Инициализация основных сервисов...")
    
    try:
        # OpenAI Service
        logger.info("- Инициализация OpenAI Service...")
        openai_service = OpenAIService()
        global_services["openai"] = openai_service
        logger.info("  ✅ OpenAI Service инициализирован")
        
        # Confluence Service
        logger.info("- Инициализация Confluence Service...")
        confluence_service = ConfluenceService()
        global_services["confluence"] = confluence_service
        logger.info("  ✅ Confluence Service инициализирован")
        
        # TFS Service
        logger.info("- Инициализация TFS Service...")
        tfs_service = TFSService()
        global_services["tfs"] = tfs_service
        logger.info("  ✅ TFS Service инициализирован")
        
        logger.info("🎯 Все основные сервисы инициализированы")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации основных сервисов: {e}")
        raise

async def _test_connections():
    """Тестирование подключений к внешним сервисам"""
    
    logger.info("🔍 Тестирование подключений...")
    
    connection_results = {}
    
    # Тест OpenAI - ЗАКОММЕНТИРОВАНО (токены не получены)
    # try:
    #     openai_service = global_services["openai"]
    #     openai_ok = await openai_service.test_connection()
    #     connection_results["openai"] = openai_ok
    #     logger.info(f"  OpenAI: {'✅' if openai_ok else '❌'}")
    # except Exception as e:
    #     logger.warning(f"  OpenAI: ❌ {e}")
    #     connection_results["openai"] = False
    
    # Временно отключаем OpenAI
    connection_results["openai"] = False
    logger.info("  OpenAI: ❌ (отключен - токены не получены)")
    
    # Тест Confluence
    try:
        confluence_service = global_services["confluence"]
        confluence_ok = confluence_service.test_connection()
        connection_results["confluence"] = confluence_ok
        logger.info(f"  Confluence: {'✅' if confluence_ok else '❌'}")
    except Exception as e:
        logger.warning(f"  Confluence: ❌ {e}")
        connection_results["confluence"] = False
    
    # Тест TFS
    try:
        tfs_service = global_services["tfs"]
        tfs_ok = tfs_service.test_connection()
        connection_results["tfs"] = tfs_ok
        logger.info(f"  TFS: {'✅' if tfs_ok else '❌'}")
    except Exception as e:
        logger.warning(f"  TFS: ❌ {e}")
        connection_results["tfs"] = False
    
    # Сохраняем результаты подключений
    global_services["connection_status"] = connection_results
    
    # Предупреждения о неработающих сервисах
    failed_services = [name for name, status in connection_results.items() if not status]
    if failed_services:
        logger.warning(f"⚠️ Некоторые сервисы недоступны: {', '.join(failed_services)}")
        logger.warning("Проверьте настройки API ключей и подключение к интернету")
    else:
        logger.info("🎉 Все внешние сервисы доступны")

async def _initialize_extensions():
    """Инициализация расширений системы (если будут добавлены)"""
    
    logger.info("🧩 Инициализация расширений...")
    
    try:
        # Здесь будет инициализация расширений когда они появятся
        # Например:
        # - GitHub интеграция
        # - Jira интеграция
        # - Генераторы документации
        # - Анализаторы данных
        
        # Пока что просто заглушка
        extensions_count = 0
        logger.info(f"📦 Загружено расширений: {extensions_count}")
        
        # Сохраняем информацию о расширениях
        global_services["extensions"] = {
            "loaded": extensions_count,
            "available": [],
            "failed": []
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации расширений: {e}")
        # Не прерываем работу, расширения не критичны
        global_services["extensions"] = {"loaded": 0, "available": [], "failed": [str(e)]}

def _configure_logging():
    """Настройка системы логирования"""
    
    # Настраиваем уровень логирования из настроек
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Настраиваем формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Если нет обработчиков, добавляем консольный
    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    logger.info(f"📝 Логирование настроено на уровень: {settings.LOG_LEVEL}")

def get_service(service_name: str):
    """
    Получение экземпляра сервиса по имени
    
    Args:
        service_name: Название сервиса ("openai", "confluence", "tfs")
        
    Returns:
        Экземпляр сервиса или None если не найден
    """
    return global_services.get(service_name)

def get_connection_status() -> Dict[str, bool]:
    """Получение статуса подключений к внешним сервисам"""
    return global_services.get("connection_status", {})

def get_system_info() -> Dict[str, Any]:
    """Получение информации о состоянии системы"""
    return {
        "services_loaded": len([k for k in global_services.keys() if k not in ["connection_status", "extensions"]]),
        "connections": get_connection_status(),
        "extensions": global_services.get("extensions", {}),
        "debug_mode": settings.DEBUG,
        "log_level": settings.LOG_LEVEL
    }

async def cleanup_extensions():
    """Очистка ресурсов при завершении работы"""
    
    logger.info("🧹 Очистка ресурсов...")
    
    try:
        # Здесь можно добавить очистку ресурсов сервисов
        # Например, закрытие соединений, очистка кэшей и т.д.
        
        global_services.clear()
        logger.info("✅ Ресурсы очищены")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке ресурсов: {e}")

# Вспомогательные функции для проверки доступности сервисов
def is_openai_available() -> bool:
    """Проверка доступности OpenAI"""
    return get_connection_status().get("openai", False)

def is_confluence_available() -> bool:
    """Проверка доступности Confluence"""
    return get_connection_status().get("confluence", False)

def is_tfs_available() -> bool:
    """Проверка доступности TFS"""
    return get_connection_status().get("tfs", False)

# Функции для получения сервисов с проверкой доступности
def get_openai_service():
    """Получение OpenAI сервиса с проверкой доступности"""
    if not is_openai_available():
        raise RuntimeError("OpenAI сервис недоступен. Проверьте API ключ и подключение.")
    return get_service("openai")

def get_confluence_service():
    """Получение Confluence сервиса с проверкой доступности"""
    if not is_confluence_available():
        raise RuntimeError("Confluence сервис недоступен. Проверьте настройки подключения.")
    return get_service("confluence")

def get_tfs_service():
    """Получение TFS сервиса с проверкой доступности"""
    if not is_tfs_available():
        raise RuntimeError("TFS сервис недоступен. Проверьте настройки подключения.")
    return get_service("tfs")