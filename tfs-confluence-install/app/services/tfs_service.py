import requests
import json
import base64
import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.config.settings import settings
from app.models.request_models import UserStoryData, TaskData, ConfluenceArticle
from app.models.tfs_models import (
    WorkItemInfo, ProjectInfo, WorkItemCreateRequest, 
    WorkItemUpdateRequest, WorkItemLinkRequest, LinkType
)
from app.core.logging_config import log_tfs_operation

logger = logging.getLogger(__name__)

class TFSValidationError(Exception):
    """Ошибка валидации входных параметров"""
    pass

class TFSConnectionError(Exception):
    """Ошибка подключения к TFS/Azure DevOps"""
    pass

class TFSRetryableError(Exception):
    """Временная ошибка, которую можно повторить"""
    pass

class TFSService:
    """Сервис для работы с TFS/Azure DevOps API"""
    
    def __init__(self):
        self.base_url = settings.TFS_URL.rstrip('/')
        self.pat = settings.TFS_PAT_TOKEN or settings.TFS_PAT or settings.TFS_TOKEN
        self.project = settings.TFS_PROJECT
        self.organization = settings.TFS_ORGANIZATION
        
        # Создаем сессию с аутентификацией
        self.session = requests.Session()
        
        # Логируем информацию о токене для отладки
        logger.info(f"TFS Configuration:")
        logger.info(f"  - Base URL: {self.base_url}")
        logger.info(f"  - Project: {self.project}")
        logger.info(f"  - Organization: {self.organization}")
        logger.info(f"  - PAT Token: {'*' * 10 if self.pat else 'NOT SET'}")
        
        # Для TFS/Azure DevOps используем Basic auth с пустым username
        auth_string = f":{self.pat}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        logger.info(f"  - Auth String: :{self.pat[:10]}...")
        logger.info(f"  - Encoded Auth: {encoded_auth[:20]}...")
        
        self.session.headers.update({
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json-patch+json',
            'Accept': 'application/json'
        })
    
    async def test_connection(self) -> bool:
        """Test connection to TFS/Azure DevOps"""
        try:
            # Проверяем, что токен установлен
            if not self.pat:
                logger.error("❌ TFS PAT Token не установлен!")
                logger.error("   Проверьте переменные окружения: TFS_PAT_TOKEN, TFS_PAT или TFS_TOKEN")
                return False
            
            logger.info(f"🔑 Используется TFS PAT Token: {self.pat[:10]}...{self.pat[-4:]}")
            
            # Clean base URL and determine the correct format
            base_url_clean = self.base_url.rstrip('/')
            
            # Try different URL formats for different TFS versions
            test_urls = []
            
            # If URL already contains DefaultCollection, don't add it again
            if "/DefaultCollection" in base_url_clean:
                test_urls.extend([
                    f"{base_url_clean}/_apis/projects",
                    f"{base_url_clean}/_apis/projects?api-version=4.1"
                ])
            else:
                # Try different collection formats
                test_urls.extend([
                    f"{base_url_clean}/_apis/projects",  # Modern Azure DevOps
                    f"{base_url_clean}/DefaultCollection/_apis/projects",  # TFS 2017+
                    f"{base_url_clean}/tfs/DefaultCollection/_apis/projects",  # TFS 2015-2017
                    f"{base_url_clean}/_apis/projects?api-version=4.1",  # Older API version
                    f"{base_url_clean}/DefaultCollection/_apis/projects?api-version=4.1",  # TFS with older API
                    f"{base_url_clean}/tfs/DefaultCollection/_apis/projects?api-version=4.1",  # TFS 2015-2017 with older API
                ])
            
            logger.info(f"Testing TFS connection with base URL: {base_url_clean}")
            logger.info(f"Generated {len(test_urls)} test URLs")
            
            # Try different API versions for older TFS servers
            api_versions = ["4.1", "5.0", "5.1", "6.0"]
            
            for url in test_urls:
                # If URL already has api-version, use it; otherwise try different versions
                if "api-version=" in url:
                    params = {}
                else:
                    params = {"api-version": "4.1"}  # Start with older version
                
                try:
                    logger.info(f"Testing TFS URL: {url}")
                    response = self.session.get(url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ TFS connection successful with URL: {url}")
                        # Update base_url to the working format
                        if "/DefaultCollection/" in url:
                            self.base_url = url.split("/_apis/projects")[0]
                        elif "/tfs/DefaultCollection/" in url:
                            self.base_url = url.split("/_apis/projects")[0]
                        return True
                    elif response.status_code == 401:
                        logger.warning(f"401 Unauthorized for URL: {url}")
                        logger.warning(f"  Response headers: {dict(response.headers)}")
                        logger.warning(f"  Response text: {response.text[:200]}...")
                        continue
                    elif response.status_code == 404:
                        logger.warning(f"404 Not Found for URL: {url}")
                        continue
                    else:
                        logger.warning(f"Status {response.status_code} for URL: {url}")
                        continue
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request failed for URL {url}: {str(e)}")
                    continue
            
            logger.error("All TFS URL formats failed")
            return False
            
        except Exception as e:
            logger.error(f"TFS connection test failed: {str(e)}")
            return False
    
    async def get_projects(self) -> List[ProjectInfo]:
        """Получение списка проектов"""
        try:
            url = f"{self.base_url}/_apis/projects"
            params = {"api-version": "4.1"}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            projects = []
            
            for item in data.get("value", []):
                project = ProjectInfo(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                    url=item.get("url"),
                    state=item.get("state")
                )
                projects.append(project)
            
            logger.info(f"Получено {len(projects)} проектов")
            return projects
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении проектов: {str(e)}")
            raise TFSConnectionError(f"Ошибка подключения к TFS: {str(e)}")
    
    async def create_user_story(self, story_data: UserStoryData, confluence_url: str = None, team: str = None, parent_tfs_id: str = None) -> int:
        """
        Создание User Story с полным набором полей и связью с родительским тикетом
        """
        
        url = f"{self.base_url}/{self.project}/_apis/wit/workitems/$User Story"
        params = {"api-version": "4.1"}
        
        # Формируем описание User Story в простом формате
        full_description = self._format_user_story_description(story_data)
        
        # Определяем название - используем title (название US)
        if story_data.title and story_data.title.strip():
            title = story_data.title.strip()
        else:
            title = story_data.user_story_text.strip() if story_data.user_story_text else "User Story"
        
        # Определяем область и итерацию - используем проверенные значения
        if team and team.lower() == 'foxtrot':
            area_path = "Houston\\Foxtrot"
            iteration_path = "Houston\\Foxtrot"
        else:
            # Используем значения по умолчанию, которые точно существуют в TFS
            area_path = "Houston\\Foxtrot"  # Проверенное значение
            iteration_path = "Houston\\Foxtrot"  # Проверенное значение
        
        patch_document = [
            # Основные обязательные поля
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": full_description},
            {"op": "add", "path": "/fields/System.State", "value": "Новый"},
            
            # Область и итерация на основе команды
            {"op": "add", "path": "/fields/System.AreaPath", "value": area_path},
            {"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path},
            
            # Планирование
            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": story_data.priority},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Scheduling.StoryPoints", "value": story_data.story_points or 5},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.BusinessValue", "value": 20},
            
            # Комментарий будет добавлен отдельно через add_comment
        ]

        # Поле "Проект внедрения" (если задано и не пусто)
        if story_data.project and str(story_data.project).strip():
            patch_document.insert(
                7,  # вставляем после IterationPath/AreaPath блока
                {"op": "add", "path": "/fields/ST.ImplementationProject", "value": str(story_data.project).strip()}
            )
        
        # Критерии приемки в HTML формате
        if story_data.acceptance_criteria or story_data.given_conditions:
            acceptance_html = self._format_acceptance_criteria(story_data)
            patch_document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
                "value": acceptance_html
            })
        
        # Кастомные поля для команды (если есть в вашей конфигурации TFS)
        if story_data.tech_lead:
            patch_document.append({
                "op": "add",
                "path": "/fields/System.Tags", 
                "value": f"tech-lead:{story_data.tech_lead}; " + ("; ".join(story_data.tags) if story_data.tags else "")
            })
        
        try:
            logger.info(f"Создание User Story: {story_data.title}")
            logger.info(f"   📍 AreaPath: {area_path}")
            logger.info(f"   📅 IterationPath: {iteration_path}")
            
            response = self.session.post(
                url, 
                params=params,
                data=json.dumps(patch_document, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            
            result = response.json()
            story_id = result["id"]
            
            logger.info(f"✅ User Story создана с ID: {story_id}")
            logger.info(f"   📄 Заголовок: {title}")
            logger.info(f"   👤 Назначено: {story_data.assigned_to or 'Не назначено'}")
            logger.info(f"   🏷️ Проект: {story_data.project}")
            logger.info(f"   ⭐ Приоритет: {story_data.priority}")
            logger.info(f"   📊 Story Points: {story_data.story_points or 5}")
            
            # Логируем создание User Story
            log_tfs_operation(
                logger=logger,
                operation="User Story создана",
                work_item_id=story_id,
                details={
                    "title": title,
                    "assigned_to": story_data.assigned_to,
                    "project": story_data.project,
                    "priority": story_data.priority,
                    "story_points": story_data.story_points or 5,
                    "parent_id": story_data.parent_work_item_id
                }
            )
            
            # Создаем связь с родительским тикетом, если указан
            if parent_tfs_id:
                logger.info(f"🔗 Создание связи с родительским тикетом #{parent_tfs_id}")
                try:
                    parent_id = int(parent_tfs_id) if isinstance(parent_tfs_id, str) else parent_tfs_id
                    await self._create_parent_link(story_id, parent_id)
                    logger.info(f"✅ Связь с родительским тикетом #{parent_id} создана успешно")
                except Exception as e:
                    logger.error(f"❌ Ошибка создания связи с родительским тикетом #{parent_tfs_id}: {str(e)}")
            elif story_data.parent_work_item_id:
                logger.info(f"🔗 Создание связи с родительским тикетом #{story_data.parent_work_item_id}")
                try:
                    parent_id = int(story_data.parent_work_item_id) if isinstance(story_data.parent_work_item_id, str) else story_data.parent_work_item_id
                    await self._create_parent_link(story_id, parent_id)
                    logger.info(f"✅ Связь с родительским тикетом #{parent_id} создана успешно")
                except Exception as e:
                    logger.error(f"❌ Ошибка создания связи с родительским тикетом #{story_data.parent_work_item_id}: {str(e)}")
            
            # Добавление комментария о создании
            if confluence_url and confluence_url.strip() and confluence_url != "не указано":
                comment = f"Создан автоматически приложением TCA из статьи:<br><a href=\"{confluence_url}\" target=\"_blank\">{confluence_url}</a>"
            else:
                comment = "Создан автоматически приложением TCA"
            await self.add_comment(story_id, comment)
            
            return story_id
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при создании User Story: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                error_text = e.response.text
                logger.error(f"Детали ошибки: {error_text}")
                
                # Fallback №1: проблемы с Проектом внедрения (ST.ImplementationProject)
                if ("ST.ImplementationProject" in error_text) or ("Проект внедрения" in error_text):
                    logger.warning("🔄 Попытка коррекции поля 'Проект внедрения' (ST.ImplementationProject)")
                    try:
                        # Пытаемся получить корректное значение из родительского тикета
                        parent_id = None
                        if parent_tfs_id:
                            parent_id = int(parent_tfs_id) if isinstance(parent_tfs_id, str) else parent_tfs_id
                        elif getattr(story_data, 'parent_work_item_id', None):
                            parent_id = int(story_data.parent_work_item_id)

                        parent_impl_project = None
                        if parent_id:
                            try:
                                parent_wi = await self.get_work_item(parent_id)
                                if parent_wi and getattr(parent_wi, 'fields', None):
                                    parent_impl_project = parent_wi.fields.get('ST.ImplementationProject')
                                    logger.info(f"🔍 Получен 'Проект внедрения' из родителя #{parent_id}: {parent_impl_project}")
                            except Exception as pe:
                                logger.warning(f"⚠️ Не удалось получить родительский тикет #{parent_id} для подстановки проекта: {pe}")

                        # Строим fallback-патч: либо заменяем значение, либо удаляем поле
                        def _without_impl_project(doc):
                            return [op for op in doc if op.get('path') != '/fields/ST.ImplementationProject']

                        if parent_impl_project and str(parent_impl_project).strip():
                            # Заменяем/добавляем корректное значение
                            fallback_patch = _without_impl_project(patch_document)
                            fallback_patch.insert(
                                7,
                                {"op": "add", "path": "/fields/ST.ImplementationProject", "value": str(parent_impl_project).strip()}
                            )
                            logger.info("🔁 Повторная попытка с 'Проект внедрения' из родительского тикета")
                        else:
                            # Удаляем поле полностью и пробуем без него
                            fallback_patch = _without_impl_project(patch_document)
                            logger.info("🔁 Повторная попытка без поля 'Проект внедрения'")

                        response = self.session.post(
                            url,
                            params=params,
                            data=json.dumps(fallback_patch, ensure_ascii=False).encode('utf-8')
                        )
                        response.raise_for_status()

                        result = response.json()
                        story_id = result["id"]
                        logger.info(f"✅ User Story создана с ID: {story_id} после коррекции 'Проект внедрения'")

                        # Создаем связь с родительским тикетом, если указан
                        if parent_tfs_id:
                            try:
                                await self._create_parent_link(story_id, int(parent_tfs_id))
                            except Exception as link_e:
                                logger.error(f"❌ Ошибка создания связи с родительским тикетом #{parent_tfs_id}: {str(link_e)}")
                        elif getattr(story_data, 'parent_work_item_id', None):
                            try:
                                await self._create_parent_link(story_id, int(story_data.parent_work_item_id))
                            except Exception as link_e:
                                logger.error(f"❌ Ошибка создания связи с родительским тикетом #{story_data.parent_work_item_id}: {str(link_e)}")

                        # Добавление комментария о создании
                        if confluence_url and confluence_url.strip() and confluence_url != "не указано":
                            comment = f"Создан автоматически приложением TCA из статьи: {confluence_url}"
                        else:
                            comment = "Создан автоматически приложением TCA"
                        await self.add_comment(story_id, comment)

                        return story_id
                    except Exception as fix_e:
                        logger.error(f"❌ Коррекция 'Проект внедрения' не удалась: {fix_e}")
                
                # Если ошибка связана с AreaPath, пробуем создать без AreaPath и IterationPath
                if "AreaPath" in error_text or "IterationPath" in error_text:
                    logger.warning("🔄 Пробуем создать User Story без AreaPath и IterationPath")
                    try:
                        # Создаем новый patch_document без AreaPath и IterationPath
                        fallback_patch = [item for item in patch_document 
                                        if not (item.get("path") in ["/fields/System.AreaPath", "/fields/System.IterationPath"])]
                        
                        response = self.session.post(
                            url, 
                            params=params,
                            data=json.dumps(fallback_patch, ensure_ascii=False).encode('utf-8')
                        )
                        response.raise_for_status()
                        
                        result = response.json()
                        story_id = result["id"]
                        logger.info(f"✅ User Story создана с ID: {story_id} (без AreaPath/IterationPath)")
                        
                        # Создаем связь с родительским тикетом, если указан
                        if parent_tfs_id:
                            try:
                                await self._create_parent_link(story_id, int(parent_tfs_id))
                                logger.info(f"✅ Связь с родительским тикетом #{parent_tfs_id} создана успешно")
                            except Exception as link_e:
                                logger.error(f"❌ Ошибка создания связи с родительским тикетом #{parent_tfs_id}: {str(link_e)}")
                        elif story_data.parent_work_item_id:
                            try:
                                await self._create_parent_link(story_id, story_data.parent_work_item_id)
                                logger.info(f"✅ Связь с родительским тикетом #{story_data.parent_work_item_id} создана успешно")
                            except Exception as link_e:
                                logger.error(f"❌ Ошибка создания связи с родительским тикетом #{story_data.parent_work_item_id}: {str(link_e)}")
                        
                        # Добавление комментария о создании
                        if confluence_url and confluence_url.strip() and confluence_url != "не указано":
                            comment = f"Создан автоматически приложением TCA из статьи: {confluence_url}"
                        else:
                            comment = "Создан автоматически приложением TCA"
                        await self.add_comment(story_id, comment)
                        
                        return story_id
                        
                    except Exception as fallback_e:
                        logger.error(f"❌ Fallback создание также не удалось: {str(fallback_e)}")
                        raise Exception(f"Ошибка при создании User Story: {str(e)}")
            
            raise Exception(f"Ошибка при создании User Story: {str(e)}")

    def _format_user_story_description(self, story_data: UserStoryData) -> str:
        """Форматирование полного описания User Story в HTML"""
        
        html_parts = []
        
        # User Story в формате "Как..., хочу..., чтобы..." с правильным форматированием
        if story_data.user_story_text:
            # Убираем переносы строк перед словами "хочу" и "чтобы"
            text = story_data.user_story_text.replace('\n', ' ').replace('\r', ' ')
            # Убираем лишние пробелы
            text = ' '.join(text.split())
            
            # Выделяем "я, как", "хочу" и "чтобы" жирным и добавляем переносы строк
            text = text.replace(' я, как ', '<br><strong>я, как</strong> ')
            text = text.replace(' хочу ', '<br><strong>хочу</strong> ')
            text = text.replace(' чтобы ', '<br><strong>чтобы</strong> ')
            
            html_parts.append(f"<p>{text}</p>")
        
        # УБРАТЬ раздел "Детальные требования" - он не нужен в описании
        # Критерии приемки должны быть только в Microsoft.VSTS.Common.AcceptanceCriteria
        
        return "".join(html_parts)

    def _format_acceptance_criteria(self, story_data: UserStoryData) -> str:
        """Форматирование критериев приемки в HTML как таблица"""
        
        html_parts = []
        
        # Если given_conditions содержит HTML таблицу, используем её напрямую
        if story_data.given_conditions and story_data.given_conditions.startswith('<table'):
            return story_data.given_conditions
        
        # Если acceptance_criteria содержит HTML таблицы, используем их
        if story_data.acceptance_criteria:
            for criteria in story_data.acceptance_criteria:
                if isinstance(criteria, dict) and 'html' in criteria:
                    # Это HTML таблица из парсера
                    html_parts.append(criteria['html'])
                elif isinstance(criteria, str) and criteria.startswith('<table'):
                    # Это HTML таблица в виде строки
                    html_parts.append(criteria)
                else:
                    # Это обычный текст критерия
                    html_parts.append(f"<p>{criteria}</p>")
        
        # Если есть структурированные критерии, создаем таблицу
        elif story_data.given_conditions or story_data.when_actions or story_data.then_results:
            html_parts.append("<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse; width: 100%;'>")
            html_parts.append("<tr style='background-color: #f0f0f0;'>")
        html_parts.append("<th style='width: 20%; text-align: left; border: 1px solid #000;'>Дано</th>")
        html_parts.append("<th style='width: 20%; text-align: left; border: 1px solid #000;'>Когда</th>")
        html_parts.append("<th style='width: 60%; text-align: left; border: 1px solid #000;'>Тогда</th>")
            html_parts.append("</tr>")
            html_parts.append("<tr>")
            html_parts.append(f"<td style='border: 1px solid #000;'>{story_data.given_conditions or ''}</td>")
            html_parts.append(f"<td style='border: 1px solid #000;'>{story_data.when_actions or ''}</td>")
            html_parts.append(f"<td style='border: 1px solid #000;'>{story_data.then_results or ''}</td>")
            html_parts.append("</tr>")
            html_parts.append("</table>")
        
        return "".join(html_parts)

    async def _create_parent_link(self, child_id: int, parent_id: int):
        """
        Создание связи 'Родитель в backlog' между User Story и родительским тикетом
        """
        
        url = f"{self.base_url}/_apis/wit/workItems/{child_id}"
        params = {"api-version": "4.1"}
        
        # Patch для добавления связи с родительским элементом
        patch_document = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "ST.Backlog.LinkTypes.Hierarchy-Reverse",  # Родитель в backlog
                    "url": f"{self.base_url}/_apis/wit/workItems/{parent_id}",
                    "attributes": {
                        "comment": f"Связан с родительским тикетом #{parent_id} из Confluence"
                    }
                }
            }
        ]
        
        try:
            logger.info(f"🔗 Создание связи: User Story #{child_id} -> Родитель #{parent_id}")
            logger.info(f"   📋 URL: {url}")
            logger.info(f"   📋 Patch document: {json.dumps(patch_document, ensure_ascii=False, indent=2)}")
            
            response = self.session.patch(
                url,
                params=params,
                data=json.dumps(patch_document, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            
            logger.info(f"✅ Связь с родительским тикетом #{parent_id} создана")
            
        except requests.RequestException as e:
            logger.error(f"❌ Ошибка при создании связи с родительским тикетом #{parent_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   📋 Статус ответа: {e.response.status_code}")
                logger.error(f"   📋 Текст ответа: {e.response.text}")
            # НЕ прерываем выполнение, связь не критична для создания US
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при создании связи с родительским тикетом #{parent_id}: {str(e)}")
            # НЕ прерываем выполнение, связь не критична для создания US

    async def create_task(self, task_data: TaskData) -> int:
        """Создание Task"""
        try:
            url = f"{self.base_url}/{self.project}/_apis/wit/workitems/$Task"
            params = {"api-version": "4.1"}
            
            patch_document = [
                {"op": "add", "path": "/fields/System.Title", "value": task_data.title},
                {"op": "add", "path": "/fields/System.Description", "value": task_data.description or ""},
                {"op": "add", "path": "/fields/System.State", "value": "New"},
                {"op": "add", "path": "/fields/System.AreaPath", "value": f"{self.project}\\{task_data.project}"},
                {"op": "add", "path": "/fields/System.AssignedTo", "value": task_data.assigned_to or ""},
                {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": task_data.priority},
                {"op": "add", "path": "/fields/System.Tags", "value": "; ".join(task_data.tags) if task_data.tags else "automation"},
            ]
            
            if task_data.estimated_hours:
                patch_document.append({
                    "op": "add", 
                    "path": "/fields/Microsoft.VSTS.Scheduling.OriginalEstimate", 
                    "value": task_data.estimated_hours
                })
            
            response = self.session.post(
                url,
                params=params,
                data=json.dumps(patch_document, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            
            result = response.json()
            task_id = result["id"]
            
            logger.info(f"✅ Task создана с ID: {task_id}")
            logger.info(f"   📄 Заголовок: {task_data.title}")
            logger.info(f"   👤 Назначено: {task_data.assigned_to or 'Не назначено'}")
            logger.info(f"   🏷️ Проект: {task_data.project}")
            logger.info(f"   ⭐ Приоритет: {task_data.priority}")
            if task_data.estimated_hours:
                logger.info(f"   ⏱️ Оценка времени: {task_data.estimated_hours} часов")
            return task_id
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при создании Task: {str(e)}")
            raise Exception(f"Ошибка при создании Task: {str(e)}")

    async def get_work_item(self, work_item_id: int) -> WorkItemInfo:
        """Получение информации о Work Item"""
        try:
            url = f"{self.base_url}/_apis/wit/workitems/{work_item_id}"
            params = {"api-version": "4.1", "$expand": "relations"}
            
            logger.debug(f"Requesting work item {work_item_id} from URL: {url}")
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Проверяем content type
            content_type = response.headers.get('content-type', '')
            logger.debug(f"Response content type: {content_type}")
            
            # Проверяем, что ответ валидный JSON
            try:
                data = response.json()
                logger.debug(f"Parsed JSON data type: {type(data)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response for work item {work_item_id}: {e}")
                logger.error(f"Raw response text: {response.text[:500]}...")
                raise Exception(f"Некорректный ответ от TFS API")
            
            # Проверяем, что data - словарь
            if not isinstance(data, dict):
                logger.error(f"Expected dict, got {type(data)} for work item {work_item_id}")
                logger.error(f"Data content: {str(data)[:200]}...")
                raise Exception(f"Некорректный формат данных от TFS API")
            
            fields = data.get("fields", {})
            relations = data.get("relations", [])
            
            # Безопасное извлечение assigned_to
            assigned_to = None
            assigned_to_data = fields.get("System.AssignedTo")
            if isinstance(assigned_to_data, dict):
                assigned_to = assigned_to_data.get("displayName")
            elif isinstance(assigned_to_data, str):
                assigned_to = assigned_to_data
            
            # Безопасное извлечение created_by
            created_by = None
            created_by_data = fields.get("System.CreatedBy")
            if isinstance(created_by_data, dict):
                created_by = created_by_data.get("displayName")
            elif isinstance(created_by_data, str):
                created_by = created_by_data
            
            # Безопасное извлечение URL
            url_data = None
            links = data.get("_links", {})
            if isinstance(links, dict):
                html_data = links.get("html", {})
                if isinstance(html_data, dict):
                    url_data = html_data.get("href")
            
            # Извлекаем информацию о проекте
            project = fields.get("System.TeamProject", "Unknown")
            
            work_item = WorkItemInfo(
                id=data.get("id", work_item_id),
                work_item_type=fields.get("System.WorkItemType", ""),
                title=fields.get("System.Title", ""),
                state=fields.get("System.State", ""),
                assigned_to=assigned_to,
                created_by=created_by,
                created_date=fields.get("System.CreatedDate"),
                changed_date=fields.get("System.ChangedDate"),
                url=url_data,
                fields=fields,
                relations=relations,
                project=project
            )
            
            return work_item
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении Work Item {work_item_id}: {str(e)}")
            raise Exception(f"Ошибка при получении Work Item: {str(e)}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении Work Item {work_item_id}: {str(e)}")
            # Добавляем отладочную информацию
            if 'data' in locals():
                logger.error(f"Response data type: {type(data)}")
                logger.error(f"Response data: {str(data)[:200]}...")
            raise Exception(f"Ошибка обработки Work Item: {str(e)}")

    async def link_work_items(self, project_name: str, link_request: WorkItemLinkRequest) -> bool:
        """Связывание Work Items"""
        try:
            url = f"{self.base_url}/_apis/wit/workitems/{link_request.source_work_item_id}"
            params = {"api-version": "4.1"}
            
            patch_document = [
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": link_request.link_type.value,
                        "url": f"{self.base_url}/_apis/wit/workitems/{link_request.target_work_item_id}",
                        "attributes": {
                            "comment": link_request.comment or "Связано автоматически"
                        }
                    }
                }
            ]
            
            response = self.session.patch(
                url,
                params=params,
                data=json.dumps(patch_document, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            
            logger.info(f"✅ Связь создана: {link_request.source_work_item_id} -> {link_request.target_work_item_id}")
            logger.info(f"   🔗 Тип связи: {link_request.link_type.value}")
            logger.info(f"   💬 Комментарий: {link_request.comment or 'Связано автоматически'}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при создании связи: {str(e)}")
            return False

    async def create_parent_link(self, child_id: int, parent_id: int) -> bool:
        """Создание связи с родительским элементом"""
        return await self._create_parent_link(child_id, parent_id)

    async def create_work_item_link(self, source_work_item_id: int, target_work_item_id: int, link_type: str) -> bool:
        """Создание связи между Work Items"""
        try:
            logger.info(f"🔄 Создание связи {source_work_item_id} -> {target_work_item_id} ({link_type})")
            
            return await self.link_work_items("Houston", WorkItemLinkRequest(
                source_work_item_id=source_work_item_id,
                target_work_item_id=target_work_item_id,
                link_type=link_type
            ))
            
        except Exception as e:
            logger.error(f"❌ Ошибка при создании связи: {str(e)}")
            return False

    async def create_linked_tasks(self, parent_id: int, implementation_objects: List[str]) -> List[int]:
        """Создание связанных подзадач"""
        task_ids = []
        
        for obj_name in implementation_objects:
            task_data = TaskData(
                title=f"Доработка компонента: {obj_name}",
                description=f"Реализация изменений в компоненте {obj_name}",
                project=self.project,
                parent_work_item_id=parent_id,
                priority=2,
                tags=["subtask", "component-work"],
                estimated_hours=8
            )
            
            try:
                task_id = await self.create_task(task_data)
                task_ids.append(task_id)
                
                # Создаем связь с родительским элементом
                link_request = WorkItemLinkRequest(
                    source_work_item_id=task_id,
                    target_work_item_id=parent_id,
                    link_type=LinkType.CHILD,
                    comment=f"Подзадача для доработки {obj_name}"
                )
                await self.link_work_items(self.project, link_request)
                
            except Exception as e:
                logger.error(f"Ошибка при создании подзадачи для {obj_name}: {str(e)}")
        
        return task_ids

    async def create_work_item(self, project_name: str, work_item_request: WorkItemCreateRequest) -> WorkItemInfo:
        """Создание Work Item из запроса"""
        if work_item_request.work_item_type == WorkItemType.USER_STORY:
            story_data = UserStoryData(
                title=work_item_request.title,
                description=work_item_request.description,
                project=project_name,
                assigned_to=work_item_request.assigned_to,
                priority=work_item_request.priority,
                tags=work_item_request.tags
            )
            work_item_id = await self.create_user_story(story_data)
        elif work_item_request.work_item_type == WorkItemType.TASK:
            task_data = TaskData(
                title=work_item_request.title,
                description=work_item_request.description,
                project=project_name,
                assigned_to=work_item_request.assigned_to,
                priority=work_item_request.priority,
                tags=work_item_request.tags
            )
            work_item_id = await self.create_task(task_data)
        else:
            raise ValueError(f"Неподдерживаемый тип Work Item: {work_item_request.work_item_type}")
        
        return await self.get_work_item(work_item_id)

    async def update_work_item(self, work_item_id: int, project_name: str, update_request: WorkItemUpdateRequest) -> WorkItemInfo:
        """Обновление Work Item"""
        try:
            url = f"{self.base_url}/_apis/wit/workitems/{work_item_id}"
            params = {"api-version": "4.1"}
            
            patch_document = []
            
            if update_request.title:
                patch_document.append({"op": "replace", "path": "/fields/System.Title", "value": update_request.title})
            
            if update_request.description:
                patch_document.append({"op": "replace", "path": "/fields/System.Description", "value": update_request.description})
            
            if update_request.assigned_to:
                patch_document.append({"op": "replace", "path": "/fields/System.AssignedTo", "value": update_request.assigned_to})
            
            if update_request.state:
                patch_document.append({"op": "replace", "path": "/fields/System.State", "value": update_request.state.value})
            
            if update_request.priority:
                patch_document.append({"op": "replace", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": update_request.priority.value})
            
            if update_request.tags:
                patch_document.append({"op": "replace", "path": "/fields/System.Tags", "value": "; ".join(update_request.tags)})
            
            if not patch_document:
                raise ValueError("Нет полей для обновления")
            
            response = self.session.patch(
                url,
                params=params,
                data=json.dumps(patch_document, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            
            logger.info(f"✅ Work Item {work_item_id} обновлен")
            return await self.get_work_item(work_item_id)
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при обновлении Work Item {work_item_id}: {str(e)}")
            raise Exception(f"Ошибка при обновлении Work Item: {str(e)}")

    async def add_comment(self, work_item_id: int, comment: str) -> bool:
        """Добавление комментария к Work Item (через System.History для совместимости с TFS)."""
        try:
            logger.info(f"🔄 Добавление комментария к Work Item {work_item_id}")
            return await self.update_work_item_field(work_item_id, "/fields/System.History", comment)
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении комментария к Work Item {work_item_id}: {str(e)}")
            return False

    async def update_work_item_field(self, work_item_id: int, field_path: str, value: str) -> bool:
        """Обновление (или добавление) одного поля Work Item c JSON Patch.

        По умолчанию используем 'add'. Если сервер вернет ошибку о существующем значении,
        повторяем с 'replace'. Для System.History всегда 'add'.
        """
        try:
            url = f"{self.base_url}/_apis/wit/workitems/{work_item_id}"
            params = {"api-version": "4.1"}

            def _patch(op: str) -> requests.Response:
                doc = [{"op": op, "path": field_path, "value": value}]
                return self.session.patch(
                    url,
                    params=params,
                    data=json.dumps(doc, ensure_ascii=False).encode('utf-8')
                )

            # System.History всегда добавляем как новую запись
            if field_path == "/fields/System.History":
                resp = _patch("add")
                resp.raise_for_status()
                logger.info(f"✅ Поле {field_path} обновлено у Work Item {work_item_id}")
                return True

            # Сначала пробуем add
            resp = _patch("add")
            if resp.status_code >= 200 and resp.status_code < 300:
                logger.info(f"✅ Поле {field_path} обновлено у Work Item {work_item_id} (add)")
                return True

            # Иначе пробуем replace
            resp = _patch("replace")
            resp.raise_for_status()
            logger.info(f"✅ Поле {field_path} обновлено у Work Item {work_item_id} (replace)")
            return True

        except requests.RequestException as e:
            logger.error(f"❌ Ошибка обновления поля {field_path} у Work Item {work_item_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Детали ошибки: {e.response.text}")
            return False

    async def search_work_items(self, project_name: str, query: str = None, work_item_types: List[str] = None) -> List[WorkItemInfo]:
        """Поиск Work Items"""
        try:
            # Простой поиск по названию
            url = f"{self.base_url}/{project_name}/_apis/wit/wiql"
            params = {"api-version": "4.1"}
            
            # Базовая WIQL для получения всех Work Items
            wiql_query = f"SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State] FROM WorkItems WHERE [System.TeamProject] = '{project_name}'"
            
            if query:
                wiql_query += f" AND [System.Title] CONTAINS '{query}'"
            
            if work_item_types:
                types_str = "', '".join(work_item_types)
                wiql_query += f" AND [System.WorkItemType] IN ('{types_str}')"
            
            data = {"query": wiql_query}
            
            response = self.session.post(url, params=params, json=data)
            response.raise_for_status()
            
            result = response.json()
            work_items = []
            
            for item in result.get("workItems", []):
                work_item = await self.get_work_item(item["id"])
                work_items.append(work_item)
            
            logger.info(f"Найдено {len(work_items)} Work Items")
            return work_items
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при поиске Work Items: {str(e)}")
            raise Exception(f"Ошибка при поиске Work Items: {str(e)}")

# Глобальный экземпляр сервиса
tfs_service = TFSService()
