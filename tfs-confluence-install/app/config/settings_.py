from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API ключи
    OPENAI_API_KEY: str
    CONFLUENCE_TOKEN: str  
    TFS_TOKEN: str  
    
    # URL сервисов
    CONFLUENCE_URL: str  # https://yourcompany.atlassian.net/wiki
    TFS_URL: str  # https://dev.azure.com/yourorganization
    
    # Confluence настройки
    CONFLUENCE_USER: str  # email пользователя
    CONFLUENCE_SPACE: Optional[str] = None  
    
    # TFS настройки  
    TFS_PROJECT: str  
    TFS_ORGANIZATION: str  
    
    # Настройки приложения
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    MAX_SEARCH_RESULTS: int = 10
    
    # OpenAI настройки
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from environment

settings = Settings()
