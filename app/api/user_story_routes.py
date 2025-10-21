from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
import logging

from app.services.user_story_creator_service import user_story_creator_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-stories", tags=["User Stories"])

class CreateUserStoriesRequest(BaseModel):
    """Запрос на создание User Stories из Confluence"""
    confluence_url: HttpUrl = Field(..., description="URL страницы Confluence")
    user_confirmation: Optional[str] = Field(None, description="Подтверждение пользователя (Да/Нет)")

class UserStoryPreviewResponse(BaseModel):
    """Ответ с предварительным просмотром User Stories"""
    success: bool
    preview: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    error: Optional[str] = None

class UserStoryCreationResponse(BaseModel):
    """Ответ о создании User Stories"""
    success: bool
    created_stories: Optional[list] = None
    parent_ticket: Optional[str] = None
    confluence_url: Optional[str] = None
    preview: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/create-from-confluence", response_model=UserStoryCreationResponse)
async def create_user_stories_from_confluence(request: CreateUserStoriesRequest):
    """
    Создание User Stories на основе страницы Confluence
    
    Эта функция:
    1. Парсит страницу Confluence и извлекает User Stories
    2. Показывает предварительный просмотр (если user_confirmation не указан)
    3. Создает User Stories в TFS после подтверждения пользователя
    4. Создает связи с родительским тикетом
    5. Логирует результаты операции
    """
    try:
        logger.info(f"Запрос на создание User Stories из: {request.confluence_url}")
        
        # Вызов основного сервиса
        result = await user_story_creator_service.create_user_stories_from_confluence(
            confluence_url=str(request.confluence_url),
            user_confirmation=request.user_confirmation
        )
        
        if result["success"]:
            if result.get("needs_confirmation", False):
                # Возвращаем предварительный просмотр
                return UserStoryPreviewResponse(
                    success=True,
                    preview=result["preview"],
                    needs_confirmation=True
                )
            else:
                # Возвращаем результат создания
                return UserStoryCreationResponse(
                    success=True,
                    created_stories=result["created_stories"],
                    parent_ticket=result["parent_ticket"],
                    confluence_url=result["confluence_url"],
                    preview=result["preview"]
                )
        else:
            # Возвращаем ошибку
            return UserStoryCreationResponse(
                success=False,
                error=result["error"],
                preview=result.get("preview")
            )
            
    except Exception as e:
        logger.error(f"Ошибка в API создания User Stories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )

@router.get("/preview/{confluence_url:path}")
async def preview_user_stories(confluence_url: str):
    """
    Получение предварительного просмотра User Stories без создания
    
    Полезно для предварительного просмотра перед созданием
    """
    try:
        logger.info(f"Запрос предварительного просмотра для: {confluence_url}")
        
        result = await user_story_creator_service.create_user_stories_from_confluence(
            confluence_url=confluence_url,
            user_confirmation=None
        )
        
        if result["success"] and result.get("needs_confirmation", False):
            return UserStoryPreviewResponse(
                success=True,
                preview=result["preview"],
                needs_confirmation=True
            )
        else:
            return UserStoryPreviewResponse(
                success=False,
                error=result.get("error", "Не удалось получить предварительный просмотр")
            )
            
    except Exception as e:
        logger.error(f"Ошибка при получении предварительного просмотра: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении предварительного просмотра: {str(e)}"
        )

@router.post("/confirm-creation")
async def confirm_user_stories_creation(
    confluence_url: str,
    user_confirmation: str
):
    """
    Подтверждение создания User Stories после предварительного просмотра
    
    Args:
        confluence_url: URL страницы Confluence
        user_confirmation: Подтверждение пользователя ("Да"/"Нет")
    """
    try:
        logger.info(f"Подтверждение создания User Stories: {user_confirmation}")
        
        result = await user_story_creator_service.create_user_stories_from_confluence(
            confluence_url=confluence_url,
            user_confirmation=user_confirmation
        )
        
        if result["success"]:
            return UserStoryCreationResponse(
                success=True,
                created_stories=result["created_stories"],
                parent_ticket=result["parent_ticket"],
                confluence_url=result["confluence_url"],
                preview=result["preview"]
            )
        else:
            return UserStoryCreationResponse(
                success=False,
                error=result["error"],
                preview=result.get("preview")
            )
            
    except Exception as e:
        logger.error(f"Ошибка при подтверждении создания: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при подтверждении создания: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Проверка состояния сервиса User Stories"""
    return {
        "status": "healthy",
        "service": "User Story Creator",
        "version": "1.0.0"
    }
