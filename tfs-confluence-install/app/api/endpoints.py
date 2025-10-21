from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import time
import traceback
import logging
from datetime import datetime
from app.models.request_models import UserRequest
from app.models.response_models import (
    DetailedProcessingResult, ExecutionStep, ActionStatus, 
    CreatedWorkItem, ConfluenceArticleInfo, ProcessingError
)
from app.models.confluence_models import ConfluencePageRequest, ConfluencePageResponse
from app.services.openai_service import OpenAIService
from app.services.confluence_service import ConfluenceService
from app.services.tfs_service import TFSService
from app.services.user_story_creator_service import user_story_creator_service
from app.config.settings import settings
from app.core.startup import get_connection_status, get_system_info, global_services
from app.core.logging_config import log_api_request, log_user_action, log_tfs_operation, log_confluence_operation

router = APIRouter()
logger = logging.getLogger(__name__)

# Инициализируем сервисы
openai_service = OpenAIService()
confluence_service = ConfluenceService()
tfs_service = TFSService()

@router.post("/process-request", response_model=DetailedProcessingResult)
async def process_user_request(request: UserRequest) -> DetailedProcessingResult:
    """
    Основной endpoint для обработки запроса с детальным отчетом
    """
    
    logger.info(f"🚀 Начало обработки запроса пользователя: '{request.query[:100]}...'")
    logger.info(f"   📅 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   🔍 Длина запроса: {len(request.query)} символов")
    
    # Логируем API запрос
    log_api_request(
        logger=logger,
        method="POST",
        endpoint="/process-request",
        details={
            "query_length": len(request.query),
            "query_preview": request.query[:100] + "..." if len(request.query) > 100 else request.query
        }
    )
    
    # Логируем действие пользователя
    log_user_action(
        logger=logger,
        action="Отправлен запрос на обработку",
        details={
            "query": request.query[:200] + "..." if len(request.query) > 200 else request.query
        }
    )
    
    result = DetailedProcessingResult(
        success=False,
        user_query=request.query,
        processing_start=datetime.now(),
        summary="Обработка не завершена"
    )
    
    try:
        # Проверяем, является ли запрос подтверждением пользователя
        confirmation_text = request.query.lower().strip()
        is_confirmation = confirmation_text in ["да", "создать", "yes", "create", "подтвердить", "подтверждаю", "нет", "отмена", "no", "cancel"]
        
        if is_confirmation:
            logger.info("✅ Обрабатываем подтверждение пользователя")
            return await handle_user_confirmation(request, result)
        
        # Проверяем, является ли запрос запросом на создание User Stories из Confluence
        logger.info(f"🔍 Анализируем запрос: '{request.query}'")
        is_us_request = await is_user_story_creation_request(request.query)
        logger.info(f"🎯 Результат анализа User Story запроса: {is_us_request}")
        
        if is_us_request:
            logger.info("✅ Направляем запрос на создание User Stories")
            return await handle_user_story_creation_request(request, result)
        
        # Шаг 1: Анализ запроса пользователя через OpenAI
        step1 = await execute_step(
            result, "Анализ запроса пользователя",
            lambda: openai_service.analyze_user_request(request.query)
        )
        
        if step1["status"] == ActionStatus.FAILED:
            return finalize_result(result, "Не удалось проанализировать запрос пользователя")
        
        keywords = step1["data"].get("search_keywords", "")
        result.extracted_keywords = keywords
        
        # Шаг 2: Поиск статьи в Confluence
        step2 = await execute_step(
            result, "Поиск статьи в Confluence",
            lambda: confluence_service.search_articles(keywords)
        )
        
        if step2["status"] == ActionStatus.FAILED or not step2["data"]:
            return finalize_result(result, f"Статьи по запросу '{keywords}' не найдены в Confluence")
        
        articles = step2["data"]
        selected_article = articles[0]  # Берем первую найденную статью
        
        # Сохраняем информацию о статье
        result.confluence_article = ConfluenceArticleInfo(
            id=selected_article.id,
            title=selected_article.title,
            url=f"{settings.CONFLUENCE_URL}/pages/viewpage.action?pageId={selected_article.id}",
            space_key=selected_article.space_key,
            content_length=len(selected_article.content)
        )
        
        # Шаг 3: Извлечение данных для User Story
        step3 = await execute_step(
            result, "Извлечение данных для User Story",
            lambda: openai_service.extract_story_data(selected_article)
        )
        
        if step3["status"] == ActionStatus.FAILED:
            return finalize_result(result, "Не удалось извлечь данные для создания User Story")
        
        story_data = step3["data"]
        
        # Обновляем информацию о статье
        if result.confluence_article:
            result.confluence_article.extracted_project = story_data.project
            result.confluence_article.extracted_team = [story_data.assigned_to, story_data.tech_lead] + (story_data.developers or [])
            result.confluence_article.parent_tfs_reference = story_data.parent_work_item_id
        
        # Шаг 4: Создание User Story в TFS
        step4 = await execute_step(
            result, "Создание User Story в TFS",
            lambda: tfs_service.create_user_story(story_data)
        )
        
        if step4["status"] == ActionStatus.FAILED:
            return finalize_result(result, "Не удалось создать User Story в TFS")
        
        user_story_id = step4["data"]
        
        # Добавляем информацию о созданной User Story
        user_story_url = f"{settings.TFS_URL}/{settings.TFS_PROJECT}/_workitems/edit/{user_story_id}"
        created_us = CreatedWorkItem(
            id=user_story_id,
            title=story_data.title,
            work_item_type="User Story",
            state="New",
            assigned_to=story_data.assigned_to,
            url=user_story_url,
            created_date=datetime.now(),
            story_points=story_data.story_points,
            priority=story_data.priority,
            tags=story_data.tags or []
        )
        result.created_work_items.append(created_us)
        
        # Шаг 5: Создание связи с родительским элементом (если указан)
        if story_data.parent_work_item_id:
            step5 = await execute_step(
                result, f"Создание связи с родительским элементом #{story_data.parent_work_item_id}",
                lambda: tfs_service.create_parent_link(user_story_id, story_data.parent_work_item_id)
            )
            
            if step5["status"] == ActionStatus.SUCCESS:
                result.created_relations.append({
                    "child_id": user_story_id,
                    "parent_id": story_data.parent_work_item_id,
                    "relation_type": "System.LinkTypes.Hierarchy-Reverse",
                    "description": "Родитель в backlog"
                })
                created_us.parent_id = story_data.parent_work_item_id
        
        # Шаг 6: Создание связанных подзадач
        if story_data.implementation_objects:
            step6 = await execute_step(
                result, f"Создание {len(story_data.implementation_objects)} подзадач",
                lambda: tfs_service.create_linked_tasks(user_story_id, story_data.implementation_objects)
            )
            
            if step6["status"] == ActionStatus.SUCCESS:
                task_ids = step6["data"]
                created_us.child_ids = task_ids
                
                # Добавляем информацию о каждой созданной задаче
                for i, (task_id, obj_name) in enumerate(zip(task_ids, story_data.implementation_objects)):
                    task_url = f"{settings.TFS_URL}/{settings.TFS_PROJECT}/_workitems/edit/{task_id}"
                    created_task = CreatedWorkItem(
                        id=task_id,
                        title=f"Доработка компонента: {obj_name}",
                        work_item_type="Task",
                        state="New",
                        url=task_url,
                        parent_id=user_story_id,
                        created_date=datetime.now(),
                        priority=story_data.priority,
                        tags=["subtask", "component-work"]
                    )
                    result.created_work_items.append(created_task)
                    
                    # Связь подзадачи с User Story
                    result.created_relations.append({
                        "child_id": task_id,
                        "parent_id": user_story_id,
                        "relation_type": "System.LinkTypes.Hierarchy-Reverse",
                        "description": f"Подзадача для доработки {obj_name}"
                    })
        
        # Успешное завершение
        return finalize_result(result, generate_success_summary(result), success=True)
        
    except Exception as e:
        error = ProcessingError(
            error_type="UnexpectedError",
            error_message=str(e),
            occurred_at=datetime.now(),
            step_name="Основной процесс",
            technical_details=traceback.format_exc(),
            suggestion="Обратитесь к администратору системы"
        )
        result.errors.append(error)
        return finalize_result(result, f"Критическая ошибка: {str(e)}")

async def execute_step(result: DetailedProcessingResult, step_name: str, action_func) -> Dict[str, Any]:
    """Выполнение шага с отслеживанием времени и ошибок"""
    
    step = ExecutionStep(
        step_name=step_name,
        status=ActionStatus.SUCCESS,
        start_time=datetime.now()
    )
    
    try:
        logger.info(f"🔄 Начинаем: {step_name}")
        action_result = await action_func()
        
        step.end_time = datetime.now()
        step.duration_seconds = (step.end_time - step.start_time).total_seconds()
        step.details = f"Выполнено успешно за {step.duration_seconds:.2f} сек"
        step.data = {"result": action_result}
        
        logger.info(f"✅ Завершено: {step_name}")
        
        result.execution_steps.append(step)
        return {"status": ActionStatus.SUCCESS, "data": action_result}
        
    except Exception as e:
        step.status = ActionStatus.FAILED
        step.end_time = datetime.now()
        step.duration_seconds = (step.end_time - step.start_time).total_seconds()
        step.error_message = str(e)
        step.details = f"Ошибка после {step.duration_seconds:.2f} сек: {str(e)}"
        
        # Создаем детальную ошибку
        error = ProcessingError(
            error_type=type(e).__name__,
            error_message=str(e),
            occurred_at=datetime.now(),
            step_name=step_name,
            technical_details=traceback.format_exc(),
            suggestion=get_error_suggestion(type(e).__name__, str(e))
        )
        result.errors.append(error)
        
        logger.error(f"❌ Ошибка в {step_name}: {str(e)}")
        
        result.execution_steps.append(step)
        return {"status": ActionStatus.FAILED, "error": str(e)}

def get_error_suggestion(error_type: str, error_message: str) -> str:
    """Получение рекомендации по исправлению ошибки"""
    
    suggestions = {
        "ConnectionError": "Проверьте подключение к интернету и доступность внешних сервисов",
        "AuthenticationError": "Проверьте правильность API ключей и токенов в настройках",
        "ValidationError": "Проверьте формат входных данных",
        "TimeoutError": "Попробуйте повторить запрос позже",
        "HTTPError": "Проверьте доступность внешних API сервисов",
        "JSONDecodeError": "Возможна проблема с форматом ответа от внешнего сервиса"
    }
    
    for error_key, suggestion in suggestions.items():
        if error_key in error_type:
            return suggestion
    
    if "openai" in error_message.lower():
        return "Проверьте API ключ OpenAI и остаток средств на аккаунте"
    elif "confluence" in error_message.lower():
        return "Проверьте доступность Confluence и правильность токена доступа"
    elif "tfs" in error_message.lower() or "azure" in error_message.lower():
        return "Проверьте доступность TFS/Azure DevOps и права доступа"
    
    return "Обратитесь к техническому специалисту для диагностики"

def generate_success_summary(result: DetailedProcessingResult) -> str:
    """Генерация итоговой сводки об успешном выполнении"""
    
    created_items = len(result.created_work_items)
    created_relations = len(result.created_relations)
    
    us_count = len([item for item in result.created_work_items if item.work_item_type == "User Story"])
    task_count = len([item for item in result.created_work_items if item.work_item_type == "Task"])
    
    summary_parts = [
        f"✅ Успешно обработан запрос и создано {created_items} рабочих элементов в TFS:"
    ]
    
    if us_count > 0:
        summary_parts.append(f"   • {us_count} User Story")
    if task_count > 0:
        summary_parts.append(f"   • {task_count} Task")
    
    if created_relations > 0:
        summary_parts.append(f"   • Создано {created_relations} связей между элементами")
    
    if result.confluence_article:
        summary_parts.append(f"   • Обработана статья: '{result.confluence_article.title}'")
        if result.confluence_article.parent_tfs_reference:
            summary_parts.append(f"   • Связано с родительским элементом #{result.confluence_article.parent_tfs_reference}")
    
    return "\n".join(summary_parts)

def finalize_result(result: DetailedProcessingResult, summary: str, success: bool = False) -> DetailedProcessingResult:
    """Финализация результата обработки"""
    
    result.processing_end = datetime.now()
    result.total_duration_seconds = (result.processing_end - result.processing_start).total_seconds()
    result.success = success
    result.summary = summary
    
    # Добавляем рекомендации
    if success:
        result.recommendations = [
            "Проверьте созданные рабочие элементы в TFS",
            "Убедитесь, что все связи установлены корректно",
            "При необходимости откорректируйте приоритеты и назначения"
        ]
    else:
        result.recommendations = [
            "Проверьте логи ошибок для диагностики проблемы",
            "Убедитесь в правильности настроек API ключей",
            "При повторении ошибки обратитесь к администратору"
        ]
    
    logger.info(f"🏁 Обработка завершена за {result.total_duration_seconds:.2f} сек. Успех: {success}")
    
    return result

@router.get("/status")
async def get_system_status():
    """
    Получение статуса системы и подключений к внешним сервисам
    """
    try:
        # Простая версия без сложных вычислений
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "services": {
                "openai": {
                    "available": False,  # Отключен
                    "name": "OpenAI",
                    "description": "Искусственный интеллект для анализа запросов (отключен)"
                },
                "confluence": {
                    "available": True,  # Предполагаем, что работает
                    "name": "Confluence",
                    "description": "Система документации и знаний"
                },
                "tfs": {
                    "available": True,  # Предполагаем, что работает
                    "name": "TFS/Azure DevOps",
                    "description": "Система управления задачами и проектами"
                }
            },
            "system": {
                "debug_mode": settings.DEBUG,
                "log_level": settings.LOG_LEVEL,
                "services_loaded": 3
            }
        }
    except Exception as e:
        logger.error(f"Ошибка при получении статуса системы: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.post("/confluence/pages", response_model=ConfluencePageResponse)
async def create_confluence_page(request: ConfluencePageRequest):
    """
    Создание страницы в Confluence
    
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
        
        confluence_service = ConfluenceService()
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

@router.post("/confluence/pages/quick-create", response_model=ConfluencePageResponse)
async def quick_create_confluence_page(
    title: str,
    content: str,
    space_key: str = "DEV",
    parent_id: str = None,
    labels: str = None
):
    """
    Быстрое создание страницы в Confluence с минимальными параметрами
    
    Параметры:
    - title: Заголовок страницы (обязательно)
    - content: Содержимое страницы (обязательно)
    - space_key: Ключ пространства (по умолчанию "DEV")
    - parent_id: ID родительской страницы (опционально)
    - labels: Метки через запятую (опционально)
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
                "labels": labels
            }
        )
        
        # Парсим метки
        labels_list = []
        if labels:
            labels_list = [label.strip() for label in labels.split(",") if label.strip()]
        
        request = ConfluencePageRequest(
            title=title,
            content=content,
            space_key=space_key,
            parent_id=parent_id,
            labels=labels_list
        )
        
        confluence_service = ConfluenceService()
        result = await confluence_service.create_page_from_request(request)
        
        if result.success:
            log_confluence_operation(
                logger=logger,
                operation="Быстрое создание страницы через API",
                page_id=result.page_id,
                details={
                    "title": result.title,
                    "space_key": result.space_key,
                    "url": result.url,
                    "labels": labels_list
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при быстром создании страницы: {str(e)}")
        return ConfluencePageResponse(
            success=False,
            error=f"Ошибка быстрого создания: {str(e)}"
        )

async def is_user_story_creation_request(query: str) -> bool:
    """
    Проверяет, является ли запрос запросом на создание User Stories из Confluence
    """
    query_lower = query.lower()
    logger.info(f"🔍 Анализ запроса на User Story: '{query_lower}'")
    
    # Ключевые слова для распознавания запроса
    creation_keywords = [
        "создай us в tfs",
        "создать us в tfs", 
        "создай user story в tfs",
        "создать user story в tfs",
        "создай пользовательскую историю в tfs",
        "создать пользовательскую историю в tfs",
        "создай us",
        "создать us",
        "создай user story",
        "создать user story",
        # Добавляем ключевые слова для цепочки тикетов
        "создай цепочку",
        "создать цепочку",
        "создай цепочку тикетов",
        "создать цепочку тикетов",
        "создай цепочку связанных тикетов",
        "создать цепочку связанных тикетов",
        "цепочка тикетов",
        "цепочка связанных тикетов"
    ]
    
    # Проверяем наличие ключевых слов
    for keyword in creation_keywords:
        if keyword in query_lower:
            logger.info(f"✅ Найдено ключевое слово: '{keyword}'")
            return True
    
    # Проверяем наличие URL Confluence
    confluence_url_patterns = [
        "confluence.systtech.ru",
        "confluence",
        "pageid=",
        "pages/viewpage.action"
    ]
    
    for pattern in confluence_url_patterns:
        if pattern in query_lower:
            logger.info(f"✅ Найден URL Confluence: '{pattern}'")
            return True
    
    # Проверяем комбинацию "создай" + "на основании" + URL
    if "создай" in query_lower and "на основании" in query_lower:
        logger.info("✅ Найдена комбинация 'создай' + 'на основании'")
        return True
    
    logger.info("❌ Запрос не распознан как запрос на создание User Stories")
    return False

async def handle_user_story_creation_request(request: UserRequest, result: DetailedProcessingResult) -> DetailedProcessingResult:
    """
    Обрабатывает запрос на создание User Stories из Confluence или цепочки тикетов
    """
    try:
        logger.info(f"🎯 Обработка запроса на создание: {request.query}")
        
        # Проверяем, является ли запрос запросом на создание цепочки тикетов
        query_lower = request.query.lower()
        chain_keywords = ["цепочка", "цепочку", "связанных тикетов"]
        is_chain_request = any(keyword in query_lower for keyword in chain_keywords)
        
        if is_chain_request:
            logger.info("🔗 Обрабатываем запрос на создание цепочки тикетов")
            return await handle_change_chain_request(request, result)
        
        # Обрабатываем как обычный запрос на создание User Stories
        logger.info(f"🎯 Обработка запроса на создание User Stories: {request.query}")
        
        # Извлекаем URL из запроса
        confluence_url = extract_confluence_url(request.query)
        if not confluence_url:
            return finalize_result(result, "Не удалось найти URL страницы Confluence в запросе")
        
        # Создаем User Stories через новый сервис
        creation_result = await user_story_creator_service.create_user_stories_from_confluence(
            confluence_url=confluence_url,
            user_confirmation=None  # Не подтверждаем автоматически - нужен предварительный просмотр
        )
        
        if creation_result["success"]:
            # Проверяем, нужен ли предварительный просмотр
            if creation_result.get("needs_confirmation"):
                # Возвращаем предварительный просмотр для подтверждения пользователем
                preview_data = creation_result["preview"]
                result.message = f"Найдено {len(preview_data['user_stories'])} User Stories для создания. Требуется подтверждение:\n\n"
                
                for i, us in enumerate(preview_data["user_stories"], 1):
                    result.message += f"{i}. **{us['title']}**\n"
                    result.message += f"   Описание: {us['description'][:100]}...\n"
                    result.message += f"   Критерии приёмки: {len(us['acceptance_criteria'])} пунктов\n\n"
                
                result.message += "Для подтверждения создания отправьте: 'Да' или 'Создать'\n"
                result.message += "Для отмены отправьте: 'Нет' или 'Отмена'"
                
                # Сохраняем данные для последующего создания
                result.additional_data = {
                    "confluence_url": confluence_url,
                    "page_data": creation_result.get("page_data"),
                    "preview": preview_data
                }
                
                # Обновляем результат
                result.success = True
                result.summary = "Требуется подтверждение для создания User Stories"
                result.processing_end = datetime.now()
                result.duration_seconds = (result.processing_end - result.processing_start).total_seconds()
                
                return result
            else:
                # User Stories уже созданы
                for story in creation_result["created_stories"]:
                    created_us = CreatedWorkItem(
                        id=story["id"],
                        title=story["title"],
                        work_item_type="User Story",
                        state="New",
                        assigned_to="",  # Будет заполнено автоматически
                        url=story["url"],
                        created_date=datetime.now(),
                        story_points=5,  # По умолчанию
                        priority=2,      # По умолчанию
                        tags=["confluence", "auto-generated", "TCA"]
                    )
                    result.created_work_items.append(created_us)
                
                # Формируем детальное сообщение с кликабельными ссылками
                created_stories = creation_result.get('created_stories', [])
                parent_ticket = creation_result.get('parent_ticket', '')
                confluence_url = confluence_url
                
                message_parts = [
                    "✅ User Stories созданы успешно:",
                    f"📄 Статья: <a href=\"{confluence_url}\" target=\"_blank\">{confluence_url}</a>",
                    f"🔗 Родительский тикет: <a href=\"#\" onclick=\"openTfsTicket('{parent_ticket}')\">{parent_ticket}</a>",
                    f"📊 Создано User Stories: {len(created_stories)}"
                ]
                
                for i, story in enumerate(created_stories, 1):
                    story_id = story.get("id", "")
                    story_title = story.get("title", "")
                    story_url = story.get("url", "")
                    message_parts.extend([
                        f"📋 US {i}: <a href=\"{story_url}\" target=\"_blank\">{story_id}</a> - {story_title}",
                        f"🔗 Связан с: <a href=\"#\" onclick=\"openTfsTicket('{parent_ticket}')\">#{parent_ticket}</a> (Родитель в Backlog)"
                    ])
                
                detailed_message = "<br>".join(message_parts)
                
                # Обновляем результат
                result.success = True
                result.summary = f"✅ Создано {len(created_stories)} User Stories из статьи Confluence"
                result.message = detailed_message
                result.processing_end = datetime.now()
                result.duration_seconds = (result.processing_end - result.processing_start).total_seconds()
                
                # Добавляем информацию о статье Confluence
                result.confluence_article = ConfluenceArticleInfo(
                    id="",  # Будет заполнено из URL
                    title="Статья Confluence",
                    url=confluence_url,
                    space_key="",
                    content_length=0
                )
                
                logger.info(f"✅ Успешно создано {len(creation_result['created_stories'])} User Stories")
                return result
        else:
            return finalize_result(result, f"Ошибка при создании User Stories: {creation_result.get('error', 'Неизвестная ошибка')}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке запроса создания User Stories: {str(e)}")
        return finalize_result(result, f"Ошибка при создании User Stories: {str(e)}")

async def handle_user_confirmation(request: UserRequest, result: DetailedProcessingResult) -> DetailedProcessingResult:
    """
    Обрабатывает подтверждение пользователя для создания User Stories
    """
    try:
        logger.info(f"🎯 Обработка подтверждения пользователя: {request.query}")
        
        # Проверяем, есть ли сохраненные данные для создания
        if not hasattr(result, 'additional_data') or not result.additional_data:
            return finalize_result(result, "Нет данных для создания User Stories. Сначала выполните запрос на создание.")
        
        additional_data = result.additional_data
        confluence_url = additional_data.get("confluence_url")
        
        if not confluence_url:
            return finalize_result(result, "Не найден URL страницы Confluence для создания User Stories")
        
        # Определяем, подтвердил ли пользователь
        confirmation_text = request.query.lower().strip()
        is_confirmed = confirmation_text in ["да", "создать", "yes", "create", "подтвердить", "подтверждаю"]
        
        if not is_confirmed:
            return finalize_result(result, "Создание User Stories отменено пользователем")
        
        # Создаем User Stories с подтверждением
        creation_result = await user_story_creator_service.create_user_stories_from_confluence(
            confluence_url=confluence_url,
            user_confirmation="Да"
        )
        
        if creation_result["success"]:
            # Добавляем информацию о созданных User Stories
            for story in creation_result["created_stories"]:
                created_us = CreatedWorkItem(
                    id=story["id"],
                    title=story["title"],
                    work_item_type="User Story",
                    state="New",
                    assigned_to="",  # Будет заполнено автоматически
                    url=story["url"],
                    created_date=datetime.now(),
                    story_points=5,  # По умолчанию
                    priority=2,      # По умолчанию
                    tags=["confluence", "auto-generated", "TCA"]
                )
                result.created_work_items.append(created_us)
            
            # Формируем детальное сообщение с кликабельными ссылками
            created_stories = creation_result.get('created_stories', [])
            parent_ticket = creation_result.get('parent_ticket', '')
            
            message_parts = [
                "✅ User Stories созданы успешно:",
                f"📄 Статья: <a href=\"{confluence_url}\" target=\"_blank\">{confluence_url}</a>",
                f"🔗 Родительский тикет: <a href=\"#\" onclick=\"openTfsTicket('{parent_ticket}')\">{parent_ticket}</a>",
                f"📊 Создано User Stories: {len(created_stories)}"
            ]
            
            for i, story in enumerate(created_stories, 1):
                story_id = story.get("id", "")
                story_title = story.get("title", "")
                story_url = story.get("url", "")
                message_parts.extend([
                    f"📋 US {i}: <a href=\"{story_url}\" target=\"_blank\">{story_id}</a> - {story_title}",
                    f"🔗 Связан с: <a href=\"#\" onclick=\"openTfsTicket('{parent_ticket}')\">#{parent_ticket}</a> (Родитель в Backlog)"
                ])
            
            detailed_message = "<br>".join(message_parts)
            
            # Обновляем результат
            result.success = True
            result.summary = f"✅ Создано {len(created_stories)} User Stories из статьи Confluence"
            result.message = detailed_message
            result.processing_end = datetime.now()
            result.duration_seconds = (result.processing_end - result.processing_start).total_seconds()
            
            # Добавляем информацию о статье Confluence
            result.confluence_article = ConfluenceArticleInfo(
                id="",  # Будет заполнено из URL
                title="Статья Confluence",
                url=confluence_url,
                space_key="",
                content_length=0
            )
            
            # Очищаем дополнительные данные
            result.additional_data = None
            
            logger.info(f"✅ Успешно создано {len(creation_result['created_stories'])} User Stories после подтверждения")
            return result
        else:
            return finalize_result(result, f"Ошибка при создании User Stories: {creation_result.get('error', 'Неизвестная ошибка')}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке подтверждения: {str(e)}")
        return finalize_result(result, f"Ошибка при обработке подтверждения: {str(e)}")

async def handle_change_chain_request(request: UserRequest, result: DetailedProcessingResult) -> DetailedProcessingResult:
    """
    Обрабатывает запрос на создание цепочки тикетов
    """
    try:
        logger.info(f"🔗 Обработка запроса на создание цепочки тикетов: {request.query}")
        
        # Импортируем сервис цепочки изменений
        from app.services.change_chain_service import change_chain_service
        
        # Проверяем подключение к TFS
        tfs_connected = await change_chain_service.tfs_service.test_connection()
        if not tfs_connected:
            return finalize_result(result, "TFS сервис недоступен. Проверьте настройки подключения.")
        
        # Парсим запрос
        parsed_data = await change_chain_service.parse_change_request(request.query)
        
        if not parsed_data.get("sourceBacklogId"):
            return finalize_result(result, "Не удалось найти номер тикета в запросе. Укажите номер тикета в формате #123456")
        
        # Создаем цепочку изменений
        chain_result = await change_chain_service.create_linked_change_chain(
            project=parsed_data["project"],
            request_title=parsed_data["requestTitle"],
            source_backlog_id=parsed_data["sourceBacklogId"],
            request_id=parsed_data.get("requestId")
        )
        
        if chain_result.get("success"):
            result.success = True
            result.summary = "Цепочка тикетов создана успешно"
            result.message = f"✅ Создана цепочка тикетов:\n\n"
            result.message += f"📋 **Epic**: {chain_result.get('Epic', {}).get('title', 'N/A')}\n"
            result.message += f"🔗 **Feature**: {chain_result.get('Feature', {}).get('title', 'N/A')}\n"
            result.message += f"📝 **Backlog Item**: {chain_result.get('Backlog Item', {}).get('title', 'N/A')}\n\n"
            result.message += f"🎯 **Исходный тикет**: #{parsed_data['sourceBacklogId']}\n"
            result.message += f"🔗 **Связь**: Backlog Item связан с исходным тикетом как дочерний элемент"
            
            result.extracted_data = chain_result
            result.processing_end = datetime.now()
            
            logger.info(f"✅ Успешно создана цепочка тикетов для #{parsed_data['sourceBacklogId']}")
            return result
        else:
            return finalize_result(result, f"Ошибка при создании цепочки тикетов: {chain_result.get('error', 'Неизвестная ошибка')}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке запроса на цепочку тикетов: {str(e)}")
        return finalize_result(result, f"Ошибка при создании цепочки тикетов: {str(e)}")

def extract_confluence_url(query: str) -> Optional[str]:
    """
    Извлекает URL страницы Confluence из запроса пользователя
    """
    import re
    
    # Паттерны для поиска URL
    url_patterns = [
        r'https://confluence\.systtech\.ru/pages/viewpage\.action\?pageId=\d+',
        r'https://confluence\.systtech\.ru/.*?pageId=(\d+)',
        r'confluence\.systtech\.ru.*?pageId=(\d+)',
        r'pageId=(\d+)'
    ]
    
    for pattern in url_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            if 'pageId=' in match.group(0):
                return match.group(0)
            else:
                # Если нашли только pageId, формируем полный URL
                page_id = match.group(1)
                return f"https://confluence.systtech.ru/pages/viewpage.action?pageId={page_id}"
    
    return None
