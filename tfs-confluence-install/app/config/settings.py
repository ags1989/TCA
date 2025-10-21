from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API ключи
    OPENAI_API_KEY: str = ""
    CONFLUENCE_TOKEN: str = ""  
    TFS_TOKEN: str = ""  
    TFS_PAT: str = ""  # Alias for TFS_TOKEN
    TFS_PAT_TOKEN: str = ""  # Alternative name from env.example
    GITHUB_TOKEN: str = ""  # GitHub Personal Access Token
    
    # URL сервисов
    CONFLUENCE_URL: str = "https://yourcompany.atlassian.net/wiki"
    TFS_URL: str = "https://dev.azure.com/yourorganization"
    
    # Confluence настройки
    CONFLUENCE_USER: str = ""  # email пользователя
    CONFLUENCE_USERNAME: str = ""  # Alias for CONFLUENCE_USER
    CONFLUENCE_SPACE: Optional[str] = None  
    
    # TFS настройки  
    TFS_PROJECT: str = ""  
    TFS_ORGANIZATION: str = ""
    TFS_DEFAULT_PROJECT: Optional[str] = None
    
    # Настройки приложения
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    MAX_SEARCH_RESULTS: int = 10
    
    # OpenAI настройки
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 1000
    
    # Настройки для работы с Work Items
    work_item_types: Dict[str, str] = {
        "user_story": "User Story",
        "task": "Task",
        "bug": "Bug",
        "epic": "Epic",
        "feature": "Feature"
    }
    
    # Настройки для связывания задач
    link_types: Dict[str, str] = {
        "parent": "System.LinkTypes.Hierarchy-Reverse",
        "child": "System.LinkTypes.Hierarchy-Forward",
        "related": "System.LinkTypes.Related",
        "successor": "System.LinkTypes.Dependency-Forward",
        "predecessor": "System.LinkTypes.Dependency-Reverse"
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from environment

# Глобальный экземпляр настроек
settings = Settings()

# Backward compatibility aliases
tfs_settings = settings