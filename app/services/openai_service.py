import json
import logging
from typing import Dict, Any, List
from openai import AsyncOpenAI
from app.config.settings import settings
from app.models.request_models import ConfluenceArticle, UserStoryData

logger = logging.getLogger(__name__)

class OpenAIService:
    """Сервис для работы с OpenAI API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    async def analyze_user_request(self, query: str) -> Dict[str, Any]:
        """
        Анализ запроса пользователя и извлечение ключевых слов для поиска
        """
        
        system_prompt = """
        Проанализируй запрос пользователя и извлеки ключевые слова для поиска в Confluence.
        
        Верни ТОЛЬКО JSON в следующем формате:
        {
            "search_keywords": "ключевые слова для поиска",
            "intent": "создать user story",
            "domain": "мобильная торговля",
            "priority": "medium"
        }
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Запрос: {query}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI анализ запроса: {result_text}")
            
            try:
                analysis = json.loads(result_text)
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON от OpenAI: {e}")
                # Fallback
                return {
                    "search_keywords": query,
                    "intent": "создать user story",
                    "domain": "общий",
                    "priority": "medium"
                }
                
        except Exception as e:
            logger.error(f"Ошибка при анализе запроса: {str(e)}")
            raise Exception(f"Ошибка при анализе запроса: {str(e)}")

    async def extract_story_data(self, article: ConfluenceArticle) -> UserStoryData:
        """
        Извлекаем структурированные данные для User Story из статьи Confluence
        """
        
        system_prompt = """
        Проанализируй статью из Confluence и извлеки данные для создания User Story в TFS.
        
        В статье есть таблица с полями:
        - Проект, Продукт, № TFS, SO, Аналитик, Тех. лид, Разработчик
        - User Story с описанием в формате "Я, как..., хочу..., чтобы..."
        - Критерии приемки в формате "Дано/Когда/Тогда"
        
        Верни ТОЛЬКО JSON в следующем формате:
        {
            "title": "Название User Story (из таблицы)",
            "description": "Полное описание User Story из поля User Story",
            "project": "Название проекта",
            "product": "Название продукта",
            "parent_tfs_id": 123456,
            "assigned_to": "email аналитика или имя",
            "tech_lead": "имя тех.лида",
            "developers": ["разработчик1", "разработчик2"],
            "so_owner": "имя SO",
            "user_story_format": "Я, как..., хочу..., чтобы...",
            "given_conditions": "текст из колонки Дано",
            "when_actions": "текст из колонки Когда", 
            "then_results": "текст из колонки Тогда",
            "acceptance_criteria": ["критерий1", "критерий2"],
            "implementation_objects": ["компонент1", "компонент2"],
            "story_points": 5,
            "priority": 2,
            "tags": ["мобильная-торговля", "транзитные-заказы"]
        }
        """
        
        # Ограничиваем размер контента
        content_preview = article.content[:4000] if len(article.content) > 4000 else article.content
        
        content_for_analysis = f"""
        Название статьи: {article.title}
        Содержание статьи: {content_preview}
        Пространство: {article.space_key}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content_for_analysis}
                ],
                temperature=0.1,  # Низкая температура для точности
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI ответ для извлечения данных: {result_text}")
            
            try:
                extracted_data = json.loads(result_text)
                
                return UserStoryData(
                    title=extracted_data.get("title", article.title),
                    description=extracted_data.get("description", ""),
                    project=extracted_data.get("project", ""),
                    product=extracted_data.get("product"),
                    parent_work_item_id=extracted_data.get("parent_tfs_id"),
                    
                    assigned_to=extracted_data.get("assigned_to"),
                    tech_lead=extracted_data.get("tech_lead"),
                    developers=extracted_data.get("developers", []),
                    so_owner=extracted_data.get("so_owner"),
                    
                    user_story_format=extracted_data.get("user_story_format"),
                    given_conditions=extracted_data.get("given_conditions"),
                    when_actions=extracted_data.get("when_actions"),
                    then_results=extracted_data.get("then_results"),
                    
                    acceptance_criteria=extracted_data.get("acceptance_criteria", []),
                    implementation_objects=extracted_data.get("implementation_objects", []),
                    
                    story_points=extracted_data.get("story_points", 5),
                    priority=extracted_data.get("priority", 2),
                    tags=extracted_data.get("tags", [])
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON от OpenAI: {e}")
                # Fallback с базовыми данными
                return UserStoryData(
                    title=article.title,
                    description="User Story из Confluence",
                    project="Ладога",
                    product="ST Мобильная Торговля",
                    parent_work_item_id=None,
                    acceptance_criteria=["Функционал реализован согласно ТЗ"],
                    implementation_objects=["МобильноеПриложение"]
                )
                
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных: {str(e)}")
            raise Exception(f"Ошибка при извлечении данных из статьи: {str(e)}")

    async def generate_documentation(self, content: str, doc_type: str = "technical") -> str:
        """
        Генерация документации на основе контента
        """
        
        system_prompt = f"""
        Создай {doc_type} документацию на основе предоставленного контента.
        Используй четкую структуру, заголовки и списки.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при генерации документации: {str(e)}")
            raise Exception(f"Ошибка при генерации документации: {str(e)}")

    async def analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """
        Анализ качества кода
        """
        
        system_prompt = """
        Проанализируй качество кода и верни JSON с оценками:
        {
            "readability": "high|medium|low",
            "maintainability": "high|medium|low", 
            "performance": "high|medium|low",
            "security": "high|medium|low",
            "issues": ["проблема1", "проблема2"],
            "suggestions": ["предложение1", "предложение2"]
        }
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": code}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {
                    "readability": "medium",
                    "maintainability": "medium",
                    "performance": "medium", 
                    "security": "medium",
                    "issues": ["Не удалось проанализировать код"],
                    "suggestions": ["Проверьте код вручную"]
                }
                
        except Exception as e:
            logger.error(f"Ошибка при анализе качества кода: {str(e)}")
            raise Exception(f"Ошибка при анализе качества кода: {str(e)}")