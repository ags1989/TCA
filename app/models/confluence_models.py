from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ConfluencePageType(str, Enum):
    """Типы страниц Confluence"""
    PAGE = "page"
    BLOG_POST = "blogpost"
    COMMENT = "comment"

class ConfluenceRepresentation(str, Enum):
    """Форматы представления содержимого"""
    STORAGE = "storage"  # HTML формат
    WIKI = "wiki"        # Wiki markup
    ATLAS_DOC_FORMAT = "atlas_doc_format"  # Atlassian Document Format

class ConfluencePageRequest(BaseModel):
    """Запрос на создание страницы в Confluence"""
    
    # Обязательные поля
    title: str = Field(..., min_length=1, max_length=255, description="Заголовок страницы")
    content: str = Field(..., min_length=1, description="Содержимое страницы")
    space_key: str = Field(..., min_length=1, description="Ключ пространства")
    
    # Опциональные поля
    parent_id: Optional[str] = Field(None, description="ID родительской страницы")
    page_type: ConfluencePageType = Field(ConfluencePageType.PAGE, description="Тип страницы")
    representation: ConfluenceRepresentation = Field(ConfluenceRepresentation.STORAGE, description="Формат содержимого")
    
    # Поля для шаблонов
    template_id: Optional[str] = Field(None, description="ID шаблона для создания страницы")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Данные для заполнения шаблона")
    
    # Метаданные
    labels: Optional[List[str]] = Field(None, description="Метки страницы")
    restrictions: Optional[Dict[str, Any]] = Field(None, description="Ограничения доступа")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Документация по задаче 123456",
                "content": "<h1>Описание задачи</h1><p>Детальное описание...</p>",
                "space_key": "DEV",
                "parent_id": "123456789",
                "template_id": "template-123",
                "labels": ["documentation", "task-123456"],
                "template_data": {
                    "task_id": "123456",
                    "assignee": "john.doe@company.com",
                    "priority": "High"
                }
            }
        }

class ConfluencePageResponse(BaseModel):
    """Ответ при создании страницы в Confluence"""
    
    success: bool = Field(..., description="Успешность операции")
    page_id: Optional[str] = Field(None, description="ID созданной страницы")
    title: Optional[str] = Field(None, description="Заголовок страницы")
    url: Optional[str] = Field(None, description="URL страницы")
    space_key: Optional[str] = Field(None, description="Ключ пространства")
    version: Optional[int] = Field(None, description="Версия страницы")
    created_at: Optional[str] = Field(None, description="Дата создания")
    error: Optional[str] = Field(None, description="Сообщение об ошибке")

class ConfluenceTemplate(BaseModel):
    """Шаблон страницы Confluence"""
    
    id: str = Field(..., description="ID шаблона")
    name: str = Field(..., description="Название шаблона")
    description: Optional[str] = Field(None, description="Описание шаблона")
    space_key: str = Field(..., description="Ключ пространства шаблона")
    content: Optional[str] = Field(None, description="Содержимое шаблона")
    variables: Optional[List[str]] = Field(None, description="Переменные шаблона")

class ConfluenceSpace(BaseModel):
    """Пространство Confluence"""
    
    key: str = Field(..., description="Ключ пространства")
    name: str = Field(..., description="Название пространства")
    description: Optional[str] = Field(None, description="Описание пространства")
    url: Optional[str] = Field(None, description="URL пространства")

class ConfluencePageUpdateRequest(BaseModel):
    """Запрос на обновление страницы в Confluence"""
    
    page_id: str = Field(..., description="ID страницы для обновления")
    title: Optional[str] = Field(None, description="Новый заголовок")
    content: Optional[str] = Field(None, description="Новое содержимое")
    version: int = Field(..., description="Текущая версия страницы")
    representation: ConfluenceRepresentation = Field(ConfluenceRepresentation.STORAGE, description="Формат содержимого")
    minor_edit: bool = Field(False, description="Минорное редактирование")

class ConfluenceCommentRequest(BaseModel):
    """Запрос на добавление комментария к странице"""
    
    page_id: str = Field(..., description="ID страницы")
    comment: str = Field(..., min_length=1, description="Текст комментария")
    parent_id: Optional[str] = Field(None, description="ID родительского комментария")

class ConfluenceSearchRequest(BaseModel):
    """Запрос на поиск в Confluence"""
    
    query: str = Field(..., min_length=1, description="Поисковый запрос")
    space_key: Optional[str] = Field(None, description="Ключ пространства для поиска")
    content_type: Optional[str] = Field("page", description="Тип контента (page, blogpost, comment)")
    limit: int = Field(10, ge=1, le=100, description="Максимальное количество результатов")
    start: int = Field(0, ge=0, description="Начальная позиция для пагинации")
