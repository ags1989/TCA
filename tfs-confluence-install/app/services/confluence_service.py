import requests
import base64
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from app.config.settings import settings
from app.models.request_models import ConfluenceArticle
from app.models.confluence_models import (
    ConfluencePageRequest, ConfluencePageResponse, ConfluenceTemplate,
    ConfluenceSpace, ConfluencePageUpdateRequest, ConfluenceCommentRequest,
    ConfluenceSearchRequest, ConfluencePageType, ConfluenceRepresentation
)
from app.core.logging_config import log_confluence_operation

logger = logging.getLogger(__name__)

class ConfluenceService:
    """Сервис для работы с Confluence API"""
    
    def __init__(self):
        self.base_url = settings.CONFLUENCE_URL.rstrip('/')
        self.auth = self._get_auth_headers()
        self.session = requests.Session()
        self.session.headers.update(self.auth)
    
    def _get_auth_headers(self) -> dict:
        """Создаем заголовки для аутентификации"""
        token = settings.CONFLUENCE_TOKEN
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def get_spaces(self) -> List[dict]:
        """Get list of Confluence spaces"""
        try:
            url = f"{self.base_url}/rest/api/space"
            params = {"limit": 100}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("results", [])
            
        except Exception as e:
            logger.error(f"Error getting Confluence spaces: {str(e)}")
            return []
    
    def _clean_html_content(self, html_content: str) -> str:
        """Очистка HTML контента от тегов"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Убираем скрипты и стили
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator='\n', strip=True)
        except Exception:
            return html_content
    
    async def search_articles(self, keywords: str) -> List[ConfluenceArticle]:
        """
        Поиск статей по ключевым словам
        
        Пример: search_articles("tdd итоговое окно")
        """
        
        search_url = f"{self.base_url}/rest/api/content"
        
        # Параметры поиска
        params = {
            "title": keywords,  # Поиск в названии
            "expand": "body.storage,space",
            "limit": 10,
            "type": "page"
        }
        
        try:
            logger.info(f"Поиск статей в Confluence по запросу: {keywords}")
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            logger.info(f"Найдено статей: {len(data.get('results', []))}")
            
            for item in data.get("results", []):
                # Извлекаем содержимое
                content_html = ""
                if "body" in item and "storage" in item["body"]:
                    content_html = item["body"]["storage"]["value"]
                
                # Очищаем HTML
                clean_content = self._clean_html_content(content_html)
                
                article = ConfluenceArticle(
                    id=item["id"],
                    title=item["title"],
                    content=clean_content,
                    space_key=item.get("space", {}).get("key", "")
                )
                articles.append(article)
                logger.info(f"Добавлена статья: {article.title} (ID: {article.id})")
            
            # Если не найдено по точному названию, попробуем поиск по содержимому
            if not articles:
                articles = await self._search_by_content(keywords)
            
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при поиске в Confluence: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Детали ошибки: {e.response.text}")
            raise Exception(f"Ошибка при поиске в Confluence: {str(e)}")
    
    async def _search_by_content(self, keywords: str) -> List[ConfluenceArticle]:
        """Поиск по содержимому статей"""
        search_url = f"{self.base_url}/rest/api/search"
        
        # CQL запрос для поиска по содержимому
        cql_query = f'text ~ "{keywords}" and type=page'
        
        params = {
            "cql": cql_query,
            "limit": 10,
            "expand": "content.body.storage,content.space"
        }
        
        try:
            logger.info(f"Поиск по содержимому: {cql_query}")
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for item in data.get("results", []):
                content = item.get("content", {})
                
                content_html = ""
                if "body" in content and "storage" in content["body"]:
                    content_html = content["body"]["storage"]["value"]
                
                clean_content = self._clean_html_content(content_html)
                
                article = ConfluenceArticle(
                    id=content["id"],
                    title=content["title"],
                    content=clean_content,
                    space_key=content.get("space", {}).get("key", "")
                )
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Ошибка при поиске по содержимому: {str(e)}")
            return []
    
    async def get_article_by_id(self, article_id: str) -> Optional[ConfluenceArticle]:
        """
        Получение статьи по ID
        
        Пример: get_article_by_id("123456")
        """
        
        url = f"{self.base_url}/rest/api/content/{article_id}"
        params = {"expand": "body.storage,space"}
        
        try:
            logger.info(f"Получение статьи по ID: {article_id}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            content_html = ""
            if "body" in data and "storage" in data["body"]:
                content_html = data["body"]["storage"]["value"]
            
            article = ConfluenceArticle(
                id=data["id"],
                title=data["title"],
                content=content_html,
                space_key=data.get("space", {}).get("key", "")
            )
            
            logger.info(f"Получена статья: {article.title}")
            return article
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении статьи: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """Тестирование подключения к Confluence API"""
        try:
            test_url = f"{self.base_url}/rest/api/space"
            response = self.session.get(test_url, params={"limit": 1})
            response.raise_for_status()
            logger.info("✅ Подключение к Confluence успешно")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Confluence: {str(e)}")
            return False

    async def create_page(self, title: str, content: str, space_key: str = "DEV", parent_id: str = None) -> dict:
        """
        Создание новой страницы в Confluence
        
        Args:
            title: Заголовок страницы
            content: Содержимое страницы (HTML или Markdown)
            space_key: Ключ пространства (по умолчанию "DEV")
            parent_id: ID родительской страницы (опционально)
        
        Returns:
            dict: Информация о созданной странице
        """
        try:
            logger.info(f"🔄 Создание страницы в Confluence: '{title}' в пространстве '{space_key}'")
            
            url = f"{self.base_url}/rest/api/content"
            
            # Подготавливаем данные для создания страницы
            page_data = {
                "type": "page",
                "title": title,
                "space": {"key": space_key},
                "body": {
                    "storage": {
                        "value": content,
                        "representation": "storage"  # HTML формат
                    }
                }
            }
            
            # Добавляем родительскую страницу, если указана
            if parent_id:
                page_data["ancestors"] = [{"id": parent_id}]
                logger.info(f"📄 Страница будет создана как дочерняя для страницы ID: {parent_id}")
            
            response = self.session.post(url, json=page_data)
            response.raise_for_status()
            
            result = response.json()
            page_id = result["id"]
            page_url = f"{self.base_url}/pages/viewpage.action?pageId={page_id}"
            
            logger.info(f"✅ Страница создана успешно:")
            logger.info(f"   📄 ID: {page_id}")
            logger.info(f"   📄 Заголовок: {title}")
            logger.info(f"   📄 Пространство: {space_key}")
            logger.info(f"   🔗 URL: {page_url}")
            
            # Логируем создание страницы
            log_confluence_operation(
                logger=logger,
                operation="Страница создана",
                page_id=page_id,
                details={
                    "title": title,
                    "space_key": space_key,
                    "parent_id": parent_id,
                    "url": page_url,
                    "version": result.get("version", {}).get("number", 1)
                }
            )
            
            return {
                "id": page_id,
                "title": title,
                "url": page_url,
                "space_key": space_key,
                "parent_id": parent_id,
                "created_at": result.get("version", {}).get("when", ""),
                "version": result.get("version", {}).get("number", 1)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при создании страницы '{title}': {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   Детали ошибки: {e.response.text}")
            raise Exception(f"Ошибка при создании страницы в Confluence: {str(e)}")

    async def update_page(self, page_id: str, title: str = None, content: str = None) -> dict:
        """
        Обновление существующей страницы в Confluence
        
        Args:
            page_id: ID страницы для обновления
            title: Новый заголовок (опционально)
            content: Новое содержимое (опционально)
        
        Returns:
            dict: Информация об обновленной странице
        """
        try:
            logger.info(f"🔄 Обновление страницы в Confluence: ID {page_id}")
            
            # Сначала получаем текущую версию страницы
            get_url = f"{self.base_url}/rest/api/content/{page_id}"
            get_response = self.session.get(get_url, params={"expand": "version"})
            get_response.raise_for_status()
            
            current_data = get_response.json()
            current_version = current_data["version"]["number"]
            
            # Подготавливаем данные для обновления
            update_data = {
                "version": {"number": current_version + 1}
            }
            
            if title:
                update_data["title"] = title
                logger.info(f"   📝 Обновление заголовка на: '{title}'")
            
            if content:
                update_data["body"] = {
                    "storage": {
                        "value": content,
                        "representation": "storage"
                    }
                }
                logger.info(f"   📝 Обновление содержимого")
            
            # Выполняем обновление
            update_url = f"{self.base_url}/rest/api/content/{page_id}"
            response = self.session.put(update_url, json=update_data)
            response.raise_for_status()
            
            result = response.json()
            page_url = f"{self.base_url}/pages/viewpage.action?pageId={page_id}"
            
            logger.info(f"✅ Страница обновлена успешно:")
            logger.info(f"   📄 ID: {page_id}")
            logger.info(f"   📄 Версия: {result.get('version', {}).get('number', 'N/A')}")
            logger.info(f"   🔗 URL: {page_url}")
            
            return {
                "id": page_id,
                "title": result.get("title", title),
                "url": page_url,
                "version": result.get("version", {}).get("number", current_version + 1),
                "updated_at": result.get("version", {}).get("when", "")
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении страницы ID {page_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   Детали ошибки: {e.response.text}")
            raise Exception(f"Ошибка при обновлении страницы в Confluence: {str(e)}")

    async def add_comment(self, page_id: str, comment: str) -> dict:
        """
        Добавление комментария к странице в Confluence
        
        Args:
            page_id: ID страницы
            comment: Текст комментария
        
        Returns:
            dict: Информация о созданном комментарии
        """
        try:
            logger.info(f"🔄 Добавление комментария к странице ID: {page_id}")
            
            url = f"{self.base_url}/rest/api/content"
            
            comment_data = {
                "type": "comment",
                "container": {
                    "id": page_id,
                    "type": "page"
                },
                "body": {
                    "storage": {
                        "value": comment,
                        "representation": "storage"
                    }
                }
            }
            
            response = self.session.post(url, json=comment_data)
            response.raise_for_status()
            
            result = response.json()
            comment_id = result["id"]
            
            logger.info(f"✅ Комментарий добавлен успешно:")
            logger.info(f"   💬 ID комментария: {comment_id}")
            logger.info(f"   📄 К странице: {page_id}")
            logger.info(f"   📝 Текст: {comment[:50]}...")
            
            return {
                "id": comment_id,
                "page_id": page_id,
                "comment": comment,
                "created_at": result.get("version", {}).get("when", "")
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении комментария к странице ID {page_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   Детали ошибки: {e.response.text}")
            raise Exception(f"Ошибка при добавлении комментария в Confluence: {str(e)}")

    async def create_page_from_request(self, request: ConfluencePageRequest) -> ConfluencePageResponse:
        """
        Создание страницы в Confluence из запроса
        
        Args:
            request: Запрос на создание страницы
        
        Returns:
            ConfluencePageResponse: Результат создания страницы
        """
        try:
            logger.info(f"🔄 Создание страницы в Confluence из запроса: '{request.title}'")
            
            # Если указан шаблон, получаем его содержимое
            if request.template_id:
                template = await self.get_template(request.template_id)
                if template:
                    content = await self._apply_template(template, request.template_data or {})
                else:
                    content = request.content
            else:
                content = request.content
            
            # Создаем страницу
            result = await self.create_page(
                title=request.title,
                content=content,
                space_key=request.space_key,
                parent_id=request.parent_id
            )
            
            # Добавляем метки, если указаны
            if request.labels:
                await self._add_labels_to_page(result["id"], request.labels)
            
            return ConfluencePageResponse(
                success=True,
                page_id=result["id"],
                title=result["title"],
                url=result["url"],
                space_key=result["space_key"],
                version=result["version"],
                created_at=result["created_at"]
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка при создании страницы из запроса: {str(e)}")
            return ConfluencePageResponse(
                success=False,
                error=str(e)
            )

    async def get_templates(self, space_key: str = None) -> List[ConfluenceTemplate]:
        """
        Получение списка доступных шаблонов
        
        Args:
            space_key: Ключ пространства для фильтрации шаблонов
        
        Returns:
            List[ConfluenceTemplate]: Список шаблонов
        """
        try:
            logger.info(f"🔄 Получение списка шаблонов Confluence")
            
            url = f"{self.base_url}/rest/api/template"
            params = {"limit": 100}
            
            if space_key:
                params["spaceKey"] = space_key
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            templates = []
            
            for item in data.get("results", []):
                template = ConfluenceTemplate(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                    space_key=item.get("space", {}).get("key", ""),
                    content=item.get("body", {}).get("storage", {}).get("value"),
                    variables=item.get("variables", [])
                )
                templates.append(template)
            
            logger.info(f"✅ Получено {len(templates)} шаблонов")
            return templates
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении шаблонов: {str(e)}")
            return []

    async def get_template(self, template_id: str) -> Optional[ConfluenceTemplate]:
        """
        Получение конкретного шаблона по ID
        
        Args:
            template_id: ID шаблона
        
        Returns:
            ConfluenceTemplate: Шаблон или None
        """
        try:
            logger.info(f"🔄 Получение шаблона ID: {template_id}")
            
            url = f"{self.base_url}/rest/api/template/{template_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            template = ConfluenceTemplate(
                id=data["id"],
                name=data["name"],
                description=data.get("description"),
                space_key=data.get("space", {}).get("key", ""),
                content=data.get("body", {}).get("storage", {}).get("value"),
                variables=data.get("variables", [])
            )
            
            logger.info(f"✅ Шаблон получен: {template.name}")
            return template
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении шаблона {template_id}: {str(e)}")
            return None

    async def get_spaces(self) -> List[ConfluenceSpace]:
        """
        Получение списка пространств Confluence
        
        Returns:
            List[ConfluenceSpace]: Список пространств
        """
        try:
            logger.info(f"🔄 Получение списка пространств Confluence")
            
            url = f"{self.base_url}/rest/api/space"
            params = {"limit": 100}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            spaces = []
            
            for item in data.get("results", []):
                space = ConfluenceSpace(
                    key=item["key"],
                    name=item["name"],
                    description=item.get("description"),
                    url=item.get("_links", {}).get("webui")
                )
                spaces.append(space)
            
            logger.info(f"✅ Получено {len(spaces)} пространств")
            return spaces
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении пространств: {str(e)}")
            return []

    async def search_pages(self, request: ConfluenceSearchRequest) -> List[ConfluenceArticle]:
        """
        Поиск страниц в Confluence
        
        Args:
            request: Запрос на поиск
        
        Returns:
            List[ConfluenceArticle]: Найденные страницы
        """
        try:
            logger.info(f"🔄 Поиск страниц в Confluence: '{request.query}'")
            
            url = f"{self.base_url}/rest/api/content"
            params = {
                "title": request.query,
                "type": request.content_type,
                "limit": request.limit,
                "start": request.start,
                "expand": "body.storage,space"
            }
            
            if request.space_key:
                params["spaceKey"] = request.space_key
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for item in data.get("results", []):
                content_html = ""
                if "body" in item and "storage" in item["body"]:
                    content_html = item["body"]["storage"]["value"]
                
                clean_content = self._clean_html_content(content_html)
                
                article = ConfluenceArticle(
                    id=item["id"],
                    title=item["title"],
                    content=clean_content,
                    space_key=item.get("space", {}).get("key", "")
                )
                articles.append(article)
            
            logger.info(f"✅ Найдено {len(articles)} страниц")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске страниц: {str(e)}")
            return []

    async def _apply_template(self, template: ConfluenceTemplate, data: Dict[str, Any]) -> str:
        """
        Применение шаблона с данными
        
        Args:
            template: Шаблон
            data: Данные для заполнения
        
        Returns:
            str: Заполненное содержимое
        """
        try:
            content = template.content or ""
            
            # Заменяем переменные в шаблоне
            for key, value in data.items():
                placeholder = f"{{{{{key}}}}}"
                content = content.replace(placeholder, str(value))
            
            # Заменяем стандартные переменные
            standard_vars = {
                "{{date}}": data.get("date", ""),
                "{{time}}": data.get("time", ""),
                "{{user}}": data.get("user", ""),
                "{{project}}": data.get("project", ""),
                "{{task_id}}": data.get("task_id", ""),
                "{{title}}": data.get("title", ""),
                "{{description}}": data.get("description", "")
            }
            
            for placeholder, value in standard_vars.items():
                content = content.replace(placeholder, str(value))
            
            return content
            
        except Exception as e:
            logger.error(f"❌ Ошибка при применении шаблона: {str(e)}")
            return template.content or ""

    async def _add_labels_to_page(self, page_id: str, labels: List[str]):
        """
        Добавление меток к странице
        
        Args:
            page_id: ID страницы
            labels: Список меток
        """
        try:
            logger.info(f"🔄 Добавление меток к странице {page_id}: {labels}")
            
            url = f"{self.base_url}/rest/api/content/{page_id}/label"
            
            for label in labels:
                label_data = {"name": label}
                response = self.session.post(url, json=label_data)
                response.raise_for_status()
            
            logger.info(f"✅ Метки добавлены к странице {page_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении меток: {str(e)}")

# Глобальный экземпляр сервиса
confluence_service = ConfluenceService()
