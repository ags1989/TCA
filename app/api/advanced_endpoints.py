from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import re
from datetime import datetime
from app.services.change_chain_service import change_chain_service
from app.services.checklist_service import checklist_service
from app.services.user_story_creator_service import user_story_creator_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Advanced Features"])

# Простое хранилище состояния в памяти (в продакшене лучше использовать Redis или базу данных)
pending_user_story_requests = {}

@router.post("/change-chain-chat")
async def change_chain_chat(request: Dict[str, str]) -> Dict[str, Any]:
    """
    Process natural language request for creating change chains
    """
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        logger.info(f"Processing request: {message}")
        
        # Сначала анализируем тип запроса
        query_lower = message.lower().strip()
        
        # Проверяем, является ли запрос запросом на создание User Stories или цепочки тикетов
        if await is_user_story_creation_request(message):
            logger.info("✅ Направляем запрос на создание User Stories или цепочки тикетов")
            result = await handle_user_story_creation_request_advanced(message)
            logger.info(f"✅ Получен результат от handle_user_story_creation_request_advanced: success={result.get('success')}, needs_confirmation={result.get('needs_confirmation')}")
            logger.info(f"🔍 Сообщение в результате: {result.get('message', 'No message')}")
            return result
        
        # Проверяем, является ли запрос подтверждением пользователя (только если это не запрос на создание)
        is_confirmation = query_lower in ["да", "создать", "yes", "create", "подтвердить", "подтверждаю", "нет", "отмена", "no", "cancel", "а", "д"]
        
        logger.info(f"🔍 Проверка подтверждения: '{query_lower}' -> is_confirmation={is_confirmation}")
        
        if is_confirmation:
            logger.info("✅ Обрабатываем подтверждение пользователя для User Stories")
            result = await handle_user_confirmation_advanced(message)
            logger.info(f"🔍 Результат подтверждения: {result}")
            return result
        
        # Check TFS connection before processing request
        tfs_connected = await change_chain_service.tfs_service.test_connection()
        if not tfs_connected:
            raise HTTPException(status_code=503, detail="TFS service is not available")
        
        logger.info(f"Processing change chain request: {message}")
        
        # Parse the request using OpenAI
        parsed_data = await change_chain_service.parse_change_request(message)
        
        # Create the change chain
        result = await change_chain_service.create_linked_change_chain(
            project=parsed_data["project"],
            request_title=parsed_data["requestTitle"],
            source_backlog_id=parsed_data["sourceBacklogId"],
            request_id=parsed_data.get("requestId")
        )
        
        return {
            "success": True,
            "message": "✅ Цепочка изменений создана успешно",
            "data": result,
            "parsed_request": parsed_data
        }
        
    except Exception as e:
        logger.error(f"Error in change chain chat: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка при создании цепочки изменений: {str(e)}"
        }

async def handle_user_confirmation_advanced(message: str) -> Dict[str, Any]:
    """
    Обрабатывает подтверждение пользователя для создания User Stories (для advanced endpoints)
    """
    try:
        logger.info(f"🎯 Обработка подтверждения пользователя: {message}")
        
        # Определяем, подтвердил ли пользователь
        confirmation_text = message.lower().strip()
        is_confirmed = confirmation_text in ["да", "создать", "yes", "create", "подтвердить", "подтверждаю", "а", "д"]
        
        if not is_confirmed:
            return {
                "success": False,
                "message": "Создание User Stories отменено пользователем"
            }
        
        # Ищем последний запрос на создание User Stories
        if not pending_user_story_requests:
            return {
                "success": False,
                "message": "Нет активных запросов на создание User Stories. Сначала выполните запрос на создание."
            }
        
        # Берем последний запрос (самый свежий)
        latest_request_id = max(pending_user_story_requests.keys(), 
                              key=lambda x: pending_user_story_requests[x]["created_at"])
        request_data = pending_user_story_requests[latest_request_id]
        
        logger.info(f"🔍 Найден последний запрос: {latest_request_id}")
        logger.info(f"🔗 URL Confluence: {request_data['confluence_url']}")
        
        # Создаем User Stories с подтверждением
        creation_result = await user_story_creator_service.create_user_stories_from_confluence(
            confluence_url=request_data["confluence_url"],
            user_confirmation="Да"
        )
        
        if creation_result["success"]:
            # Удаляем запрос из очереди
            del pending_user_story_requests[latest_request_id]
            
            # Формируем детальное сообщение с кликабельными ссылками
            created_stories = creation_result["created_stories"]
            parent_ticket = creation_result.get("parent_ticket", "")
            confluence_url = request_data["confluence_url"]
            
            message_parts = [
                "✅ User Stories созданы успешно:",
                f"📄 Статья: <a href=\"{confluence_url}\" target=\"_blank\">{confluence_url}</a>",
                f"🔗 Родительский тикет: <a href=\"#\" onclick=\"openTfsTicket('{parent_ticket}')\">{parent_ticket}</a>",
                f"📊 Создано User Stories: {len(created_stories)}"
            ]
            
            # Добавляем информацию о каждой User Story
            for i, story in enumerate(created_stories, 1):
                story_id = story.get("id", "")
                story_title = story.get("title", "")
                story_url = story.get("url", "")
                message_parts.extend([
                    f"📋 US {i}: <a href=\"{story_url}\" target=\"_blank\">{story_id}</a> - {story_title}",
                    f"🔗 Связан с: <a href=\"#\" onclick=\"openTfsTicket('{parent_ticket}')\">#{parent_ticket}</a> (Родитель в Backlog)"
                ])
            
            detailed_message = "<br>".join(message_parts)
            
            return {
                "success": True,
                "message": detailed_message,
                "created_stories": created_stories,
                "data": {
                    "created_stories": created_stories,
                    "parent_ticket": parent_ticket,
                    "confluence_url": confluence_url
                }
            }
        else:
            return {
                "success": False,
                "error": creation_result.get("error", "Неизвестная ошибка"),
                "message": f"Ошибка при создании User Stories: {creation_result.get('error', 'Неизвестная ошибка')}"
            }
        
    except Exception as e:
        logger.error(f"Ошибка при обработке подтверждения: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка при обработке подтверждения: {str(e)}"
        }

@router.post("/checklist-chat")
async def checklist_chat(request: Dict[str, str]) -> Dict[str, Any]:
    """
    Process checklist request: Создай чек-лист БДК ЗЗЛ #<id>
    """
    try:
        # Check TFS connection before processing request
        tfs_connected = await checklist_service.tfs_service.test_connection()
        if not tfs_connected:
            raise HTTPException(status_code=503, detail="TFS service is not available")
        
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        logger.info(f"Processing checklist request: {message}")
        
        # Parse work item ID from message
        work_item_id = _parse_checklist_request(message)
        if not work_item_id:
            raise HTTPException(status_code=400, detail="Не удалось найти ID рабочего элемента в запросе")
        
        # Create checklist
        checklist = await checklist_service.create_checklist(work_item_id)
        
        return {
            "success": True,
            "message": f"Чек-лист БДК ЗЗЛ для элемента #{work_item_id}",
            "work_item_id": work_item_id,
            "checklist": checklist
        }
        
    except Exception as e:
        logger.error(f"Error in checklist chat: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка при создании чек-листа: {str(e)}"
        }

def _parse_checklist_request(message: str) -> int:
    """
    Parse work item ID from checklist request
    Format: Создай чек-лист БДК ЗЗЛ #<number>
    """
    
    # Pattern to match: Создай чек-лист БДК ЗЗЛ #<number>
    pattern = r'Создай\s+чек-лист\s+БДК\s+ЗЗЛ\s+#(\d+)'
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        return int(match.group(1))
    
    # Alternative pattern: just look for #<number> anywhere in the message
    pattern = r'#(\d+)'
    match = re.search(pattern, message)
    
    if match:
        return int(match.group(1))
    
    return None

@router.get("/service-status")
async def get_service_status() -> Dict[str, Any]:
    """
    Get status of all integrated services
    """
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # Check TFS service
        try:
            tfs_connected = await change_chain_service.tfs_service.test_connection()
            if tfs_connected:
                projects = await change_chain_service.tfs_service.get_projects()
                status["services"]["tfs"] = {
                    "status": "online",
                    "projects_count": len(projects),
                    "url": change_chain_service.tfs_service.base_url
                }
            else:
                status["services"]["tfs"] = {
                    "status": "offline",
                    "error": "Connection test failed"
                }
        except Exception as e:
            status["services"]["tfs"] = {
                "status": "offline",
                "error": str(e)
            }
        
        # Check OpenAI service
        # try:
        #     # Simple test request
        #     test_response = await change_chain_service.openai_service.client.chat.completions.create(
        #         model=change_chain_service.openai_service.model,
        #         messages=[{"role": "user", "content": "test"}],
        #         max_tokens=10
        #     )
        #     status["services"]["openai"] = {
        #         "status": "online",
        #         "model": change_chain_service.openai_service.model
        #     }
        # except Exception as e:
        #     status["services"]["openai"] = {
        #         "status": "offline",
        #         "error": str(e)
        #     }
        # 
        # Check Confluence service
        # try:
        #     from app.services.confluence_service import confluence_service
        #     # Test Confluence connection by getting spaces
        #     spaces = await confluence_service.get_spaces()
        #     status["services"]["confluence"] = {
        #         "status": "online",
        #         "spaces_count": len(spaces) if spaces else 0,
        #         "url": confluence_service.base_url
        #     }
        # except Exception as e:
        #     status["services"]["confluence"] = {
        #         "status": "offline",
        #         "error": str(e)
        #     }
        # 
        # Логирование результата в service_status.log
        try:
            with open("service_status.log", "a", encoding="utf-8") as logf:
                logf.write(f"[{datetime.now().isoformat()}] {status}\n")
        except Exception as log_err:
            logger.error(f"Не удалось записать лог service_status.log: {log_err}")
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting service status: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Функции для обработки User Stories
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

async def handle_user_story_creation_request_advanced(message: str) -> Dict[str, Any]:
    """
    Обрабатывает запрос на создание User Stories из Confluence или цепочки тикетов (для advanced endpoints)
    """
    try:
        logger.info(f"🎯 Обработка запроса на создание: {message}")
        
        # Проверяем, является ли запрос запросом на создание цепочки тикетов
        query_lower = message.lower()
        chain_keywords = ["цепочка", "цепочку", "связанных тикетов"]
        is_chain_request = any(keyword in query_lower for keyword in chain_keywords)
        
        if is_chain_request:
            logger.info("🔗 Обрабатываем запрос на создание цепочки тикетов")
            return await handle_change_chain_request_advanced(message)
        
        # Обрабатываем как обычный запрос на создание User Stories
        logger.info(f"🎯 Обработка запроса на создание User Stories: {message}")
        
        # Извлекаем URL из запроса
        confluence_url = extract_confluence_url(message)
        if not confluence_url:
            return {
                "success": False,
                "error": "Не удалось найти URL страницы Confluence в запросе",
                "message": "Ошибка: не найден URL страницы Confluence"
            }
        
        # Создаем User Stories через новый сервис
        logger.info(f"🔗 URL Confluence: {confluence_url}")
        creation_result = await user_story_creator_service.create_user_stories_from_confluence(
            confluence_url=confluence_url,
            user_confirmation=None  # Не подтверждаем автоматически - нужен предварительный просмотр
        )
        logger.info(f"📊 Результат создания: success={creation_result.get('success')}, needs_confirmation={creation_result.get('needs_confirmation')}")
        
        if creation_result["success"]:
            # Проверяем, нужен ли предварительный просмотр
            if creation_result.get("needs_confirmation"):
                # Возвращаем предварительный просмотр для подтверждения пользователем
                preview_data = creation_result["preview"]
                logger.info(f"🔍 Preview data keys: {list(preview_data.keys()) if preview_data else 'None'}")
                logger.info(f"🔍 User stories count: {len(preview_data.get('user_stories', [])) if preview_data else 'No preview_data'}")
                
                if not preview_data or 'user_stories' not in preview_data:
                    logger.error("❌ Preview data отсутствует или не содержит user_stories")
                    return {
                        "success": False,
                        "error": "Ошибка при формировании предварительного просмотра",
                        "message": "Ошибка при формировании предварительного просмотра User Stories"
                    }
                
                try:
                    logger.info("🔍 Начинаем формирование preview message")
                    preview_message = f"Найдено {len(preview_data['user_stories'])} User Stories для создания. Требуется подтверждение:\n\n"
                    logger.info(f"🔍 Базовое сообщение создано: {len(preview_message)} символов")
                    
                    for i, us in enumerate(preview_data["user_stories"], 1):
                        logger.info(f"🔍 Обрабатываем US {i}: {us.get('title', 'No title')}")
                        preview_message += f"{i}. **{us['title']}**\n"
                        preview_message += f"   Описание: {us['description'][:100]}...\n"
                        
                        # Показываем критерии приемки
                        if us.get('given_conditions') or us.get('when_actions') or us.get('then_results'):
                            preview_message += f"   Критерии приёмки (Дано/Когда/Тогда):\n"
                            if us.get('given_conditions'):
                                preview_message += f"     Дано: {us['given_conditions'][:80]}...\n"
                            if us.get('when_actions'):
                                preview_message += f"     Когда: {us['when_actions'][:80]}...\n"
                            if us.get('then_results'):
                                preview_message += f"     Тогда: {us['then_results'][:80]}...\n"
                        elif us.get('acceptance_criteria'):
                            preview_message += f"   Критерии приёмки:\n"
                            for j, criteria in enumerate(us['acceptance_criteria'], 1):
                                # Если это HTML таблица, показываем как таблицу
                                if criteria.startswith('<table'):
                                    preview_message += f"     {criteria[:200]}...\n"
                                else:
                                    preview_message += f"     {j}. {criteria[:60]}...\n"
                        else:
                            preview_message += f"   Критерии приёмки: не найдены\n"
                        
                        preview_message += "\n"
                        logger.info(f"🔍 US {i} обработан успешно")
                    
                    preview_message += "Для подтверждения создания отправьте: 'Да' или 'Создать'\n"
                    preview_message += "Для отмены отправьте: 'Нет' или 'Отмена'"
                    logger.info(f"✅ Preview message сформирован успешно: {len(preview_message)} символов")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при формировании preview message: {str(e)}")
                    logger.error(f"❌ Тип ошибки: {type(e).__name__}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    return {
                        "success": False,
                        "error": f"Ошибка при формировании предварительного просмотра: {str(e)}",
                        "message": f"Ошибка при формировании предварительного просмотра: {str(e)}"
                    }
                
                # Сохраняем состояние для последующего подтверждения
                request_id = f"us_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                pending_user_story_requests[request_id] = {
                    "confluence_url": confluence_url,
                    "preview_data": preview_data,
                    "created_at": datetime.now()
                }
                
                logger.info("🔍 Формируем финальный ответ")
                result = {
                    "success": True,
                    "message": preview_message,
                    "needs_confirmation": True,
                    "data": {
                        "confluence_url": confluence_url,
                        "preview": preview_data,
                        "request_id": request_id
                    }
                }
                logger.info(f"✅ Ответ сформирован успешно: success={result['success']}, needs_confirmation={result['needs_confirmation']}")
                return result
            else:
                # User Stories уже созданы (этот случай не должен происходить при user_confirmation=None)
                logger.warning("⚠️ User Stories созданы без подтверждения - это неожиданное поведение")
                logger.info(f"✅ Успешно создано {len(creation_result['created_stories'])} User Stories")
                return {
                    "success": True,
                    "message": f"✅ Создано {len(creation_result['created_stories'])} User Stories из статьи Confluence",
                    "data": {
                        "created_stories": creation_result["created_stories"],
                        "parent_ticket": creation_result["parent_ticket"],
                        "confluence_url": confluence_url
                    }
                }
        else:
            logger.error(f"❌ Создание User Stories не удалось: {creation_result.get('error', 'Неизвестная ошибка')}")
            return {
                "success": False,
                "error": creation_result.get("error", "Неизвестная ошибка"),
                "message": f"Ошибка при создании User Stories: {creation_result.get('error', 'Неизвестная ошибка')}"
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке запроса создания User Stories: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка при создании User Stories: {str(e)}"
        }

async def handle_change_chain_request_advanced(message: str) -> Dict[str, Any]:
    """
    Обрабатывает запрос на создание цепочки тикетов (для advanced endpoints)
    """
    try:
        logger.info(f"🔗 Обработка запроса на создание цепочки тикетов: {message}")
        
        # Импортируем сервис цепочки изменений
        from app.services.change_chain_service import change_chain_service
        
        # Проверяем подключение к TFS
        tfs_connected = await change_chain_service.tfs_service.test_connection()
        if not tfs_connected:
            return {
                "success": False,
                "error": "TFS сервис недоступен",
                "message": "TFS сервис недоступен. Проверьте настройки подключения."
            }
        
        # Парсим запрос
        parsed_data = await change_chain_service.parse_change_request(message)
        
        if not parsed_data.get("sourceBacklogId"):
            return {
                "success": False,
                "error": "Не найден номер тикета",
                "message": "Не удалось найти номер тикета в запросе. Укажите номер тикета в формате #123456"
            }
        
        # Создаем цепочку изменений
        chain_result = await change_chain_service.create_linked_change_chain(
            project=parsed_data["project"],
            request_title=parsed_data["requestTitle"],
            source_backlog_id=parsed_data["sourceBacklogId"],
            request_id=parsed_data.get("requestId")
        )
        
        if chain_result.get("success"):
            message_text = f"✅ Создана цепочка тикетов:\n\n"
            message_text += f"📋 **Epic**: {chain_result.get('Epic', {}).get('title', 'N/A')}\n"
            message_text += f"🔗 **Feature**: {chain_result.get('Feature', {}).get('title', 'N/A')}\n"
            message_text += f"📝 **Backlog Item**: {chain_result.get('Backlog Item', {}).get('title', 'N/A')}\n\n"
            message_text += f"🎯 **Исходный тикет**: #{parsed_data['sourceBacklogId']}\n"
            message_text += f"🔗 **Связь**: Backlog Item связан с исходным тикетом как дочерний элемент"
            
            logger.info(f"✅ Успешно создана цепочка тикетов для #{parsed_data['sourceBacklogId']}")
            return {
                "success": True,
                "message": message_text,
                "data": chain_result,
                "parsed_request": parsed_data
            }
        else:
            return {
                "success": False,
                "error": chain_result.get('error', 'Неизвестная ошибка'),
                "message": f"Ошибка при создании цепочки тикетов: {chain_result.get('error', 'Неизвестная ошибка')}"
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке запроса на цепочку тикетов: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка при создании цепочки тикетов: {str(e)}"
        }

def extract_confluence_url(query: str) -> str:
    """
    Извлекает URL страницы Confluence из запроса пользователя
    """
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
