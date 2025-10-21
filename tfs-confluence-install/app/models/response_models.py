from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from app.models.request_models import ActionStatus, ExecutionStep

class CreatedWorkItem(BaseModel):
    """Информация о созданном рабочем элементе в TFS"""
    id: int
    title: str
    work_item_type: str  # User Story, Task, Bug
    state: str
    assigned_to: Optional[str] = None
    url: str
    parent_id: Optional[int] = None
    child_ids: Optional[List[int]] = []
    created_date: datetime
    story_points: Optional[int] = None
    priority: int
    tags: List[str] = []

class ConfluenceArticleInfo(BaseModel):
    """Информация об обработанной статье Confluence"""
    id: str
    title: str
    url: str
    space_key: str
    content_length: int
    extracted_project: Optional[str] = None
    extracted_team: Optional[List[str]] = []
    parent_tfs_reference: Optional[int] = None

class ProcessingError(BaseModel):
    """Детальная информация об ошибке"""
    error_type: str
    error_code: Optional[str] = None
    error_message: str
    occurred_at: datetime
    step_name: str
    technical_details: Optional[str] = None
    suggestion: Optional[str] = None

class DetailedProcessingResult(BaseModel):
    """Расширенный результат обработки запроса"""
    success: bool
    request_id: str = Field(default_factory=lambda: f"req_{int(datetime.now().timestamp())}")
    
    # Общая информация
    user_query: str
    processing_start: datetime
    processing_end: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    
    # Пошаговое выполнение
    execution_steps: List[ExecutionStep] = []
    
    # Обработанные данные
    confluence_article: Optional[ConfluenceArticleInfo] = None
    extracted_keywords: Optional[str] = None
    
    # Созданные объекты в TFS
    created_work_items: List[CreatedWorkItem] = []
    created_relations: List[Dict[str, Any]] = []  # Связи между элементами
    
    # Ошибки и предупреждения
    errors: List[ProcessingError] = []
    warnings: List[str] = []
    
    # Итоговая сводка
    summary: str
    recommendations: List[str] = []
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
