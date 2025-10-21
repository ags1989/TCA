from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..services.tfs_service import tfs_service, TFSValidationError, TFSConnectionError, TFSRetryableError
from ..models.tfs_models import (
    ProjectInfo,
    WorkItemCreateRequest,
    WorkItemUpdateRequest,
    WorkItemLinkRequest,
    WorkItemInfo,
    WorkItemType,
    LinkType,
    ProjectListResponse,
    WorkItemResponse,
    WorkItemListResponse,
    LinkResponse,
    UserRequest,
    RequestType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tfs", tags=["TFS"])


@router.get("/projects", response_model=ProjectListResponse)
async def get_projects():
    """Получение списка всех проектов"""
    try:
        projects = await tfs_service.get_projects()
        return ProjectListResponse(
            success=True,
            projects=projects
        )
    except Exception as e:
        logger.error(f"Ошибка при получении проектов: {e}")
        return ProjectListResponse(
            success=False,
            error=str(e)
        )


@router.get("/projects/{project_name}/work-items", response_model=WorkItemListResponse)
async def get_work_items(
    project_name: str,
    query: Optional[str] = Query(None, description="Поисковый запрос"),
    work_item_types: Optional[List[str]] = Query(None, description="Типы Work Items для фильтрации")
):
    """Получение списка Work Items в проекте"""
    try:
        work_items = await tfs_service.search_work_items(
            project_name=project_name,
            query=query,
            work_item_types=work_item_types
        )
        return WorkItemListResponse(
            success=True,
            work_items=work_items,
            total_count=len(work_items)
        )
    except Exception as e:
        logger.error(f"Ошибка при получении Work Items: {e}")
        return WorkItemListResponse(
            success=False,
            error=str(e)
        )


@router.get("/work-items/{work_item_id}", response_model=WorkItemResponse)
async def get_work_item(work_item_id: int):
    """Получение информации о конкретном Work Item"""
    try:
        work_item = await tfs_service.get_work_item(work_item_id)
        return WorkItemResponse(
            success=True,
            work_item=work_item
        )
    except Exception as e:
        logger.error(f"Ошибка при получении Work Item {work_item_id}: {e}")
        return WorkItemResponse(
            success=False,
            error=str(e)
        )


@router.post("/projects/{project_name}/work-items", response_model=WorkItemResponse)
async def create_work_item(
    project_name: str,
    work_item_request: WorkItemCreateRequest
):
    """Создание нового Work Item"""
    try:
        work_item = await tfs_service.create_work_item(project_name, work_item_request)
        return WorkItemResponse(
            success=True,
            work_item=work_item
        )
    except Exception as e:
        logger.error(f"Ошибка при создании Work Item: {e}")
        return WorkItemResponse(
            success=False,
            error=str(e)
        )


@router.post("/projects/{project_name}/user-stories", response_model=WorkItemResponse)
async def create_user_story(
    project_name: str,
    title: str,
    description: Optional[str] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[str] = "2",
    tags: Optional[List[str]] = None
):
    """Создание User Story с улучшенной обработкой ошибок"""
    try:
        logger.info(f"API: Запрос на создание User Story в проекте '{project_name}'")
        
        from app.models.request_models import UserStoryData
        
        story_data = UserStoryData(
            title=title,
            description=description,
            project=project_name,
            assigned_to=assigned_to,
            priority=int(priority) if priority else 2,
            tags=tags or []
        )
        
        work_item_id = await tfs_service.create_user_story(story_data)
        work_item = await tfs_service.get_work_item(work_item_id)
        
        logger.info(f"API: User Story успешно создана с ID {work_item.id}")
        return WorkItemResponse(
            success=True,
            work_item=work_item
        )
        
    except TFSValidationError as e:
        logger.warning(f"API: Ошибка валидации при создании User Story: {e}")
        return WorkItemResponse(
            success=False,
            error=f"Ошибка валидации: {str(e)}"
        )
        
    except TFSConnectionError as e:
        logger.error(f"API: Ошибка подключения при создании User Story: {e}")
        return WorkItemResponse(
            success=False,
            error=f"Ошибка подключения к TFS: {str(e)}"
        )
        
    except TFSRetryableError as e:
        logger.error(f"API: Временная ошибка при создании User Story: {e}")
        return WorkItemResponse(
            success=False,
            error=f"Временная ошибка сервиса: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"API: Неожиданная ошибка при создании User Story: {e}", exc_info=True)
        return WorkItemResponse(
            success=False,
            error=f"Неожиданная ошибка: {str(e)}"
        )


@router.post("/projects/{project_name}/tasks", response_model=WorkItemResponse)
async def create_task(
    project_name: str,
    title: str,
    description: Optional[str] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[str] = "2",
    tags: Optional[List[str]] = None
):
    """Создание Task"""
    try:
        from app.models.request_models import TaskData
        
        task_data = TaskData(
            title=title,
            description=description,
            project=project_name,
            assigned_to=assigned_to,
            priority=int(priority) if priority else 2,
            tags=tags or []
        )
        
        work_item_id = await tfs_service.create_task(task_data)
        work_item = await tfs_service.get_work_item(work_item_id)
        return WorkItemResponse(
            success=True,
            work_item=work_item
        )
    except Exception as e:
        logger.error(f"Ошибка при создании Task: {e}")
        return WorkItemResponse(
            success=False,
            error=str(e)
        )


@router.put("/work-items/{work_item_id}", response_model=WorkItemResponse)
async def update_work_item(
    work_item_id: int,
    project_name: str,
    update_request: WorkItemUpdateRequest
):
    """Обновление Work Item"""
    try:
        work_item = await tfs_service.update_work_item(
            work_item_id=work_item_id,
            project_name=project_name,
            update_request=update_request
        )
        return WorkItemResponse(
            success=True,
            work_item=work_item
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении Work Item {work_item_id}: {e}")
        return WorkItemResponse(
            success=False,
            error=str(e)
        )


@router.post("/work-items/link", response_model=LinkResponse)
async def link_work_items(
    project_name: str,
    link_request: WorkItemLinkRequest
):
    """Связывание Work Items между собой"""
    try:
        success = await tfs_service.link_work_items(project_name, link_request)
        return LinkResponse(
            success=success,
            message=f"Work Items {link_request.source_work_item_id} и {link_request.target_work_item_id} успешно связаны"
        )
    except Exception as e:
        logger.error(f"Ошибка при связывании Work Items: {e}")
        return LinkResponse(
            success=False,
            error=str(e)
        )


@router.post("/work-items/{source_id}/link/{target_id}", response_model=LinkResponse)
async def link_work_items_simple(
    source_id: int,
    target_id: int,
    project_name: str,
    link_type: LinkType = LinkType.RELATED,
    comment: Optional[str] = None
):
    """Упрощенное связывание Work Items"""
    try:
        link_request = WorkItemLinkRequest(
            source_work_item_id=source_id,
            target_work_item_id=target_id,
            link_type=link_type,
            comment=comment
        )
        
        success = await tfs_service.link_work_items(project_name, link_request)
        return LinkResponse(
            success=success,
            message=f"Work Items {source_id} и {target_id} успешно связаны"
        )
    except Exception as e:
        logger.error(f"Ошибка при связывании Work Items: {e}")
        return LinkResponse(
            success=False,
            error=str(e)
        )


@router.get("/work-item-types", response_model=List[str])
async def get_work_item_types():
    """Получение доступных типов Work Items"""
    return [work_item_type.value for work_item_type in WorkItemType]


@router.get("/link-types", response_model=List[str])
async def get_link_types():
    """Получение доступных типов связей"""
    return [link_type.value for link_type in LinkType]


@router.post("/user-request", response_model=WorkItemResponse)
async def process_user_request(user_request: UserRequest):
    """Обработка пользовательского запроса с валидацией"""
    try:
        logger.info(f"Обработка запроса типа {user_request.request_type}: {user_request.query[:50]}...")
        
        # Определяем проект (используем default_project если не указан)
        project_name = user_request.project_name or "DefaultProject"
        
        # Обработка в зависимости от типа запроса
        if user_request.request_type == RequestType.CREATE_USER_STORY:
            from app.models.request_models import UserStoryData
            
            story_data = UserStoryData(
                title=user_request.query,
                description=user_request.additional_params.get("description") if user_request.additional_params else None,
                project=project_name,
                assigned_to=user_request.additional_params.get("assigned_to") if user_request.additional_params else None,
                priority=int(user_request.additional_params.get("priority", 2)) if user_request.additional_params else 2,
                tags=user_request.additional_params.get("tags", []) if user_request.additional_params else []
            )
            
            work_item_id = await tfs_service.create_user_story(story_data)
            work_item = await tfs_service.get_work_item(work_item_id)
            
        elif user_request.request_type == RequestType.CREATE_TASK:
            from app.models.request_models import TaskData
            
            task_data = TaskData(
                title=user_request.query,
                description=user_request.additional_params.get("description") if user_request.additional_params else None,
                project=project_name,
                assigned_to=user_request.additional_params.get("assigned_to") if user_request.additional_params else None,
                priority=int(user_request.additional_params.get("priority", 2)) if user_request.additional_params else 2,
                tags=user_request.additional_params.get("tags", []) if user_request.additional_params else []
            )
            
            work_item_id = await tfs_service.create_task(task_data)
            work_item = await tfs_service.get_work_item(work_item_id)
            
        elif user_request.request_type == RequestType.SEARCH_ITEMS:
            # Для поиска возвращаем список найденных элементов
            work_items = await tfs_service.search_work_items(
                project_name=project_name,
                query=user_request.query,
                work_item_types=user_request.additional_params.get("work_item_types") if user_request.additional_params else None
            )
            
            if work_items:
                # Возвращаем первый найденный элемент
                work_item = work_items[0]
            else:
                return WorkItemResponse(
                    success=False,
                    error="Work Items не найдены"
                )
                
        elif user_request.request_type == RequestType.GET_PROJECTS:
            projects = await tfs_service.get_projects()
            if projects:
                # Возвращаем информацию о первом проекте как WorkItem
                first_project = projects[0]
                work_item = WorkItemInfo(
                    id=0,  # Проекты не имеют числового ID как Work Items
                    work_item_type="Project",
                    title=first_project.name,
                    state="Active",
                    fields={"description": first_project.description}
                )
            else:
                return WorkItemResponse(
                    success=False,
                    error="Проекты не найдены"
                )
        else:
            return WorkItemResponse(
                success=False,
                error=f"Тип запроса {user_request.request_type} пока не поддерживается"
            )
        
        return WorkItemResponse(
            success=True,
            work_item=work_item
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке пользовательского запроса: {e}")
        return WorkItemResponse(
            success=False,
            error=str(e)
        )


@router.get("/request-types", response_model=List[str])
async def get_request_types():
    """Получение доступных типов запросов"""
    return [request_type.value for request_type in RequestType]
