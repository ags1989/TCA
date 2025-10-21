import uvicorn
import logging
from app.core.logging_config import setup_logging
from app.config.settings import settings

# Настройка логирования
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file="logs/app.log"
)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("🚀 Запуск приложения TFS-Confluence Automation")
    logger.info(f"   🌐 Хост: 127.0.0.1")
    logger.info(f"   🔌 Порт: 8000")
    logger.info(f"   🔄 Режим перезагрузки: включен")
    
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="warning",  # Подавляем INFO сообщения uvicorn
        access_log=False,     # Отключаем логи доступа
        reload_dirs=[],       # Пустой список для минимизации отслеживания
        reload_excludes=["*.pyc", "*.pyo", "__pycache__", "*.log", "logs/*", "venv/*", ".git/*"]
    )
