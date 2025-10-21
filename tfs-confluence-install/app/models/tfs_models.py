from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum


class WorkItemType(str, Enum):
    """Типы Work Items в TFS"""
    USER_STORY = "User Story"
    TASK = "Task"
    BUG = "Bug"
    EPIC = "Epic"
    FEATURE = "Feature"


class LinkType(str, Enum):
    """Типы связей между Work Items"""
    PARENT = "System.LinkTypes.Hierarchy-Reverse"
    CHILD = "System.LinkTypes.Hierarchy-Forward"
    RELATED = "System.LinkTypes.Related"
    SUCCESSOR = "System.LinkTypes.Dependency-Forward"
    PREDECESSOR = "System.LinkTypes.Dependency-Reverse"


class WorkItemState(str, Enum):
    """Состояния Work Items"""
    NEW = "New"
    ACTIVE = "Active"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REMOVED = "Removed"


class WorkItemPriority(str, Enum):
    """Приоритеты Work Items"""
    HIGH = "1"
    MEDIUM = "2"
    LOW = "3"


class RequestType(str, Enum):
    """Типы запросов пользователя"""
    CREATE_USER_STORY = "create_user_story"
    CREATE_TASK = "create_task"
    LINK_ITEMS = "link_items"
    SEARCH_ITEMS = "search_items"
    UPDATE_ITEM = "update_item"
    GET_PROJECTS = "get_projects"
    GET_ITEM_INFO = "get_item_info"


class ProjectInfo(BaseModel):
    """Информация о проекте"""
    id: str
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    state: Optional[str] = None


class WorkItemField(BaseModel):
    """Поле Work Item"""
    name: str
    value: Any


class WorkItemCreateRequest(BaseModel):
    """Запрос на создание Work Item"""
    work_item_type: WorkItemType
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[WorkItemPriority] = WorkItemPriority.MEDIUM
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class WorkItemUpdateRequest(BaseModel):
    """Запрос на обновление Work Item"""
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    state: Optional[WorkItemState] = None
    priority: Optional[WorkItemPriority] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class WorkItemLinkRequest(BaseModel):
    """Запрос на связывание Work Items"""
    source_work_item_id: int
    target_work_item_id: int
    link_type: LinkType
    comment: Optional[str] = None


class WorkItemInfo(BaseModel):
    """Информация о Work Item"""
    id: int
    work_item_type: str
    title: str
    state: str
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    created_date: Optional[str] = None
    changed_date: Optional[str] = None
    url: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None
    relations: Optional[List[Dict[str, Any]]] = None
    project: Optional[str] = None  # Добавляем поле проекта



class WorkItemResponse(BaseModel):
    """Ответ с информацией о Work Item"""
    success: bool
    work_item: Optional[WorkItemInfo] = None
    error: Optional[str] = None


class ProjectListResponse(BaseModel):
    """Ответ со списком проектов"""
    success: bool
    projects: Optional[List[ProjectInfo]] = None
    error: Optional[str] = None


class WorkItemListResponse(BaseModel):
    """Ответ со списком Work Items"""
    success: bool
    work_items: Optional[List[WorkItemInfo]] = None
    error: Optional[str] = None
    total_count: Optional[int] = None


class LinkResponse(BaseModel):
    """Ответ на операцию связывания"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class UserRequest(BaseModel):
    """Модель запроса пользователя с валидацией"""
    query: str = Field(..., description="Текст запроса пользователя")
    request_type: RequestType = Field(..., description="Тип запроса")
    project_name: Optional[str] = Field(None, description="Название проекта (если требуется)")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Дополнительные параметры")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Валидация поля query"""
        if not v or not v.strip():
            raise ValueError('Query не может быть пустым')
        
        if len(v) > 500:
            raise ValueError('Query не может быть длиннее 500 символов')
        
        return v.strip()
    
    @field_validator('request_type')
    @classmethod
    def validate_request_type(cls, v):
        """Валидация типа запроса"""
        if v not in RequestType:
            raise ValueError(f'Недопустимый тип запроса: {v}')
        return v
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "query": "Создать User Story для функции авторизации",
                "request_type": "create_user_story",
                "project_name": "MyProject",
                "additional_params": {
                    "priority": "high",
                    "assigned_to": "user@company.com"
                }
            }
        }
    )
