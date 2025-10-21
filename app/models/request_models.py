from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class ActionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed" 
    PARTIAL = "partial"
    SKIPPED = "skipped"

class ExecutionStep(BaseModel):
    """Модель для отслеживания каждого шага выполнения"""
    step_name: str
    status: ActionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    details: Optional[str] = None
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}

class ConfluenceArticle(BaseModel):
    """Модель статьи Confluence"""
    id: str
    title: str
    content: str
    space_key: str
    url: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None

class UserStoryData(BaseModel):
    """Модель данных для создания User Story"""
    title: str
    description: Optional[str] = None
    project: str
    product: Optional[str] = None
    parent_work_item_id: Optional[int] = None
    
    # Команда
    assigned_to: Optional[str] = None
    tech_lead: Optional[str] = None
    developers: Optional[List[str]] = []
    so_owner: Optional[str] = None
    
    # User Story структура
    user_story_format: Optional[str] = None
    user_story_text: Optional[str] = None
    given_conditions: Optional[str] = None
    when_actions: Optional[str] = None
    then_results: Optional[str] = None
    
    # Критерии приемки и реализация
    acceptance_criteria: Optional[List[Union[str, Dict[str, str]]]] = []
    implementation_objects: Optional[List[str]] = []
    
    # Метаданные
    story_points: Optional[int] = 5
    priority: int = 2
    tags: Optional[List[str]] = []

class TaskData(BaseModel):
    """Модель данных для создания Task"""
    title: str
    description: Optional[str] = None
    project: str
    parent_work_item_id: Optional[int] = None
    assigned_to: Optional[str] = None
    priority: int = 2
    tags: Optional[List[str]] = []
    estimated_hours: Optional[int] = None

class UserRequest(BaseModel):
    """Модель запроса пользователя"""
    query: str = Field(..., description="Текст запроса пользователя")
    request_type: str = Field(..., description="Тип запроса")
    project_name: Optional[str] = Field(None, description="Название проекта")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Дополнительные параметры")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )