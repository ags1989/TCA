import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.services.tfs_service import TFSService
from app.services.openai_service import OpenAIService
from app.config.settings import settings
from app.core.logging_config import log_tfs_operation, log_user_action

logger = logging.getLogger(__name__)

class ChangeChainService:
    """Service for creating linked change chains in TFS"""
    
    def __init__(self):
        from app.services.tfs_service import tfs_service
        self.tfs_service = tfs_service
        self.openai_service = OpenAIService()
    
    async def parse_change_request(self, user_message: str) -> Dict[str, Any]:
        """
        Parse user's natural language request using simple regex patterns
        Fallback when OpenAI API is not available
        """
        import re
        
        logger.info(f"Parsing change request: {user_message}")
        
        # Default values
        parsed_data = {
            "project": "Houston",  # Default project
            "requestTitle": "Запрос на создание цепочки изменений",
            "sourceBacklogId": None,
            "requestId": f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
        
        try:
            # Extract work item ID (sourceBacklogId) - look for #number pattern
            id_match = re.search(r'#(\d+)', user_message)
            if id_match:
                parsed_data["sourceBacklogId"] = int(id_match.group(1))
                logger.info(f"Found sourceBacklogId: {parsed_data['sourceBacklogId']}")
            
            # Extract project name - look for "проект" keyword
            project_match = re.search(r'проект\s+(\w+)', user_message, re.IGNORECASE)
            if project_match:
                parsed_data["project"] = project_match.group(1)
                logger.info(f"Found project: {parsed_data['project']}")
            
            # Extract title - look for text after "цепочку" or "цепочка"
            title_match = re.search(r'цепочк[ау]\s+(?:связанных\s+тикетов\s+)?(?:для\s+)?(?:ЗЗЛ\s+#\d+\s+)?(.+?)(?:\s+проект|\s+#\d+|$)', user_message, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                if title and not title.lower().startswith('для'):
                    parsed_data["requestTitle"] = title
                    logger.info(f"Found title: {parsed_data['requestTitle']}")
            
            # If no specific title found, use a generic one based on work item ID
            if parsed_data["sourceBacklogId"] and parsed_data["requestTitle"] == "Запрос на создание цепочки изменений":
                parsed_data["requestTitle"] = f"Цепочка изменений для элемента #{parsed_data['sourceBacklogId']}"
            
            # Validate required fields
            self._validate_parsed_data(parsed_data)
            
            logger.info(f"Parsed data: {parsed_data}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing change request: {e}")
            raise Exception(f"Ошибка при обработке запроса: {str(e)}")

    def _validate_parsed_data(self, parsed_data: Dict[str, Any]) -> None:
        """Валидация распарсенных данных"""
        import re
        
        # Валидация ID
        if not parsed_data.get("sourceBacklogId"):
            raise ValueError("Не удалось найти ID рабочего элемента в запросе. Используйте формат: #12345")
        
        if not isinstance(parsed_data["sourceBacklogId"], int) or parsed_data["sourceBacklogId"] <= 0:
            raise ValueError("ID рабочего элемента должен быть положительным числом")
        
        # Валидация проекта
        if not parsed_data.get("project"):
            raise ValueError("Не указан проект")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', parsed_data["project"]):
            raise ValueError("Название проекта содержит недопустимые символы")
        
        # Валидация заголовка
        if not parsed_data.get("requestTitle"):
            raise ValueError("Не указан заголовок запроса")
        
        if len(parsed_data["requestTitle"]) > 255:
            raise ValueError("Заголовок слишком длинный (максимум 255 символов)")
        
        if len(parsed_data["requestTitle"]) < 3:
            raise ValueError("Заголовок слишком короткий (минимум 3 символа)")
        
        # Проверка на SQL injection и XSS
        dangerous_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
        for pattern in dangerous_patterns:
            if pattern.lower() in parsed_data["requestTitle"].lower():
                raise ValueError("Заголовок содержит потенциально опасные символы")

    async def _get_source_ticket_data(self, source_backlog_id: int) -> Dict[str, Any]:
        """Get title and field values from source ticket"""
        try:
            url = f"{self.tfs_service.base_url}/Houston/_apis/wit/workitems/{source_backlog_id}?api-version=4.1&$expand=all"
            response = self.tfs_service.session.get(url)
            
            if response.status_code == 200:
                ticket_data = response.json()
                fields = ticket_data['fields']
                
                return {
                    "title": fields.get("System.Title", f"Элемент #{source_backlog_id}"),
                    "fields": {
                        "implementation_project": fields.get("ST.ImplementationProject", "Mars"),
                        "mvp": fields.get("ST.MVP", "Нет"),
                        # Используем правильные значения для цепочки изменений (Houston\Foxtrot)
                        "iteration_id": 2781,  # Houston\Foxtrot
                        "area_id": 2780,       # Houston\Foxtrot
                        "iteration_path": "Houston\\Foxtrot",
                        "area_path": "Houston\\Foxtrot",
                        # Для BI используем итерацию с Upstream
                        "bi_iteration_id": 4047,  # Houston\Foxtrot\F25-Upstream
                        "bi_iteration_path": "Houston\\Foxtrot\\F25-Upstream",
                        "priority": fields.get("Microsoft.VSTS.Common.Priority", 2),
                        "value_area": fields.get("Microsoft.VSTS.Common.ValueArea", "Бизнес")
                    }
                }
            else:
                logger.warning(f"Could not get source ticket data: {response.status_code}")
                return {
                    "title": f"Элемент #{source_backlog_id}",
                    "fields": {
                        "implementation_project": "Mars",
                        "mvp": "Нет",
                        "iteration_id": 2781,
                        "area_id": 2780,
                        "iteration_path": "Houston\\Foxtrot",
                        "area_path": "Houston\\Foxtrot",
                        "priority": 2,
                        "value_area": "Бизнес"
                    }
                }
        except Exception as e:
            logger.warning(f"Error getting source ticket data: {e}")
            return {
                "title": f"Элемент #{source_backlog_id}",
                "fields": {
                    "implementation_project": "Mars",
                    "mvp": "Нет",
                    "iteration_id": 2781,
                    "area_id": 2780,
                    "iteration_path": "Houston\\Foxtrot",
                    "area_path": "Houston\\Foxtrot",
                    "priority": 2,
                    "value_area": "Бизнес"
                }
            }

    async def create_linked_change_chain(
        self, 
        project: str, 
        request_title: str, 
        source_backlog_id: int,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create linked change chain: Epic -> Feature -> Product Backlog Item
        Product Backlog Item is linked as child to source_backlog_id
        """
        
        try:
            logger.info(f"Creating change chain for project: {project}, title: {request_title}, source: {source_backlog_id}")
            
            # Логируем начало создания цепочки изменений
            log_user_action(
                logger=logger,
                action="Создание цепочки изменений",
                details={
                    "project": project,
                    "title": request_title,
                    "source_ticket_id": source_backlog_id,
                    "request_id": request_id
                }
            )
            
            # Get source ticket fields and title
            source_data = await self._get_source_ticket_data(source_backlog_id)
            source_title = source_data["title"]
            source_fields = source_data["fields"]
            logger.info(f"Source ticket title: {source_title}")
            logger.info(f"Source ticket fields: {source_fields}")
            
            # 1. Create Epic with source title
            epic_id = await self._create_work_item(
                project=project,
                work_item_type="Epic",
                title=source_title,
                description=f"Epic для {source_title}",
                request_id=request_id,
                source_fields=source_fields,
                use_implementation_project=False
            )
            
            # 2. Create Feature with source title
            feature_id = await self._create_work_item(
                project=project,
                work_item_type="Feature",
                title=source_title,
                description=f"Feature для {source_title}",
                request_id=request_id,
                source_fields=source_fields,
                use_implementation_project=False
            )
            
            # 3. Create Backlog Item with HLD prefix and implementation project
            backlog_item_id = await self._create_work_item(
                project=project,
                work_item_type="Backlog Item",
                title=f"HLD {source_title}",
                description=f"HLD для {source_title}",
                request_id=request_id,
                source_fields=source_fields,
                use_implementation_project=True
            )
            
            # 4. Create links
            # Epic -> Feature
            await self._create_link(epic_id, feature_id, "System.LinkTypes.Hierarchy-Forward")
            
            # Feature -> BacklogItem
            await self._create_link(feature_id, backlog_item_id, "System.LinkTypes.Hierarchy-Forward")
            
            # BacklogItem -> Source (as child) - используем ST.Backlog.LinkTypes.Hierarchy-Reverse
            # Исправлено: backlog_item_id должен ссылаться на source_backlog_id как на родителя
            await self._create_link(backlog_item_id, source_backlog_id, "ST.Backlog.LinkTypes.Hierarchy-Reverse")
            
            # Формируем правильный URL для TFS (используем defaultcollection с маленькой буквы)
            base_tfs_url = self.tfs_service.base_url.replace('/_apis', '').replace('DefaultCollection', 'defaultcollection')
            
            result = {
                "Epic": {
                    "id": epic_id,
                    "title": source_title,
                    "url": f"{base_tfs_url}/{project}/_workitems/edit/{epic_id}"
                },
                "Feature": {
                    "id": feature_id,
                    "title": source_title,
                    "url": f"{base_tfs_url}/{project}/_workitems/edit/{feature_id}"
                },
                "BacklogItem": {
                    "id": backlog_item_id,
                    "title": f"HLD {source_title}",
                    "parent": source_backlog_id,
                    "url": f"{base_tfs_url}/{project}/_workitems/edit/{backlog_item_id}"
                }
            }
            
            logger.info(f"✅ Change chain created successfully: {result}")
            
            # Логируем успешное создание цепочки
            log_tfs_operation(
                logger=logger,
                operation="Цепочка изменений создана успешно",
                details={
                    "epic_id": epic_id,
                    "feature_id": feature_id,
                    "backlog_item_id": backlog_item_id,
                    "source_ticket_id": source_backlog_id,
                    "project": project,
                    "links_created": 3
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating change chain: {str(e)}")
            raise Exception(f"Ошибка при создании цепочки изменений: {str(e)}")

    async def _create_work_item(
        self, 
        project: str, 
        work_item_type: str, 
        title: str, 
        description: str,
        request_id: Optional[str] = None,
        source_fields: Optional[Dict[str, Any]] = None,
        use_implementation_project: bool = False
    ) -> int:
        """Create a work item in TFS"""
        
        url = f"{self.tfs_service.base_url}/{project}/_apis/wit/workitems/${work_item_type}"
        params = {"api-version": "4.1"}
        
        # Use source fields if provided, otherwise use defaults
        if source_fields:
            # Для Backlog Item используем специальные значения с Upstream
            if work_item_type == "Backlog Item":
                iteration_id = source_fields.get("bi_iteration_id", 4047)
                iteration_path = source_fields.get("bi_iteration_path", "Houston\\Foxtrot\\F25-Upstream")
            else:
                iteration_id = source_fields.get("iteration_id", 2781)
                iteration_path = source_fields.get("iteration_path", "Houston\\Foxtrot")
            
            area_id = source_fields.get("area_id", 2780)
            area_path = source_fields.get("area_path", "Houston\\Foxtrot")
            priority = source_fields.get("priority", 2)
            value_area = source_fields.get("value_area", "Бизнес")
            implementation_project = source_fields.get("implementation_project", "Mars")
            mvp = source_fields.get("mvp", "Нет")
        else:
            if work_item_type == "Backlog Item":
                iteration_id = 4047
                iteration_path = "Houston\\Foxtrot\\F25-Upstream"
            else:
                iteration_id = 2781
                iteration_path = "Houston\\Foxtrot"
            
            area_id = 2780
            area_path = "Houston\\Foxtrot"
            priority = 2
            value_area = "Бизнес"
            implementation_project = "Mars"
            mvp = "Нет"
        
        # Базовые поля для всех типов work items
        patch_document = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": description},
            {"op": "add", "path": "/fields/System.State", "value": "Новый"},
            {"op": "add", "path": "/fields/System.AreaPath", "value": area_path},
            {"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path},
            {"op": "add", "path": "/fields/System.IterationId", "value": iteration_id},
            {"op": "add", "path": "/fields/System.AreaId", "value": area_id},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.ValueArea", "value": value_area},
        ]
        
        # Дополнительные поля в зависимости от типа work item
        if work_item_type == "Feature":
            # Feature требует ST.MVP
            patch_document.append({"op": "add", "path": "/fields/ST.MVP", "value": mvp})
        elif work_item_type == "Backlog Item":
            # Backlog Item требует ST.ImplementationProject и ST.MVP
            patch_document.extend([
                {"op": "add", "path": "/fields/ST.MVP", "value": mvp},
            ])
            # Добавляем ST.ImplementationProject только если use_implementation_project=True
            if use_implementation_project:
                patch_document.append({"op": "add", "path": "/fields/ST.ImplementationProject", "value": implementation_project})
        
        # Add comment to history
        history_comment = "создано автоматически by TSA"
        if request_id:
            history_comment += f" (Request ID: {request_id})"
        
        patch_document.append({
            "op": "add", 
            "path": "/fields/System.History", 
            "value": history_comment
        })
        
        try:
            response = self.tfs_service.session.post(
                url,
                params=params,
                headers={'Content-Type': 'application/json-patch+json'},
                data=json.dumps(patch_document, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            
            result = response.json()
            work_item_id = result["id"]
            
            logger.info(f"✅ Created {work_item_type} with ID: {work_item_id}")
            logger.info(f"   📄 Title: {title}")
            logger.info(f"   🏷️ Project: {project}")
            logger.info(f"   📍 Area Path: {area_path}")
            logger.info(f"   🔄 Iteration Path: {iteration_path}")
            logger.info(f"   ⭐ Priority: {priority}")
            logger.info(f"   💼 Value Area: {value_area}")
            if work_item_type == "Backlog Item" and use_implementation_project:
                logger.info(f"   🏢 Implementation Project: {implementation_project}")
            if work_item_type in ["Feature", "Backlog Item"]:
                logger.info(f"   🎯 MVP: {mvp}")
            return work_item_id
            
        except Exception as e:
            logger.error(f"Error creating {work_item_type}: {str(e)}")
            raise Exception(f"Ошибка при создании {work_item_type}: {str(e)}")

    async def _create_link(self, source_id: int, target_id: int, link_type: str):
        """Create a link between work items"""
        
        url = f"{self.tfs_service.base_url}/_apis/wit/workitems/{source_id}"
        params = {"api-version": "4.1"}
        
        patch_document = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": link_type,
                    "url": f"{self.tfs_service.base_url}/_apis/wit/workitems/{target_id}",
                    "attributes": {
                        "comment": f"Связано автоматически через Change Chain Service"
                    }
                }
            }
        ]
        
        try:
            response = self.tfs_service.session.patch(
                url,
                params=params,
                headers={'Content-Type': 'application/json-patch+json'},
                data=json.dumps(patch_document, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            
            logger.info(f"✅ Link created: {source_id} -> {target_id} ({link_type})")
            logger.info(f"   🔗 Source ID: {source_id}")
            logger.info(f"   🎯 Target ID: {target_id}")
            logger.info(f"   📋 Link Type: {link_type}")
            logger.info(f"   💬 Comment: Связано автоматически через Change Chain Service")
            
        except Exception as e:
            logger.error(f"Error creating link {source_id} -> {target_id}: {str(e)}")
            # Для критических связей (Epic->Feature, Feature->BI) - проброс ошибки
            if link_type in ["System.LinkTypes.Hierarchy-Forward"]:
                raise Exception(f"Критическая ошибка создания связи: {str(e)}")
            # Для необязательных связей - только логирование
            else:
                logger.warning(f"Необязательная связь не создана: {str(e)}")

# Global instance
change_chain_service = ChangeChainService()
