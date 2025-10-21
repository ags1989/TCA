from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging
from datetime import datetime

from app.services.confluence_service import confluence_service
from app.models.confluence_models import (
    ConfluencePageRequest, ConfluencePageResponse, ConfluenceTemplate,
    ConfluenceSpace, ConfluencePageUpdateRequest, ConfluenceCommentRequest,
    ConfluenceSearchRequest
)
from app.core.logging_config import log_api_request, log_confluence_operation

router = APIRouter(prefix="/confluence", tags=["Confluence"])
logger = logging.getLogger(__name__)

@router.post("/pages", response_model=ConfluencePageResponse)
async def create_page(request: ConfluencePageRequest):
    """
    Создание новой страницы в Confluence
    
    Поддерживает:
    - Создание обычных страниц
    - Создание страниц на основе шаблонов
    - Добавление меток
    - Указание родительской страницы
    """
    try:
        logger.info(f"🌐 API запрос: POST /confluence/pages")
        log_api_request(
            logger=logger,
            method="POST",
            endpoint="/confluence/pages",
            details={
                "title": request.title,
                "space_key": request.space_key,
                "template_id": request.template_id,
                "has_parent": bool(request.parent_id)
            }
        )
        
        result = await confluence_service.create_page_from_request(request)
        
        if result.success:
            log_confluence_operation(
                logger=logger,
                operation="Страница создана через API",
                page_id=result.page_id,
                details={
                    "title": result.title,
                    "space_key": result.space_key,
                    "url": result.url,
                    "template_used": bool(request.template_id)
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании страницы через API: {str(e)}")
        return ConfluencePageResponse(
            success=False,
            error=f"Ошибка API: {str(e)}"
        )

@router.get("/pages", response_model=List[ConfluencePageResponse])
async def search_pages(
    query: str = Query(..., description="Поисковый запрос"),
    space_key: Optional[str] = Query(None, description="Ключ пространства"),
    content_type: str = Query("page", description="Тип контента"),
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество результатов"),
    start: int = Query(0, ge=0, description="Начальная позиция")
):
    """
    Поиск страниц в Confluence
    """
    try:
        logger.info(f"🌐 API запрос: GET /confluence/pages")
        log_api_request(
            logger=logger,
            method="GET",
            endpoint="/confluence/pages",
            details={
                "query": query,
                "space_key": space_key,
                "limit": limit
            }
        )
        
        search_request = ConfluenceSearchRequest(
            query=query,
            space_key=space_key,
            content_type=content_type,
            limit=limit,
            start=start
        )
        
        results = await confluence_service.search_pages(search_request)
        
        log_confluence_operation(
            logger=logger,
            operation="Поиск страниц через API",
            details={
                "query": query,
                "results_count": len(results),
                "space_key": space_key
            }
        )
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске страниц: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")

@router.get("/templates", response_model=List[ConfluenceTemplate])
async def get_templates(
    space_key: Optional[str] = Query(None, description="Ключ пространства для фильтрации")
):
    """
    Получение списка доступных шаблонов
    """
    try:
        logger.info(f"🌐 API запрос: GET /confluence/templates")
        log_api_request(
            logger=logger,
            method="GET",
            endpoint="/confluence/templates",
            details={"space_key": space_key}
        )
        
        templates = await confluence_service.get_templates(space_key)
        
        log_confluence_operation(
            logger=logger,
            operation="Получение шаблонов через API",
            details={
                "templates_count": len(templates),
                "space_key": space_key
            }
        )
        
        return templates
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении шаблонов: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения шаблонов: {str(e)}")

@router.get("/templates/{template_id}", response_model=ConfluenceTemplate)
async def get_template(template_id: str):
    """
    Получение конкретного шаблона по ID
    """
    try:
        logger.info(f"🌐 API запрос: GET /confluence/templates/{template_id}")
        log_api_request(
            logger=logger,
            method="GET",
            endpoint=f"/confluence/templates/{template_id}",
            details={"template_id": template_id}
        )
        
        template = await confluence_service.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
        
        log_confluence_operation(
            logger=logger,
            operation="Получение шаблона через API",
            page_id=template_id,
            details={
                "template_name": template.name,
                "space_key": template.space_key
            }
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при получении шаблона {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения шаблона: {str(e)}")

@router.get("/spaces", response_model=List[ConfluenceSpace])
async def get_spaces():
    """
    Получение списка пространств Confluence
    """
    try:
        logger.info(f"🌐 API запрос: GET /confluence/spaces")
        log_api_request(
            logger=logger,
            method="GET",
            endpoint="/confluence/spaces"
        )
        
        spaces = await confluence_service.get_spaces()
        
        log_confluence_operation(
            logger=logger,
            operation="Получение пространств через API",
            details={"spaces_count": len(spaces)}
        )
        
        return spaces
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении пространств: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения пространств: {str(e)}")

@router.put("/pages/{page_id}", response_model=ConfluencePageResponse)
async def update_page(page_id: str, request: ConfluencePageUpdateRequest):
    """
    Обновление существующей страницы
    """
    try:
        logger.info(f"🌐 API запрос: PUT /confluence/pages/{page_id}")
        log_api_request(
            logger=logger,
            method="PUT",
            endpoint=f"/confluence/pages/{page_id}",
            details={
                "page_id": page_id,
                "title": request.title,
                "version": request.version
            }
        )
        
        result = await confluence_service.update_page(
            page_id=page_id,
            title=request.title,
            content=request.content
        )
        
        log_confluence_operation(
            logger=logger,
            operation="Страница обновлена через API",
            page_id=page_id,
            details={
                "title": request.title,
                "version": request.version
            }
        )
        
        return ConfluencePageResponse(
            success=True,
            page_id=result["id"],
            title=result["title"],
            url=result["url"],
            space_key=result.get("space_key"),
            version=result["version"],
            created_at=result["updated_at"]
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении страницы {page_id}: {str(e)}")
        return ConfluencePageResponse(
            success=False,
            error=f"Ошибка обновления: {str(e)}"
        )

@router.post("/pages/{page_id}/comments", response_model=dict)
async def add_comment(page_id: str, request: ConfluenceCommentRequest):
    """
    Добавление комментария к странице
    """
    try:
        logger.info(f"🌐 API запрос: POST /confluence/pages/{page_id}/comments")
        log_api_request(
            logger=logger,
            method="POST",
            endpoint=f"/confluence/pages/{page_id}/comments",
            details={
                "page_id": page_id,
                "comment_length": len(request.comment)
            }
        )
        
        result = await confluence_service.add_comment(
            page_id=page_id,
            comment=request.comment
        )
        
        log_confluence_operation(
            logger=logger,
            operation="Комментарий добавлен через API",
            page_id=page_id,
            details={
                "comment_id": result["id"],
                "comment_length": len(request.comment)
            }
        )
        
        return {
            "success": True,
            "comment_id": result["id"],
            "page_id": page_id,
            "created_at": result["created_at"]
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении комментария к странице {page_id}: {str(e)}")
        return {
            "success": False,
            "error": f"Ошибка добавления комментария: {str(e)}"
        }

@router.get("/pages/{page_id}", response_model=ConfluencePageResponse)
async def get_page(page_id: str):
    """
    Получение конкретной страницы по ID
    """
    try:
        logger.info(f"🌐 API запрос: GET /confluence/pages/{page_id}")
        log_api_request(
            logger=logger,
            method="GET",
            endpoint=f"/confluence/pages/{page_id}",
            details={"page_id": page_id}
        )
        
        article = await confluence_service.get_article_by_id(page_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="Страница не найдена")
        
        log_confluence_operation(
            logger=logger,
            operation="Страница получена через API",
            page_id=page_id,
            details={
                "title": article.title,
                "space_key": article.space_key
            }
        )
        
        return article
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при получении страницы {page_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения страницы: {str(e)}")

@router.post("/pages/quick-create", response_model=ConfluencePageResponse)
async def quick_create_page(
    title: str,
    content: str,
    space_key: str = "DEV",
    parent_id: Optional[str] = None,
    labels: Optional[List[str]] = None
):
    """
    Быстрое создание страницы с минимальными параметрами
    """
    try:
        logger.info(f"🌐 API запрос: POST /confluence/pages/quick-create")
        log_api_request(
            logger=logger,
            method="POST",
            endpoint="/confluence/pages/quick-create",
            details={
                "title": title,
                "space_key": space_key,
                "has_parent": bool(parent_id),
                "labels_count": len(labels) if labels else 0
            }
        )
        
        request = ConfluencePageRequest(
            title=title,
            content=content,
            space_key=space_key,
            parent_id=parent_id,
            labels=labels or []
        )
        
        result = await confluence_service.create_page_from_request(request)
        
        log_confluence_operation(
            logger=logger,
            operation="Быстрое создание страницы через API",
            page_id=result.page_id,
            details={
                "title": result.title,
                "space_key": result.space_key,
                "url": result.url
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при быстром создании страницы: {str(e)}")
        return ConfluencePageResponse(
            success=False,
            error=f"Ошибка быстрого создания: {str(e)}"
        )
