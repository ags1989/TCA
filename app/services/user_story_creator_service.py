import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import html
import uuid

from app.services.confluence_service import confluence_service
from app.services.tfs_service import tfs_service
from app.core.logging_config import log_tfs_operation

logger = logging.getLogger(__name__)

class UserStoryData:
    """Модель данных для User Story из Confluence"""
    def __init__(self, title: str, description: str, acceptance_criteria: List[str], 
                 user_story_text: str, us_number: str, given_conditions: str = None,
                 when_actions: str = None, then_results: str = None):
        self.title = title
        self.description = description
        self.acceptance_criteria = acceptance_criteria
        self.user_story_text = user_story_text
        self.us_number = us_number
        self.given_conditions = given_conditions
        self.when_actions = when_actions
        self.then_results = then_results

class ConfluencePageData:
    """Модель данных страницы Confluence"""
    def __init__(self, title: str, project: str, tfs_number: str, url: str, 
                 user_stories: List[UserStoryData], team: str = None):
        self.title = title
        self.project = project
        self.tfs_number = tfs_number
        self.url = url
        self.user_stories = user_stories
        self.team = team

class UserStoryCreatorService:
    """Сервис для создания User Stories из страниц Confluence"""
    
    def __init__(self):
        self.confluence_service = confluence_service
        self.tfs_service = tfs_service
    
    async def create_user_stories_from_confluence(self, confluence_url: str, 
                                                user_confirmation: str = None) -> Dict[str, Any]:
        """
        Основная функция создания User Stories из страницы Confluence
        
        Args:
            confluence_url: URL страницы Confluence
            user_confirmation: Подтверждение пользователя ("Да"/"Нет")
        
        Returns:
            Результат операции с деталями создания
        """
        try:
            # 1. Парсинг страницы Confluence
            page_data = await self._parse_confluence_page(confluence_url)
            
            if not page_data.user_stories:
                return {
                    "success": False,
                    "error": "В статье не найдены User Stories",
                    "preview": None
                }
            
            # 2. Подготовка предварительного просмотра
            logger.info(f"🔍 Создание preview для {len(page_data.user_stories)} User Stories")
            preview = self._create_preview(page_data)
            logger.info(f"✅ Preview создан: {preview.get('user_stories_count', 0)} User Stories")
            
            # Если пользователь еще не подтвердил, возвращаем предварительный просмотр
            if user_confirmation is None:
                logger.info("📋 Возвращаем предварительный просмотр для подтверждения")
                return {
                    "success": True,
                    "preview": preview,
                    "needs_confirmation": True,
                    "page_data": page_data.__dict__
                }
            
            # 3. Обработка ответа пользователя
            if not self._is_confirmation_positive(user_confirmation):
                return {
                    "success": False,
                    "error": "Операция отменена пользователем",
                    "preview": preview
                }
            
            # 4. Создание User Stories в TFS
            creation_result = await self._create_user_stories_in_tfs(page_data)
            
            # 5. Логирование и уведомления
            await self._log_creation_results(creation_result, page_data)
            
            # Проверяем, были ли ошибки при создании
            has_errors = len(creation_result.get("errors", [])) > 0
            has_created = len(creation_result.get("created_stories", [])) > 0
            
            if has_errors and not has_created:
                # Если есть ошибки и ничего не создано
                return {
                    "success": False,
                    "error": f"Не удалось создать ни одной User Story. Ошибки: {'; '.join(creation_result['errors'])}",
                    "created_stories": creation_result["created_stories"],
                    "parent_ticket": page_data.tfs_number,
                    "confluence_url": confluence_url,
                    "preview": preview
                }
            elif has_errors and has_created:
                # Если есть ошибки, но что-то создано
                return {
                    "success": True,
                    "message": f"Создано {len(creation_result['created_stories'])} User Stories, но были ошибки: {'; '.join(creation_result['errors'])}",
                    "created_stories": creation_result["created_stories"],
                    "parent_ticket": page_data.tfs_number,
                    "confluence_url": confluence_url,
                    "preview": preview,
                    "warnings": creation_result["errors"]
                }
            else:
                # Все успешно
                return {
                    "success": True,
                    "message": f"Успешно создано {len(creation_result['created_stories'])} User Stories",
                    "created_stories": creation_result["created_stories"],
                    "parent_ticket": page_data.tfs_number,
                    "confluence_url": confluence_url,
                    "preview": preview
                }
            
        except Exception as e:
            logger.error(f"Ошибка при создании User Stories: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка при создании User Stories: {str(e)}",
                "preview": None
            }
    
    async def _parse_confluence_page(self, confluence_url: str) -> ConfluencePageData:
        """Парсинг страницы Confluence и извлечение данных"""
        try:
            # Извлечение pageId из URL
            page_id = self._extract_page_id(confluence_url)
            
            # Получение страницы из Confluence
            article = await self.confluence_service.get_article_by_id(page_id)
            if not article:
                raise Exception(f"Не удалось получить страницу с ID: {page_id}")
            
            page_content = {
                "title": article.title,
                "content": article.content
            }
            
            # Парсинг метаданных
            metadata = await self._parse_metadata(page_content)
            logger.info(f"🔍 Извлеченные метаданные: {metadata}")
            
            # Дополнительная отладка для TFS номера
            if not metadata.get("tfs_number"):
                logger.warning("⚠️ TFS номер не найден в метаданных!")
                logger.info(f"🔍 Содержимое страницы для анализа:")
                logger.info(f"   Заголовок: {page_content.get('title', 'НЕ НАЙДЕН')}")
                logger.info(f"   Длина контента: {len(page_content.get('content', ''))}")
                
                # Попробуем найти TFS номер в тексте
                content = page_content.get('content', '')
                if 'TFS' in content.upper() or '№' in content:
                    logger.info("🔍 В контенте найдены ключевые слова TFS или №")
                    # Покажем первые 500 символов для анализа
                    preview = content[:500].replace('\n', ' ').replace('\r', ' ')
                    logger.info(f"   Превью контента: {preview}...")
                else:
                    logger.warning("⚠️ В контенте не найдены ключевые слова TFS или №")
            else:
                logger.info(f"✅ TFS номер найден: {metadata.get('tfs_number')}")
            
            # Парсинг User Stories
            user_stories = self._parse_user_stories(page_content)
            
            return ConfluencePageData(
                title=page_content.get("title", ""),
                project=metadata.get("project", ""),
                tfs_number=metadata.get("tfs_number", ""),
                url=confluence_url,
                user_stories=user_stories,
                team=metadata.get("team", "")
            )
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы Confluence: {str(e)}")
            raise
    
    def _extract_page_id(self, confluence_url: str) -> str:
        """Извлечение pageId из URL Confluence"""
        # Паттерны для различных форматов URL Confluence
        patterns = [
            r'pageId=(\d+)',
            r'/pages/(\d+)/',
            r'/(\d+)/',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, confluence_url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Не удалось извлечь pageId из URL: {confluence_url}")
    
    async def _parse_metadata(self, page_content: Dict[str, Any]) -> Dict[str, str]:
        """Парсинг метаданных из страницы"""
        content = page_content.get("content", "")
        
        # Парсинг HTML для поиска таблицы метаданных
        soup = BeautifulSoup(content, 'html.parser')
        
        metadata = {}
        
        # Поиск таблицы с метаданными - более гибкий поиск
        tables = soup.find_all('table')
        logger.info(f"🔍 Найдено {len(tables)} таблиц для поиска метаданных")
        
        # Если таблиц нет, ищем другие структуры с метаданными
        if not tables:
            # Поиск в div с классами таблицы
            table_divs = soup.find_all('div', class_=re.compile(r'table|grid|row', re.IGNORECASE))
            logger.info(f"🔍 Найдено {len(table_divs)} div-элементов с табличными классами")
            
            # Поиск в любых элементах с текстом "№ TFS" или "TFS"
            tfs_elements = soup.find_all(text=re.compile(r'№\s*TFS|TFS', re.IGNORECASE))
            logger.info(f"🔍 Найдено {len(tfs_elements)} элементов с текстом TFS")
            
            # Если нашли элементы с TFS, попробуем извлечь номер
            for element in tfs_elements:
                parent = element.parent
                while parent and parent.name not in ['html', 'body', 'document']:
                    # Ищем номер TFS в тексте родительского элемента
                    text = parent.get_text()
                    tfs_match = re.search(r'№\s*TFS[:\s]*(\d+)', text, re.IGNORECASE)
                    if tfs_match:
                        metadata['tfs_number'] = tfs_match.group(1)
                        logger.info(f"✅ Найден номер TFS в тексте: {tfs_match.group(1)}")
                        break
                    parent = parent.parent
                if 'tfs_number' in metadata:
                    break
        
        # Дополнительный поиск TFS номера в любом месте страницы
        if 'tfs_number' not in metadata:
            logger.info("🔍 Дополнительный поиск TFS номера в тексте страницы")
            page_text = soup.get_text()
            
            # Нормализуем текст - заменяем переносы строк на пробелы
            normalized_text = re.sub(r'\s+', ' ', page_text)
            logger.info(f"🔍 Нормализованный текст (первые 200 символов): {normalized_text[:200]}...")
            
            tfs_patterns = [
                r'№\s*TFS[:\s]*(\d+)',
                r'TFS[:\s]*(\d+)',
                r'№\s*(\d+)',
                r'тикет[:\s]*(\d+)',
                r'задача[:\s]*(\d+)',
                r'тикет\s+(\d+)',
                r'задача\s+(\d+)',
                r'для\s+тикета\s+(\d+)',
                r'в\s+системе\s+TFS[:\s]*(\d+)',
                # Специальные паттерны для многострочного текста
                r'№\s*TFS\s+[^\d]*?(\d+)',
                r'№\s*TFS\s+Запрос\s+на\s+изменение\s+(\d+)',
                r'№\s*TFS\s+[А-Яа-я\s]+?(\d+)'
            ]
            
            for pattern in tfs_patterns:
                tfs_match = re.search(pattern, normalized_text, re.IGNORECASE)
                if tfs_match:
                    metadata['tfs_number'] = tfs_match.group(1)
                    logger.info(f"✅ Найден номер TFS по паттерну '{pattern}': {tfs_match.group(1)}")
                    break
        
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            logger.info(f"🔍 Таблица {i+1}: {len(rows)} строк")
            
            for j, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower()
                    value_cell = cells[1]
                    
                    # Проверяем, есть ли ссылка во второй ячейке
                    link = value_cell.find('a')
                    if link and ('№' in key and 'tfs' in key):
                        # Извлекаем номер из ссылки
                        href = link.get('href', '')
                        link_text = link.get_text(strip=True)
                        logger.info(f"🔍 Найдена ссылка TFS: href='{href}', text='{link_text}'")
                        
                        # Ищем номер в href или в тексте ссылки
                        tfs_match = re.search(r'(\d+)', href) or re.search(r'(\d+)', link_text)
                        if tfs_match:
                            metadata['tfs_number'] = tfs_match.group(1)
                            logger.info(f"✅ TFS номер извлечен из ссылки: {tfs_match.group(1)}")
                            break
                    
                    # Дополнительная проверка для сложной HTML структуры
                    # Ищем любую ссылку в ячейке, если ключ содержит TFS
                    if not metadata.get('tfs_number') and ('tfs' in key or '№' in key):
                        all_links = value_cell.find_all('a')
                        for link in all_links:
                            href = link.get('href', '')
                            link_text = link.get_text(strip=True)
                            logger.info(f"🔍 Проверяем ссылку: href='{href}', text='{link_text}'")
                            
                            # Ищем номер в href
                            tfs_match = re.search(r'(\d+)', href)
                            if tfs_match:
                                metadata['tfs_number'] = tfs_match.group(1)
                                logger.info(f"✅ TFS номер извлечен из ссылки (дополнительный поиск): {tfs_match.group(1)}")
                                break
                    
                    # Обычная обработка текста
                    value = value_cell.get_text(strip=True)
                    logger.info(f"🔍 Строка {j+1}: '{key}' = '{value}'")
                    
                    if 'проект' in key:
                        metadata['project'] = value
                        logger.info(f"✅ Найден проект: {value}")
                    elif '№ tfs' in key or 'tfs' in key:
                        # Извлечение номера TFS из ссылки или текста
                        tfs_match = re.search(r'(\d+)', value)
                        if tfs_match:
                            metadata['tfs_number'] = tfs_match.group(1)
                            logger.info(f"✅ Найден номер TFS: {tfs_match.group(1)}")
                        else:
                            logger.warning(f"⚠️ Не удалось извлечь номер TFS из: {value}")
                    elif 'команда' in key:
                        metadata['team'] = value
                        logger.info(f"✅ Найдена команда: {value}")
        
        # Если команда не найдена в таблице, попробуем найти её из родительского тикета
        if 'team' not in metadata and metadata.get('tfs_number'):
            try:
                # Получаем информацию о родительском тикете из TFS
                parent_work_item = await self.tfs_service.get_work_item(int(metadata['tfs_number']))
                if parent_work_item and hasattr(parent_work_item, 'fields'):
                    # Ищем поле "Команда" в родительском тикете
                    team_field = parent_work_item.fields.get('ST.Team') or parent_work_item.fields.get('System.Team')
                    if team_field:
                        metadata['team'] = team_field
                        logger.info(f"✅ Команда найдена в родительском тикете #{metadata['tfs_number']}: {team_field}")
                    else:
                        logger.warning(f"⚠️ Поле 'Команда' не найдено в родительском тикете #{metadata['tfs_number']}")
            except Exception as e:
                logger.error(f"❌ Ошибка при получении команды из родительского тикета: {str(e)}")
        
        # Если команда все еще не найдена, используем Foxtrot по умолчанию
        if 'team' not in metadata:
            metadata['team'] = 'Foxtrot'
            logger.info(f"ℹ️ Используется команда по умолчанию: Foxtrot")
        
        return metadata
    
    def _parse_user_stories(self, page_content: Dict[str, Any]) -> List[UserStoryData]:
        """Парсинг User Stories из содержимого страницы"""
        content = page_content.get("content", "")
        soup = BeautifulSoup(content, 'html.parser')
        
        logger.info(f"🔍 Парсинг User Stories из страницы: {page_content.get('title', 'Без названия')}")
        logger.info(f"📄 Длина контента: {len(content)} символов")
        
        user_stories = []
        
        # Поиск секции с User Stories
        us_section = self._find_user_stories_section(soup)
        if not us_section:
            logger.warning("❌ Секция с User Stories не найдена")
            # Попробуем найти User Stories в любом месте страницы
            logger.info("🔍 Поиск User Stories в любом месте страницы...")
            us_section = self._find_user_stories_anywhere(soup)
            if not us_section:
                logger.warning("❌ User Stories не найдены нигде на странице")
                return user_stories
            else:
                logger.info(f"✅ Найден контейнер для поиска User Stories: {us_section.name if hasattr(us_section, 'name') else 'Unknown'}")
        else:
            logger.info(f"✅ Найдена секция с User Stories: {us_section.name if hasattr(us_section, 'name') else 'Unknown'}")
        
        # Поиск таблицы с критериями приемки
        criteria_table = self._find_criteria_table(soup)
        if criteria_table:
            logger.info("✅ Найдена таблица с критериями приемки")
        else:
            logger.warning("⚠️ Таблица с критериями приемки не найдена")
        
        # Парсинг каждой User Story
        us_blocks = self._extract_user_story_blocks(us_section)
        logger.info(f"🔍 Найдено {len(us_blocks)} блоков User Stories для обработки")
        
        for i, block in enumerate(us_blocks, 1):
            logger.info(f"🔍 Обрабатываем блок {i} из {len(us_blocks)}")
            try:
                # Если блок содержит только ячейку User Story, передаем всю таблицу с критериями
                if block.find('div', class_='user-story-cell') or block.find('div', class_='user-story-row'):
                    us_data = self._parse_single_user_story(block, f"US{i}", criteria_table)
                else:
                    us_data = self._parse_single_user_story(block, f"US{i}", criteria_table)
                
                if us_data:
                    logger.info(f"✅ User Story {i} успешно обработана: {us_data.title}")
                    user_stories.append(us_data)
                else:
                    logger.warning(f"⚠️ Не удалось обработать блок {i}")
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке блока {i}: {str(e)}")
                continue
        
        return user_stories
    
    def _find_criteria_table(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Поиск таблицы с критериями приемки"""
        # Ищем таблицы с заголовками "Дано", "Когда", "Тогда"
        tables = soup.find_all('table')
        for table in tables:
            headers = table.find_all('th')
            header_texts = [th.get_text(strip=True).lower() for th in headers]
            if any(keyword in ' '.join(header_texts) for keyword in ['дано', 'когда', 'тогда']):
                logger.info("🔍 Найдена таблица с критериями приемки")
                return table
        
        # Если не нашли по заголовкам, ищем по содержимому
        for table in tables:
            table_text = table.get_text().lower()
            if any(keyword in table_text for keyword in ['дано', 'когда', 'тогда', 'критерии приемки']):
                logger.info("🔍 Найдена таблица с критериями приемки по содержимому")
                return table
        
        # Если не нашли отдельную таблицу, ищем в той же таблице, что и User Stories
        for table in tables:
            # Проверяем, есть ли в таблице и User Stories, и критерии
            table_text = table.get_text().lower()
            has_user_story = any(keyword in table_text for keyword in ['я, как', 'я как', 'я,как'])
            has_criteria = any(keyword in table_text for keyword in ['дано', 'когда', 'тогда'])
            
            if has_user_story and has_criteria:
                logger.info("🔍 Найдена таблица с User Stories и критериями приемки")
                return table
        
        return None
    
    def _find_user_stories_section(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Поиск секции с User Stories"""
        # Поиск по заголовкам
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for header in headers:
            text = header.get_text(strip=True).lower()
            if any(keyword in text for keyword in ['user story', 'пользовательская история', 'критерии приёмки']):
                # Возвращаем родительский элемент секции
                return header.find_parent()
        
        # Поиск по таблицам с User Stories
        tables = soup.find_all('table')
        for table in tables:
            if self._table_contains_user_stories(table):
                return table
        
        return None
    
    def _find_user_stories_anywhere(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Поиск User Stories в любом месте страницы"""
        logger.info("🔍 Поиск User Stories в любом месте страницы...")
        
        # Сначала ищем по префиксам US1, US2, UserStory1 и т.д.
        us_prefix_pattern = r'(US\s*\d+|UserStory\s*\d+)'
        us_elements = soup.find_all(text=re.compile(us_prefix_pattern, re.IGNORECASE))
        
        if us_elements:
            logger.info(f"✅ Найдено {len(us_elements)} элементов с префиксами User Stories")
            
            # Ищем общий контейнер, который содержит все User Stories
            common_parent = us_elements[0].parent
            for element in us_elements[1:]:
                current_parent = element.parent
                while current_parent and current_parent != common_parent:
                    if common_parent in current_parent.find_all():
                        common_parent = current_parent
                        break
                    current_parent = current_parent.parent
            
            logger.info(f"🔍 Найден общий контейнер по префиксам: {common_parent.name if common_parent else 'None'}")
            return common_parent or soup
        
        # Fallback: поиск по тексту "Я, как" или "хочу" или "чтобы"
        text_elements = soup.find_all(text=re.compile(r'я\s*,?\s*как|хочу|чтобы', re.IGNORECASE))
        if text_elements:
            logger.info(f"✅ Fallback: найдено {len(text_elements)} элементов с текстом User Story")
            
            # Ищем общий контейнер, который содержит все User Stories
            common_parent = text_elements[0].parent
            for element in text_elements[1:]:
                current_parent = element.parent
                while current_parent and current_parent != common_parent:
                    if common_parent in current_parent.find_all():
                        common_parent = current_parent
                        break
                    current_parent = current_parent.parent
            
            # Если найденный контейнер - это td, ищем родительскую таблицу
            if common_parent and common_parent.name == 'td':
                table = common_parent.find_parent('table')
                if table:
                    logger.info(f"🔍 Найдена родительская таблица для td: {table.name}")
                    return table
            
            logger.info(f"🔍 Найден общий контейнер по тексту: {common_parent.name if common_parent else 'None'}")
            return common_parent or soup
        
        # Поиск по таблицам с более широкими критериями
        tables = soup.find_all('table')
        for table in tables:
            if self._table_contains_user_stories_wide(table):
                logger.info("✅ Найдена таблица с User Stories")
                return table
        
        # Поиск по спискам
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            if self._list_contains_user_stories(list_elem):
                logger.info("✅ Найден список с User Stories")
                return list_elem
        
        logger.warning("❌ User Stories не найдены нигде на странице")
        return None
    
    def _table_contains_user_stories_wide(self, table) -> bool:
        """Расширенная проверка таблицы на наличие User Stories"""
        text = table.get_text().lower()
        keywords = [
            'я, как', 'я как', 'хочу', 'чтобы', 'user story', 'пользовательская история',
            'дано', 'когда', 'тогда', 'критерии приёмки', 'критерии приемки',
            'как пользователь', 'как разработчик', 'как администратор'
        ]
        return any(keyword in text for keyword in keywords)
    
    def _list_contains_user_stories(self, list_elem) -> bool:
        """Проверка списка на наличие User Stories"""
        text = list_elem.get_text().lower()
        return any(keyword in text for keyword in ['я, как', 'я как', 'хочу', 'чтобы'])
    
    def _extract_user_story_rows_from_table(self, table, start_row) -> List:
        """Извлечение всех строк, принадлежащих одной User Story из таблицы"""
        rows = table.find_all('tr')
        us_rows = []
        start_index = rows.index(start_row)
        
        # Добавляем заголовок таблицы, если он есть
        if start_index > 0:
            header_row = rows[0]
            if any(keyword in header_row.get_text().lower() for keyword in ['название', 'user story', 'дано', 'когда', 'тогда']):
                us_rows.append(header_row)
        
        # Добавляем стартовую строку
        us_rows.append(start_row)
        
        # Находим все строки, которые принадлежат этой User Story
        # Это строки, которые идут после стартовой до следующей User Story
        for i in range(start_index + 1, len(rows)):
            row = rows[i]
            cells = row.find_all(['td', 'th'])
            
            # Проверяем, не является ли это новой User Story
            is_new_us = False
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                if (re.match(r'US\d+', cell_text, re.IGNORECASE) or 
                    any(keyword in cell_text.lower() for keyword in ['я, как', 'я как', 'хочу', 'чтобы']) or
                    'user story' in cell_text.lower()):
                    is_new_us = True
                    break
            
            if is_new_us:
                # Это новая User Story, останавливаемся
                break
            else:
                # Это продолжение текущей User Story
                us_rows.append(row)
        
        logger.info(f"🔍 Извлечено {len(us_rows)} строк для User Story")
        return us_rows
    
    def _table_contains_user_stories(self, table) -> bool:
        """Проверка, содержит ли таблица User Stories"""
        text = table.get_text().lower()
        has_keywords = any(keyword in text for keyword in ['user story', 'пользовательская история', 'дано', 'когда', 'тогда'])
        logger.info(f"🔍 Проверка таблицы на User Stories: {has_keywords}")
        if has_keywords:
            logger.info(f"🔍 Найденные ключевые слова в таблице: {[kw for kw in ['user story', 'пользовательская история', 'дано', 'когда', 'тогда'] if kw in text]}")
        return has_keywords
    
    def _extract_user_story_blocks(self, section) -> List[BeautifulSoup]:
        """Извлечение блоков User Stories из текста (заголовки h3) и таблицы"""
        blocks = []
        logger.info(f"🔍 Извлечение блоков User Stories из текста и таблицы")
        
        # Проверяем, является ли сама секция таблицей
        if section.name == 'table':
            logger.info("🔍 Секция сама является таблицей")
            if self._table_contains_user_stories(section):
                logger.info("🔍 Таблица содержит User Stories")
                us_blocks_from_table = self._extract_user_stories_from_table(section)
                blocks.extend(us_blocks_from_table)
                logger.info(f"🔍 Извлечено {len(us_blocks_from_table)} User Stories из таблицы")
            else:
                logger.info("🔍 Таблица не содержит User Stories")
        else:
            # Сначала ищем User Stories в таблицах
            tables = section.find_all('table')
            logger.info(f"🔍 Найдено {len(tables)} таблиц в секции")
            for i, table in enumerate(tables):
                logger.info(f"🔍 Проверяем таблицу {i+1}")
                # Проверяем, содержит ли таблица User Stories
                if self._table_contains_user_stories(table):
                    logger.info("🔍 Найдена таблица с User Stories")
                    
                    # Извлекаем User Stories из таблицы
                    us_blocks_from_table = self._extract_user_stories_from_table(table)
                    blocks.extend(us_blocks_from_table)
                    logger.info(f"🔍 Извлечено {len(us_blocks_from_table)} User Stories из таблицы")
                else:
                    logger.info(f"🔍 Таблица {i+1} не содержит User Stories")
        
        logger.info(f"🔍 После обработки таблиц: {len(blocks)} блоков")
        
        # Если не нашли в таблицах, ищем в заголовках h3
        if not blocks:
            h3_elements = section.find_all('h3')
            for h3 in h3_elements:
                text = h3.get_text(strip=True)
                if re.match(r'US\s*\d+', text, re.IGNORECASE):
                    logger.info(f"🔍 Найдена User Story в заголовке h3: {text[:100]}...")
                    
                    # Создаем блок с заголовком и следующими параграфами
                    us_block_html = f"<div>{str(h3)}"
                    
                    # Добавляем следующие параграфы до следующего заголовка
                    current = h3.next_sibling
                    while current:
                        if hasattr(current, 'name'):
                            if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                break
                            elif current.name == 'p':
                                us_block_html += str(current)
                        current = current.next_sibling
                    
                    us_block_html += "</div>"
                    us_block = BeautifulSoup(us_block_html, 'html.parser')
                    blocks.append(us_block)
                    logger.info(f"🔍 Создан блок User Story из заголовка h3")
        
        # Если все еще не нашли, ищем в других заголовках
        if not blocks:
            for tag in ['h1', 'h2', 'h4', 'h5', 'h6']:
                elements = section.find_all(tag)
                for element in elements:
                    text = element.get_text(strip=True)
                    if re.match(r'US\s*\d+', text, re.IGNORECASE):
                        logger.info(f"🔍 Найдена User Story в заголовке {tag}: {text[:100]}...")
                        
                        # Создаем блок с заголовком и следующими параграфами
                        us_block_html = f"<div>{str(element)}"
                        
                        # Добавляем следующие параграфы до следующего заголовка
                        current = element.next_sibling
                        while current:
                            if hasattr(current, 'name'):
                                if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                    break
                                elif current.name == 'p':
                                    us_block_html += str(current)
                            current = current.next_sibling
                        
                        us_block_html += "</div>"
                        us_block = BeautifulSoup(us_block_html, 'html.parser')
                        blocks.append(us_block)
                        logger.info(f"🔍 Создан блок User Story из заголовка {tag}")
        
        logger.info(f"✅ Найдено {len(blocks)} блоков User Stories всего")
        return blocks
    
    def _extract_user_stories_from_table(self, table: BeautifulSoup) -> List[BeautifulSoup]:
        """Извлечение User Stories из таблицы с критериями приемки"""
        blocks = []
        rows = table.find_all('tr')
        logger.info(f"🔍 Анализ таблицы: {len(rows)} строк")
        
        # Сначала ищем User Stories в ячейках с rowspan (приоритет)
        logger.info("🔍 Поиск User Stories в ячейках с rowspan...")
        cells_with_rowspan = table.find_all(['td', 'th'], rowspan=True)
        processed_rows = set()  # Отслеживаем обработанные строки
        
        for cell in cells_with_rowspan:
            cell_text = cell.get_text(strip=True)
            logger.info(f"🔍 Проверяем ячейку с rowspan: {cell_text[:100]}...")
            
            # Расширенный поиск паттернов User Story
            user_story_patterns = [
                'я, как', 'я как', 'я,как', 'якак',
                'как пользователь', 'как администратор', 'как разработчик',
                'как менеджер', 'как тестировщик', 'как аналитик',
                'user story', 'us ', 'us1', 'us2', 'us3', 'us4', 'us5'
            ]
            
            # Проверяем наличие любого из паттернов
            has_user_story_pattern = any(pattern in cell_text.lower() for pattern in user_story_patterns)
            
            # Дополнительная проверка на наличие ключевых слов User Story
            has_keywords = 'хочу' in cell_text.lower() and 'чтобы' in cell_text.lower()
            
            # Проверяем, содержит ли ячейка текст User Story (приоритет)
            has_user_story_text = 'хочу' in cell_text.lower() and 'чтобы' in cell_text.lower()
            
            # Создаем блок только для ячейки с текстом User Story, а не с названием
            if has_user_story_text:
                logger.info(f"🔍 Найдена User Story в ячейке с rowspan: {cell_text[:100]}...")
                logger.info(f"🔍 Паттерн: {has_user_story_pattern}, Ключевые слова: {has_keywords}, Текст User Story: {has_user_story_text}")
                
                # Получаем строку и проверяем, не обрабатывали ли мы её уже
                row = cell.find_parent('tr')
                if row and id(row) not in processed_rows:
                    processed_rows.add(id(row))
                    
                    # Ищем название User Story в предыдущей ячейке (обычно это первая ячейка с rowspan)
                    title_cell = None
                    all_cells = row.find_all(['td', 'th'])
                    cell_index = all_cells.index(cell)
                    if cell_index > 0:
                        title_cell = all_cells[cell_index - 1]
                        logger.info(f"🔍 Найдена ячейка с названием: {title_cell.get_text(strip=True)[:100]}...")
                    
                    # Создаем блок с ячейкой User Story и названием
                    us_cell_html = f"<div class='user-story-cell' data-rowspan='true'>{str(cell)}</div>"
                    if title_cell:
                        us_cell_html += f"<div class='user-story-title' data-rowspan='true'>{str(title_cell)}</div>"
                    
                    us_block = BeautifulSoup(us_cell_html, 'html.parser')
                    blocks.append(us_block)
                    logger.info(f"🔍 Создан блок User Story из ячейки с rowspan")
        
        # Если не нашли в rowspan ячейках, ищем в обычных строках
        if not blocks:
            logger.info("🔍 Поиск User Stories в обычных строках...")
            us_rows = []
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Проверяем, содержит ли строка User Story
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        # Ищем "Я, как" в ячейке - это признак User Story
                        if 'я, как' in cell_text.lower() or 'я как' in cell_text.lower() or 'я,как' in cell_text.lower():
                            us_rows.append(i)
                            logger.info(f"🔍 Найдена User Story в строке {i}: {cell_text[:100]}...")
                            break
            
            logger.info(f"🔍 Найдено {len(us_rows)} строк с User Stories: {us_rows}")
            
            # Создаем блоки для каждой User Story с информацией о строке
            for i, us_row_index in enumerate(us_rows):
                # Находим ячейку с User Story
                us_row = rows[us_row_index]
                us_cells = us_row.find_all(['td', 'th'])
                
                # Ищем ячейку с текстом User Story
                us_cell = None
                for cell in us_cells:
                    cell_text = cell.get_text(strip=True)
                    if 'я, как' in cell_text.lower() or 'я как' in cell_text.lower() or 'я,как' in cell_text.lower():
                        us_cell = cell
                        break
                
                # Создаем блок с полной строкой и добавляем атрибут с индексом строки
                us_row_html = f"<div class='user-story-row' data-row-index='{us_row_index}'>{str(us_row)}</div>"
                us_block = BeautifulSoup(us_row_html, 'html.parser')
                blocks.append(us_block)
                logger.info(f"🔍 Создан блок User Story {i+1} с полной строкой (индекс: {us_row_index})")
        
        return blocks
    
    def _parse_single_user_story(self, block: BeautifulSoup, us_number: str, criteria_table: BeautifulSoup = None) -> Optional[UserStoryData]:
        """Парсинг отдельной User Story"""
        logger.info(f"🔍 _parse_single_user_story вызван для {us_number}")
        logger.info(f"🔍 Блок: {block.name}, содержимое: {str(block)[:200]}...")
        try:
            # Извлечение текста User Story
            user_story_text = self._extract_user_story_text(block)
            
            # Строгая проверка на наличие всех ключевых слов
            if not self._is_valid_user_story(user_story_text):
                logger.warning(f"❌ Блок {us_number} не является валидной User Story - отсутствуют ключевые слова")
                return None
            
            # Извлечение заголовка
            title = self._extract_title(block, us_number)
            
            # Извлечение критериев приёмки
            logger.info(f"🔍 Блок {us_number}: тип = {block.name}, содержимое = {str(block)[:200]}...")
            
            # Ищем таблицу с критериями
            table = None
            
            # Сначала проверяем переданную таблицу с критериями
            if criteria_table:
                table = criteria_table
                logger.info(f"🔍 Используем переданную таблицу с критериями для {us_number}")
            else:
                # Ищем таблицу в блоке
                if block.name == 'table':
                    table = block
                else:
                    # Ищем таблицу внутри блока
                    table = block.find('table')
                    if not table:
                        # Ищем таблицу с критериями приемки в родительских элементах
                        parent = block.parent
                        while parent and parent.name not in ['html', 'body', 'document']:
                            if parent.name == 'table' and self._table_contains_user_stories(parent):
                                table = parent
                                break
                            # Для блоков с rowspan ячейками ищем таблицу с заголовками "Дано", "Когда", "Тогда"
                            if block.find('div', class_='user-story-cell'):
                                parent_tables = parent.find_all('table')
                                for candidate_table in parent_tables:
                                    header_row = candidate_table.find('tr')
                                    if header_row:
                                        headers = [cell.get_text(strip=True).lower() for cell in header_row.find_all(['th', 'td'])]
                                        if (any('дано' in h for h in headers) and
                                            any('когда' in h for h in headers) and
                                            any('тогда' in h for h in headers)):
                                            table = candidate_table
                                            logger.info(f"✅ Найдена таблица с критериями в родителе {parent.name}")
                                            break
                                if table:
                                    break
                            parent = parent.parent
            
            if table:
                logger.info(f"🔍 Извлекаем критерии из таблицы для {us_number}")
                
                # Извлекаем индекс строки User Story из блока
                us_row_index = None
                us_row_div = block.find('div', class_='user-story-row')
                if us_row_div and us_row_div.get('data-row-index'):
                    us_row_index = int(us_row_div.get('data-row-index'))
                    logger.info(f"🔍 Найден индекс строки User Story: {us_row_index}")
                
                # Если таблица критериев передана извне (отдельная таблица),
                # используем номер US из параметра us_number (например, 'US1') для фильтра по колонке US
                if criteria_table:
                    m = re.search(r'(\d+)', us_number)
                    us_index_for_filter = int(m.group(1)) if m else None
                    logger.info(f"🔧 Для внешней таблицы критериев используем номер US из заголовка: {us_index_for_filter}")
                else:
                    # Для блоков с rowspan ячейками ищем номер US в названии
                    if block.find('div', class_='user-story-cell'):
                        title_text = self._extract_user_story_title(block)
                        if title_text:
                            m = re.search(r'US(\d+)', title_text, re.IGNORECASE)
                            if m:
                                us_index_for_filter = int(m.group(1))
                                logger.info(f"🔧 Для блока с rowspan используем номер US из названия: {us_index_for_filter}")
                            else:
                                us_index_for_filter = us_row_index
                                logger.info(f"🔧 Для блока с rowspan используем индекс строки: {us_index_for_filter}")
                        else:
                            us_index_for_filter = us_row_index
                            logger.info(f"🔧 Для блока с rowspan используем индекс строки: {us_index_for_filter}")
                    else:
                        us_index_for_filter = us_row_index
                        logger.info(f"🔧 Для таблицы с US используем индекс строки: {us_index_for_filter}")
                acceptance_criteria, given_conditions, when_actions, then_results = self._extract_acceptance_criteria(table, us_index_for_filter)
            else:
                logger.warning(f"❌ Таблица с критериями не найдена для {us_number}")
                # Если таблица не найдена, создаем пустые критерии
                acceptance_criteria, given_conditions, when_actions, then_results = [], [], [], []
            
            # Преобразуем HTML в список критериев
            if isinstance(acceptance_criteria, str) and acceptance_criteria:
                # Если это HTML таблица, создаем список критериев
                criteria_list = [{"html": acceptance_criteria}]
            elif isinstance(acceptance_criteria, list):
                criteria_list = acceptance_criteria
            else:
                criteria_list = []
            
            logger.info(f"🔍 Критерии приемки: {len(criteria_list)} элементов")
            
            # Формирование описания
            description = self._format_description(user_story_text)
            
            # Валидация данных
            if not title or not user_story_text:
                logger.warning(f"❌ Недостаточно данных для User Story {us_number}: title='{title}', user_story_text='{user_story_text[:50] if user_story_text else 'None'}...'")
                return None
            
            logger.info(f"✅ User Story {us_number} успешно обработана: {title}")
            
            return UserStoryData(
                title=title,
                description=description,
                acceptance_criteria=acceptance_criteria,
                user_story_text=user_story_text,
                us_number=us_number,
                given_conditions=given_conditions,
                when_actions=when_actions,
                then_results=then_results
            )
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге User Story {us_number}: {str(e)}")
            return None
    
    def _extract_title(self, block: BeautifulSoup, us_number: str) -> str:
        """Извлечение заголовка User Story"""
        # Сначала пытаемся извлечь название из ячейки с классом user-story-title
        title = self._extract_user_story_title(block)
        if title:
            # Если название уже содержит US и номер, возвращаем как есть
            if re.match(r'US\s*\d+', title, re.IGNORECASE):
                return title
            # Иначе добавляем префикс с номером US
            return f"{us_number} {title}"
        
        # Ищем текст, который содержит US1 и название в кавычках
        text = block.get_text()
        
        # Паттерн для поиска US1 "Название"
        pattern = r'US\s*\d+\s*["""]([^"""]+)["""]'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            return title  # Возвращаем только название без префикса
        
        # Альтернативный поиск - ищем текст после US1 до следующего ключевого слова
        pattern2 = r'US\s*\d+\s*([^Яя]+?)(?=Я,?\s*как|$)'
        match2 = re.search(pattern2, text, re.IGNORECASE | re.DOTALL)
        if match2:
            title = match2.group(1).strip()
            # Очищаем от лишних символов
            title = re.sub(r'[^\w\s\-]', '', title).strip()
            if title and len(title) > 3:
                return title  # Возвращаем только название без префикса
        
        # Поиск в ячейках таблицы как fallback
        cells = block.find_all(['td', 'th'])
        
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            # Очищаем от HTML entities и неразрывных пробелов
            text = text.replace('&nbsp;', ' ').replace('\xa0', ' ')
            text = re.sub(r'\s+', ' ', text)
            
            # Если это ячейка с номером US, берем заголовок из следующей ячейки
            if re.match(r'US\d+', text, re.IGNORECASE) and i + 1 < len(cells):
                next_cell_text = cells[i + 1].get_text(strip=True)
                # Очищаем от HTML entities и неразрывных пробелов
                next_cell_text = next_cell_text.replace('&nbsp;', ' ').replace('\xa0', ' ')
                next_cell_text = re.sub(r'\s+', ' ', next_cell_text)
                
                if next_cell_text and len(next_cell_text) > 3:
                    # Извлекаем только название из текста User Story
                    # Ищем текст между "Я, как" и "хочу"
                    title_match = re.search(r'Я,?\s*как\s+([^,]+?),\s*хочу', next_cell_text, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()
                        return title
                    # Если не нашли, ищем в первой части до "хочу"
                    title_match = re.search(r'^([^х]+?)\s*хочу', next_cell_text, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()
                        # Убираем "Я, как" если есть
                        title = re.sub(r'^я,?\s*как\s*', '', title, flags=re.IGNORECASE).strip()
                        if title:
                            return title
                    # Если не нашли, возвращаем первые 50 символов
                    return next_cell_text[:50] + "..." if len(next_cell_text) > 50 else next_cell_text
            # Если это обычная ячейка с текстом (не US номер и не заголовок таблицы)
            elif (text and not text.startswith('US') and len(text) > 3 and 
                  not any(keyword in text.lower() for keyword in ['название', 'user story', 'дано', 'когда', 'тогда'])):
                return text  # Возвращаем только название без префикса
        
        return "User Story"  # Возвращаем только название без префикса
    
    def _is_valid_user_story(self, text: str) -> bool:
        """Строгая проверка, является ли текст валидной User Story"""
        if not text or len(text.strip()) < 10:
            return False
        
        text_lower = text.lower()
        
        # Должны присутствовать ВСЕ ключевые слова
        # Ищем "я, как" или "я как" в любом месте текста, не только в начале
        has_ya_kak = any(phrase in text_lower for phrase in ['я, как', 'я как', 'якак', 'я как', 'я,как'])
        has_hocu = 'хочу' in text_lower
        has_chtoby = 'чтобы' in text_lower
        
        # Дополнительная проверка на структуру User Story
        # Должно быть предложение, начинающееся с "Я, как" или "Я как"
        # Временно ослабляем проверку для отладки
        starts_correctly = True  # text_lower.strip().startswith(('я, как', 'я как'))
        
        # Проверяем, что это не техническая документация
        technical_keywords = [
            'код', 'система', 'поле', 'колонка', 'справочник', 'база данных',
            'api', 'json', 'xml', 'файл', 'конфигурация', 'настройка',
            'разработчик', 'программист', 'код', 'функция', 'метод'
        ]
        
        has_too_many_technical = sum(1 for keyword in technical_keywords if keyword in text_lower) > 10  # Увеличиваем лимит
        
        is_valid = has_ya_kak and has_hocu and has_chtoby and starts_correctly and not has_too_many_technical
        
        logger.info(f"🔍 Проверка User Story: ya_kak={has_ya_kak}, hocu={has_hocu}, chtoby={has_chtoby}, starts_correctly={starts_correctly}, not_technical={not has_too_many_technical}")
        
        return is_valid
    
    def _extract_user_story_from_cell(self, cell_text: str) -> str:
        """Извлечение только текста User Story из ячейки таблицы"""
        # Очищаем от HTML entities и неразрывных пробелов
        cell_text = cell_text.replace('&nbsp;', ' ').replace('\xa0', ' ')
        
        # Заменяем HTML теги на пробелы, чтобы сохранить разделение между параграфами
        cell_text = re.sub(r'</p>\s*<p[^>]*>', ' ', cell_text)
        cell_text = re.sub(r'<[^>]+>', '', cell_text)  # Удаляем все остальные HTML теги
        
        # Нормализуем пробелы
        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
        
        # Поиск паттерна User Story - более строгий
        patterns = [
            r'Я,?\s*как[^.]*хочу[^.]*чтобы[^.]*\.',
            r'Я,?\s*как[^.]*хочу[^.]*чтобы[^.]*',
            r'Как[^.]*хочу[^.]*чтобы[^.]*\.',
            r'Пользователь[^.]*хочу[^.]*чтобы[^.]*\.'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cell_text, re.IGNORECASE | re.DOTALL)
            if match:
                result = match.group(0).strip()
                # Очищаем от лишних символов и HTML entities
                result = re.sub(r'\s+', ' ', result)
                result = result.replace('&nbsp;', ' ').replace('\xa0', ' ')
                return result
        
        # Если паттерн не найден, ищем предложения, начинающиеся с "Я, как"
        sentences = re.split(r'[.!?]', cell_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if re.match(r'^я,?\s*как', sentence, re.IGNORECASE):
                # Очищаем от лишних символов и HTML entities
                result = re.sub(r'\s+', ' ', sentence)
                result = result.replace('&nbsp;', ' ').replace('\xa0', ' ')
                return result
        
        # Если ничего не найдено, возвращаем пустую строку
        return ""
    
    def _extract_user_story_title(self, block: BeautifulSoup) -> str:
        """Извлечение названия User Story из блока"""
        # Если блок содержит ячейку с названием, извлекаем его
        if block.find('div', class_='user-story-title'):
            title_cell = block.find('div', class_='user-story-title').find(['td', 'th'])
            if title_cell:
                title_text = title_cell.get_text(strip=True)
                # Убираем HTML теги и нормализуем пробелы
                title_text = re.sub(r'<[^>]+>', '', title_text)
                title_text = re.sub(r'\s+', ' ', title_text).strip()
                # Убираем кавычки если есть
                title_text = re.sub(r'^["""]+|["""]+$', '', title_text).strip()
                # Добавляем пробел между US и номером, если его нет
                title_text = re.sub(r'US(\d+)', r'US\1 ', title_text)
                logger.info(f"✅ Найдено название User Story: {title_text[:100]}...")
                return title_text
        
        # Если название не найдено, возвращаем пустую строку
        return ""
    
    def _extract_user_story_text(self, block: BeautifulSoup) -> str:
        """Извлечение текста User Story в формате 'Я, как... хочу... чтобы...'"""
        logger.info(f"🔍 Извлечение текста User Story из блока: {block.name}")
        
        # Если это таблица, ищем User Story в ячейках с rowspan
        if block.name == 'table':
            # Сначала ищем в ячейках с rowspan (приоритет)
            cells_with_rowspan = block.find_all(['td', 'th'], rowspan=True)
            for cell in cells_with_rowspan:
                cell_text = cell.get_text().lower()
                if any(keyword in cell_text for keyword in ['я, как', 'я как', 'хочу', 'чтобы']):
                    # Извлекаем только текст User Story из этой ячейки
                    user_story_text = self._extract_user_story_from_cell(cell.get_text())
                    if user_story_text:
                        logger.info(f"✅ Найдена User Story в ячейке с rowspan: {user_story_text[:100]}...")
                        return user_story_text
            
            # Если не нашли в rowspan ячейках, ищем в обычных ячейках
            all_cells = block.find_all(['td', 'th'])
            for cell in all_cells:
                cell_text = cell.get_text().lower()
                if any(keyword in cell_text for keyword in ['я, как', 'я как', 'хочу', 'чтобы']):
                    # Извлекаем только текст User Story из этой ячейки
                    user_story_text = self._extract_user_story_from_cell(cell.get_text())
                    if user_story_text:
                        logger.info(f"✅ Найдена User Story в ячейке: {user_story_text[:100]}...")
                        return user_story_text
        
        # Если блок содержит ячейку с rowspan, извлекаем User Story из неё
        if block.find('div', class_='user-story-cell'):
            # Извлекаем User Story из ячейки с rowspan
            cell = block.find('div', class_='user-story-cell').find(['td', 'th'])
            if cell:
                user_story_text = self._extract_user_story_from_cell(cell.get_text())
                if user_story_text:
                    logger.info(f"✅ Найдена User Story в ячейке с rowspan: {user_story_text[:100]}...")
                    return user_story_text
        
        # Если блок содержит строку таблицы, ищем ячейку с User Story
        if block.find('div', class_='user-story-row'):
            # Ищем ячейку с User Story во второй колонке (индекс 1)
            cells = block.find_all(['td', 'th'])
            if len(cells) >= 2:
                user_story_cell = cells[1]  # Вторая ячейка содержит User Story
                user_story_text = self._extract_user_story_from_cell(user_story_cell.get_text())
                if user_story_text:
                    logger.info(f"✅ Найдена User Story в ячейке таблицы: {user_story_text[:100]}...")
                    return user_story_text
        
        # Если не таблица, получаем весь текст
        text = block.get_text()
        logger.info(f"🔍 Извлечение текста User Story из: {text[:100]}...")
        
        # Используем функцию извлечения из ячейки
        user_story_text = self._extract_user_story_from_cell(text)
        if user_story_text:
            logger.info(f"✅ Найден текст User Story: {user_story_text}")
            return user_story_text
        
        # Если ничего не найдено, возвращаем пустую строку
        logger.warning(f"⚠️ Паттерн User Story не найден в тексте: {text[:50]}...")
        return ""
    
    def _extract_acceptance_criteria(self, block: BeautifulSoup, us_row_index: int = None) -> Tuple[List[Dict[str, str]], str, str, str]:
        """
        Универсальный парсер критериев приёмки: формирует новую таблицу только с колонками Дано, Когда, Тогда
        """
        logger.info(f"🔍 Поиск критериев приёмки в блоке...")
        import uuid
        debug_uuid = str(uuid.uuid4())[:8]
        logger.info(f"🆔[{debug_uuid}] Старт обработки критериев")

        def select_acceptance_table(tables, source_label):
            for idx, candidate in enumerate(tables, start=1):
                header_row = candidate.find('tr')
                if not header_row:
                    continue
                headers = [cell.get_text(strip=True).lower() for cell in header_row.find_all(['th', 'td'])]
                logger.info(f"   🔖[{debug_uuid}] {source_label} таблица {idx}: заголовки {headers}")
                if (any('дано' in h for h in headers) and
                    any('когда' in h for h in headers) and
                    any('тогда' in h for h in headers)):
                    logger.info(f"✅[{debug_uuid}] Выбрана таблица {idx} из {source_label} по заголовкам")
                    return candidate
            return None

        table = None

        # Проверяем, является ли сам блок таблицей
        if block.name == 'table':
            table = select_acceptance_table([block], 'блока')
        else:
            # Ищем таблицы внутри блока
            tables_in_block = block.find_all('table')
            logger.info(f"🆔[{debug_uuid}] Поиск таблиц в блоке: {block.name}")
            logger.info(f"🆔[{debug_uuid}] Содержимое блока: {str(block)[:200]}...")
            if tables_in_block:
                logger.info(f"🆔[{debug_uuid}] Найдено {len(tables_in_block)} таблиц внутри блока")
                table = select_acceptance_table(tables_in_block, 'блока')

        if not table:
            # ищем в родителях
            parent = block.parent
            while parent and parent.name not in ['html', 'body', 'document']:
                parent_tables = parent.find_all('table')
                if parent_tables:
                    logger.info(f"🆔[{debug_uuid}] В родителе {parent.name} найдено {len(parent_tables)} таблиц")
                    table = select_acceptance_table(parent_tables, f'родителя {parent.name}')
                    if table:
                        break
                parent = parent.parent

        if not table:
            # ищем во всем документе
            root = block
            while root.parent:
                root = root.parent
            all_tables = root.find_all('table')
            logger.info(f"🔍[{debug_uuid}] Всего таблиц в документе: {len(all_tables)}")
            table = select_acceptance_table(all_tables, 'документа')

        if table:
            table_preview = str(table)[:500].replace('\n', ' ')
            logger.info(f"📄[{debug_uuid}] Используемая таблица (обрезано): {table_preview}...")
            # 1. Найти заголовки и индексы нужных колонок
            header_row = table.find('tr')
            if not header_row:
                logger.warning(f"⚠️[{debug_uuid}] Заголовок таблицы не найден")
                return [], '', '', ''
            
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            # Очищаем заголовки от HTML entities и неразрывных пробелов
            headers = [h.replace('&nbsp;', ' ').replace('\xa0', ' ') for h in headers]
            headers = [re.sub(r'\s+', ' ', h) for h in headers]
            headers_lower = [h.lower() for h in headers]
            headers_compact = [re.sub(r'[\s_\-\.]+', '', h.lower()) for h in headers]
            logger.info(f"🔖[{debug_uuid}] Найденные заголовки: {headers}")
            logger.info(f"🔖[{debug_uuid}] Заголовки в нижнем регистре: {headers_lower}")
            
            dano_idx = next((i for i, h in enumerate(headers_lower) if 'дано' in h), None)
            kogda_idx = next((i for i, h in enumerate(headers_lower) if 'когда' in h), None)
            togda_idx = next((i for i, h in enumerate(headers_lower) if 'тогда' in h), None)
            # Поиск колонки идентификатора US: расширенный по заголовку
            us_col_idx = None
            header_us_candidates = []
            for i, compact in enumerate(headers_compact):
                # Явные варианты: 'us', 'userstory', а также 'названиеus'
                if compact == 'us' or 'userstory' in compact or 'названиеus' in compact:
                    header_us_candidates.append(i)
            if header_us_candidates:
                us_col_idx = header_us_candidates[0]
                logger.info(f"📌[{debug_uuid}] Кандидаты US-колонки по заголовкам: {header_us_candidates}; выбран {us_col_idx} ('{headers[us_col_idx]}')")
            logger.info(f"📌[{debug_uuid}] Индексы колонок - Дано: {dano_idx}, Когда: {kogda_idx}, Тогда: {togda_idx}")
            
            if None in (dano_idx, kogda_idx, togda_idx):
                logger.warning(f"⚠️[{debug_uuid}] Не удалось определить индексы колонок Дано/Когда/Тогда")
                logger.warning(f"⚠️[{debug_uuid}] Поиск по частичным совпадениям...")
                # Попробуем найти по частичным совпадениям
                for i, h in enumerate(headers_lower):
                    if 'дано' in h or 'given' in h:
                        dano_idx = i
                        logger.info(f"✅[{debug_uuid}] Найден 'Дано' в колонке {i}: '{h}'")
                    if 'когда' in h or 'when' in h:
                        kogda_idx = i
                        logger.info(f"✅[{debug_uuid}] Найден 'Когда' в колонке {i}: '{h}'")
                    if 'тогда' in h or 'then' in h:
                        togda_idx = i
                        logger.info(f"✅[{debug_uuid}] Найден 'Тогда' в колонке {i}: '{h}'")
                
                if None in (dano_idx, kogda_idx, togda_idx):
                    logger.warning(f"⚠️[{debug_uuid}] Не удалось найти все необходимые колонки даже по частичным совпадениям")
                    return [], '', '', ''
            # 2. Построить полную матрицу значений с учётом rowspan/colspan
            matrix = []
            rowspans = {}
            data_rows = table.find_all('tr')[1:]
            logger.info(f"🔢[{debug_uuid}] Количество строк данных (без заголовка): {len(data_rows)}")
            for tr_idx, tr in enumerate(data_rows):
                row = []
                cells = tr.find_all(['td', 'th'])
                logger.info(f"   ➡️[{debug_uuid}] Строка {tr_idx + 1}: всего ячеек = {len(cells)}")
                col = 0
                i = 0
                while col < len(headers):
                    # Если есть незакрытый rowspan из предыдущих строк
                    if (tr_idx, col) in rowspans:
                        value = rowspans[(tr_idx, col)]
                        row.append(value)
                        logger.debug(f"      ↪️[{debug_uuid}] Применён rowspan значение '{value}' в колонке {col}")
                        col += 1
                        continue
                    if i >= len(cells):
                        row.append("")
                        col += 1
                        continue
                    cell = cells[i]
                    text = cell.get_text(separator=' ', strip=True)
                    # Очищаем от HTML entities и неразрывных пробелов
                    text = text.replace('&nbsp;', ' ').replace('\xa0', ' ')
                    text = re.sub(r'\s+', ' ', text)
                    rowspan = int(cell.get('rowspan', 1))
                    colspan = int(cell.get('colspan', 1))
                    logger.debug(f"      ⬜[{debug_uuid}] Ячейка {i}: text='{text[:50]}...', rowspan={rowspan}, colspan={colspan}, текущая колонка={col}")
                    for c in range(colspan):
                        row.append(text)
                        if rowspan > 1:
                            for r in range(1, rowspan):
                                rowspans[(tr_idx + r, col)] = text
                                logger.debug(f"         ↘️[{debug_uuid}] Сохранён rowspan для строки {tr_idx + r + 1}, колонки {col}")
                        col += 1
                    i += 1
                logger.info(f"   ✅[{debug_uuid}] Строка {tr_idx + 1} после разворачивания: {row}")
                matrix.append(row)
            
            # 3. Собрать только нужные колонки
            logger.info(f"🔢[{debug_uuid}] Матрица построена: {len(matrix)} строк")
            # Уточняем колонку US по содержимому (если по заголовку определили неверно)
            if len(matrix) > 0:
                best_col = None
                best_count = -1
                def _norm_us(cell_val: str) -> str:
                    s = str(cell_val).strip()
                    s = s.replace('\xa0', ' ')
                    s = re.sub(r'\s+', ' ', s)
                    return s
                for i in range(len(headers)):
                    count = 0
                    for r in range(len(matrix)):
                        cell = matrix[r][i] if i < len(matrix[r]) else ''
                        val = _norm_us(cell)
                        # Ищем префикс вида 'US\d+'
                        if re.match(r'\s*US\s*\d+', val, flags=re.IGNORECASE):
                            count += 1
                    if count > best_count:
                        best_count = count
                        best_col = i
                logger.info(f"🔬[{debug_uuid}] Лучшая US-колонка по данным: {best_col} ('{headers[best_col] if best_col is not None else '?'}'), совпадений: {best_count}")
                if best_count > 0 and (us_col_idx is None or (best_col is not None and best_col not in (header_us_candidates or []))):
                    us_col_idx = best_col
                    logger.info(f"✅[{debug_uuid}] US-колонка переопределена по данным: индекс {us_col_idx} ('{headers[us_col_idx]}')")
                elif us_col_idx is not None:
                    logger.info(f"ℹ️[{debug_uuid}] Оставляем US-колонку по заголовку: индекс {us_col_idx} ('{headers[us_col_idx]}')")
                else:
                    logger.info(f"ℹ️[{debug_uuid}] Колонка US не определена")

            rows = []

            # Вспомогательные функции
            def normalize_us_value(value: str) -> str:
                if value is None:
                    return ''
                s = str(value).strip().lower()
                s = s.replace('\xa0', ' ')
                s = re.sub(r'[\s_\-]+', '', s)
                s = s.replace('userstory', 'us')
                m = re.search(r'us?(\d+)', s)
                if m:
                    return f"us{m.group(1)}"
                return s

            def extract_vals_from_row(row_list):
                return [
                    row_list[dano_idx] if dano_idx is not None and dano_idx < len(row_list) else "",
                    row_list[kogda_idx] if kogda_idx is not None and kogda_idx < len(row_list) else "",
                    row_list[togda_idx] if togda_idx is not None and togda_idx < len(row_list) else "",
                ]
            
            if us_col_idx is not None and us_row_index is not None:
                # Режим фильтрации по колонке US: fill-down и отбор строк текущей US
                logger.info(f"🔍[{debug_uuid}] Активирован US-фильтр по колонке {us_col_idx} для us_row_index={us_row_index}")
                filled_us_vals = []
                current_us = ''
                for r in range(len(matrix)):
                    cell_val = matrix[r][us_col_idx] if us_col_idx < len(matrix[r]) else ''
                    cell_val = cell_val.strip()
                    if cell_val:
                        current_us = cell_val
                    filled_us_vals.append(current_us)
                # Формируем набор кандидатов: строго us{N} и N
                candidates_raw = [f"us{us_row_index}", str(us_row_index)]
                candidate_norms = {normalize_us_value(c) for c in candidates_raw}
                logger.info(f"🎯[{debug_uuid}] Целевые US-маркеры: {sorted(candidate_norms)}")
                for row_idx, row in enumerate(matrix):
                    us_val_norm = normalize_us_value(filled_us_vals[row_idx])
                    if us_val_norm and us_val_norm in candidate_norms:
                        vals = extract_vals_from_row(row)
                        logger.info(f"   📎[{debug_uuid}] Строка {row_idx + 1} отобрана по US='{filled_us_vals[row_idx]}' → {vals}")
                        if any(val.strip() for val in vals):
                            rows.append(vals)
                    else:
                        logger.debug(f"   ⏭️[{debug_uuid}] Строка {row_idx + 1} пропущена по US: '{filled_us_vals[row_idx]}' ({us_val_norm})")
                if not rows:
                    logger.warning(f"⚠️[{debug_uuid}] US-фильтр не дал результатов, будет использован общий режим")
            elif us_col_idx is not None and us_row_index is None:
                # Есть колонка US, но индекс не передан → разбивка не выполняется: берём все строки
                logger.info(f"ℹ️[{debug_uuid}] Найдена колонка US (индекс {us_col_idx}), но us_row_index не задан — возвращаем все строки таблицы без фильтра")
                for row_idx, row in enumerate(matrix, start=1):
                    vals = extract_vals_from_row(row)
                    if any(val.strip() for val in vals):
                        rows.append(vals)
                        logger.info(f"   ✅[{debug_uuid}] Строка {row_idx} добавлена (без фильтра)")
            elif us_row_index is not None:
                # us_row_index - это индекс строки в исходной HTML таблице (включая заголовок)
                # matrix - это матрица данных без заголовка, поэтому нужно вычесть 1
                matrix_row_index = us_row_index - 1
                logger.info(f"🔍[{debug_uuid}] Поиск строк критериев для US строки {us_row_index} (индекс в матрице: {matrix_row_index})")
                
                if matrix_row_index < 0 or matrix_row_index >= len(matrix):
                    logger.warning(f"⚠️[{debug_uuid}] Индекс строки US {matrix_row_index} выходит за границы матрицы {len(matrix)}")
                    return [], '', '', ''
                
                # Ищем строки, которые относятся к этой User Story
                # Обычно это строки после строки User Story до следующей User Story
                us_start_row = matrix_row_index
                us_end_row = len(matrix)
                
                # Ищем следующую User Story в матрице
                for row_idx in range(matrix_row_index + 1, len(matrix)):
                    row = matrix[row_idx]
                    # Проверяем, есть ли в строке признаки новой User Story
                    # Ищем "я, как" или "я как" в любой из колонок
                    row_text = ' '.join(str(cell) for cell in row).lower()
                    if 'я, как' in row_text or 'я как' in row_text or 'я,как' in row_text:
                        us_end_row = row_idx
                        logger.info(f"🔍[{debug_uuid}] Найдена следующая US в строке {row_idx + 1}, критерии до строки {us_end_row}")
                        break
                
                logger.info(f"🔍[{debug_uuid}] Критерии для US {us_row_index}: строки матрицы {us_start_row + 1} - {us_end_row}")
                
                # Берем все строки от US строки до следующей US (исключая саму US строку)
                for row_idx in range(us_start_row + 1, us_end_row):
                    if row_idx < len(matrix):
                        row = matrix[row_idx]
                        vals = extract_vals_from_row(row)
                        logger.info(f"   📎[{debug_uuid}] Строка {row_idx + 1} (Дано/Когда/Тогда): {vals}")
                        # Проверяем, что строка не пустая (не все значения пустые)
                        if any(val.strip() for val in vals):
                            rows.append(vals)
                            logger.info(f"   ✅[{debug_uuid}] Строка {row_idx + 1} добавлена в критерии")
                        else:
                            logger.info(f"   ❌[{debug_uuid}] Строка {row_idx + 1} пропущена (пустая)")
                
                # Если не найдено строк критериев, попробуем взять все строки после US
                if not rows:
                    logger.warning(f"⚠️[{debug_uuid}] Не найдено строк критериев для US {us_row_index}, берем все строки после US")
                    for row_idx in range(us_start_row + 1, len(matrix)):
                        row = matrix[row_idx]
                        vals = extract_vals_from_row(row)
                        if any(val.strip() for val in vals):
                            rows.append(vals)
                            logger.info(f"   ✅[{debug_uuid}] Строка {row_idx + 1} добавлена в критерии (fallback)")
            else:
                # Если не указан индекс строки User Story, берем все строки
                logger.info(f"🔍[{debug_uuid}] Индекс строки US не указан, берем все строки")
                for row_idx, row in enumerate(matrix, start=1):
                    vals = extract_vals_from_row(row)
                    if any(val.strip() for val in vals):
                        rows.append(vals)
                        logger.info(f"   ✅[{debug_uuid}] Строка {row_idx} добавлена в критерии (все строки)")
            
            logger.info(f"📈[{debug_uuid}] Всего строк в результирующей таблице: {len(rows)}")
            # 4. Собрать новую таблицу
            html = [
                '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse;width:100%;">',
                '<tr style="background-color:#f0f0f0;"><th style="border:1px solid #000;">Дано</th><th style="border:1px solid #000;">Когда</th><th style="border:1px solid #000;">Тогда</th></tr>'
            ]
            for row in rows:
                html.append('<tr>' + ''.join(f'<td style="border:1px solid #000;">{cell}</td>' for cell in row) + '</tr>')
            html.append('</table>')
            result_html = ''.join(html)
            logger.info(f"✅[{debug_uuid}] Итоговая таблица (обрезано): {result_html[:500]}...")
            
            # Извлечение Given, When, Then для старых полей (если нужно)
            given_conditions = "\n".join([r[0] for r in rows if r[0]])
            when_actions = "\n".join([r[1] for r in rows if r[1]])
            then_results = "\n".join([r[2] for r in rows if r[2]])
            
            return [{"html": result_html}], given_conditions, when_actions, then_results
        # если таблица не найдена, fallback на старую логику
        text = block.get_text()
        logger.info(f"🔍[{debug_uuid}] Поиск критериев в тексте: {text[:200]}...")
        criteria_patterns = [
            r'Критерии приёмки\s*\n(.+?)(?=\n\s*\n|\nTDD|$)',
            r'Критерии приемки\s*\n(.+?)(?=\n\s*\n|\nTDD|$)',
            r'Критерии приёмки\s*:?\s*\n(.+?)(?=\n\s*\n|\nTDD|$)',
            r'Критерии приемки\s*:?\s*\n(.+?)(?=\n\s*\n|\nTDD|$)'
        ]
        for pattern in criteria_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                logger.info(f"✅[{debug_uuid}] Найден текстовый паттерн критериев приёмки")
                criteria_text = match.group(1).strip()
                return [], criteria_text, '', ''
        logger.info(f"❌[{debug_uuid}] Критерии приёмки не найдены")
        return [], '', '', ''
    
    def _format_description(self, user_story_text: str) -> str:
        """Форматирование описания User Story"""
        if not user_story_text:
            return ""
        
        # Убираем лишние пробелы и переносы строк
        formatted = user_story_text.strip()
        
        # Добавляем переносы строк перед ключевыми словами
        formatted = re.sub(r'(я,?\s*как|хочу|чтобы)', r'\n\1', formatted, flags=re.IGNORECASE)
        
        # Убираем лишние переносы в начале
        formatted = formatted.lstrip('\n')
        
        return formatted
    
    def _create_preview(self, page_data: ConfluencePageData) -> Dict[str, Any]:
        logger.info(f"🔍 Создание preview для {len(page_data.user_stories)} User Stories")
        team = page_data.team or "Foxtrot"
        area_path = f"Houston\\{team}"
        iteration_path = f"Houston\\{team}"
        preview = {
            "confluence_url": page_data.url,
            "article_title": page_data.title,
            "project": page_data.project,
            "parent_ticket": page_data.tfs_number,
            "wiki_link": page_data.url,
            "user_stories_count": len(page_data.user_stories),
            "team": team,
            "area_path": area_path,
            "iteration_path": iteration_path,
            "user_stories": []
        }
        for i, us in enumerate(page_data.user_stories):
            logger.info(f"🔍 Обработка US {i+1}: title='{us.title}', user_story_text='{us.user_story_text[:50] if us.user_story_text else 'None'}...'")
            logger.info(f"🔍 given_conditions: '{us.given_conditions[:100] if us.given_conditions else 'None'}...'")
            logger.info(f"🔍 acceptance_criteria: {us.acceptance_criteria}")
            # Если acceptance_criteria содержит HTML таблицу, используем её
            acceptance_criteria = []
            if us.acceptance_criteria:
                if isinstance(us.acceptance_criteria, list) and len(us.acceptance_criteria) > 0:
                    # Если это список словарей с HTML
                    if isinstance(us.acceptance_criteria[0], dict) and 'html' in us.acceptance_criteria[0]:
                        acceptance_criteria = [us.acceptance_criteria[0]['html']]
                        logger.info("✅ Используем HTML таблицу из acceptance_criteria[0]['html']")
                    else:
                        acceptance_criteria = [str(item) for item in us.acceptance_criteria]
                        logger.info("✅ Используем acceptance_criteria как список")
                elif isinstance(us.acceptance_criteria, str) and us.acceptance_criteria.strip().startswith('<table'):
                    acceptance_criteria = [us.acceptance_criteria]
                    logger.info("✅ Используем HTML таблицу из acceptance_criteria")
                else:
                    acceptance_criteria = [str(us.acceptance_criteria)]
                    logger.info("✅ Используем acceptance_criteria как строку")
            elif us.given_conditions and us.given_conditions.strip().startswith('<table'):
                acceptance_criteria = [us.given_conditions]
                logger.info("✅ Используем HTML таблицу из given_conditions")
            elif us.given_conditions:
                acceptance_criteria = [us.given_conditions]
                logger.info("✅ Используем given_conditions как текст")
            else:
                acceptance_criteria = []
                logger.warning("⚠️ Критерии приемки не найдены")
            us_preview = {
                "title": us.title or "Без названия",
                "description": us.user_story_text or "Описание отсутствует",
                "acceptance_criteria": acceptance_criteria,
                "us_number": f"US{i+1}",
                "given_conditions": us.given_conditions or "",
                "when_actions": us.when_actions or "",
                "then_results": us.then_results or ""
            }
            preview["user_stories"].append(us_preview)
        logger.info(f"✅ Preview создан успешно с {len(preview['user_stories'])} User Stories")
        return preview
    
    def _is_confirmation_positive(self, confirmation: str) -> bool:
        """Проверка положительного подтверждения пользователя"""
        positive_keywords = ['да', 'создать', 'подтвердить', 'yes', 'create', 'confirm']
        negative_keywords = ['нет', 'отмена', 'неверно', 'отменить', 'no', 'cancel', 'wrong']
        
        confirmation_lower = confirmation.lower().strip()
        
        # Проверяем на положительные ключевые слова
        for keyword in positive_keywords:
            if keyword in confirmation_lower:
                return True
        
        # Проверяем на отрицательные ключевые слова
        for keyword in negative_keywords:
            if keyword in confirmation_lower:
                return False
        
        # Если не найдено ни положительных, ни отрицательных ключевых слов,
        # считаем подтверждение положительным по умолчанию
                return True
        
    def _extract_table_columns(self, table: BeautifulSoup) -> Dict[str, str]:
        """Извлечение только нужных колонок из таблицы критериев приемки"""
        try:
            # Находим заголовки таблицы
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            logger.info(f"🔍 Заголовки таблицы: {headers}")
            
            # Определяем индексы нужных колонок
            index_dano = None
            index_kogda = None
            index_togda = None
            
            for i, header in enumerate(headers):
                if 'дано' in header.lower():
                    index_dano = i
                elif 'когда' in header.lower():
                    index_kogda = i
                elif 'тогда' in header.lower():
                    index_togda = i
            
            # Если не найдены по названиям, используем фиксированные индексы (3, 4, 5 колонки)
            if index_dano is None or index_kogda is None or index_togda is None:
                logger.info("🔍 Колонки не найдены по названиям, используем фиксированные индексы")
                index_dano = 2  # 3-я колонка (индекс 2)
                index_kogda = 3  # 4-я колонка (индекс 3)
                index_togda = 4  # 5-я колонка (индекс 4)
            
            logger.info(f"✅ Используем индексы колонок: Дано={index_dano}, Когда={index_kogda}, Тогда={index_togda}")
            
            given_data = []
            when_data = []
            then_data = []
            
            # Обрабатываем все строки данных (пропускаем заголовок)
            for tr in table.find_all("tr")[1:]:
                cells = tr.find_all(["td", "th"])
                logger.info(f"🔍 Строка: {len(cells)} ячеек")
                
                # Корректируем индексы с учетом rowspan
                # Если в строке меньше ячеек, чем ожидается, это означает, что предыдущие ячейки имеют rowspan
                actual_index_dano = index_dano
                actual_index_kogda = index_kogda
                actual_index_togda = index_togda
                
                # Вычисляем, сколько ячеек с rowspan из предыдущих строк все еще активны
                if len(cells) < 5:  # Ожидаем 5 колонок
                    missing_cells = 5 - len(cells)
                    actual_index_dano = max(0, index_dano - missing_cells)
                    actual_index_kogda = max(0, index_kogda - missing_cells)
                    actual_index_togda = max(0, index_togda - missing_cells)
                    logger.info(f"🔍 Корректировка индексов: missing={missing_cells}, Дано={actual_index_dano}, Когда={actual_index_kogda}, Тогда={actual_index_togda}")
                
                # Извлекаем нужные колонки по скорректированным индексам
                if len(cells) > max(actual_index_dano, actual_index_kogda, actual_index_togda):
                    given_text = cells[actual_index_dano].get_text(strip=True) if actual_index_dano < len(cells) else ""
                    when_text = cells[actual_index_kogda].get_text(strip=True) if actual_index_kogda < len(cells) else ""
                    then_text = cells[actual_index_togda].get_text(strip=True) if actual_index_togda < len(cells) else ""
                    
                    logger.info(f"🔍 Извлечено: Дано='{given_text[:50]}...', Когда='{when_text[:50]}...', Тогда='{then_text[:50]}...'")
                    
                    # Фильтруем пустые значения и заголовки
                    if given_text and given_text.lower() not in ['дано', 'given']:
                        given_data.append(given_text)
                    if when_text and when_text.lower() not in ['когда', 'when']:
                        when_data.append(when_text)
                    if then_text and then_text.lower() not in ['тогда', 'then']:
                        then_data.append(then_text)
                else:
                    logger.warning(f"⚠️ В строке недостаточно ячеек: {len(cells)} < {max(actual_index_dano, actual_index_kogda, actual_index_togda) + 1}")
            
            # Объединяем данные по строкам (каждая строка на новой строке)
            result = {
                'given': '\n'.join(given_data) if given_data else '',
                'when': '\n'.join(when_data) if when_data else '',
                'then': '\n'.join(then_data) if then_data else ''
            }
            
            logger.info(f"✅ Извлечены данные: Дано={len(result['given'])} символов, Когда={len(result['when'])} символов, Тогда={len(result['then'])} символов")
            return result
                
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении колонок таблицы: {str(e)}")
            return {}

    def _format_acceptance_criteria_html(self, criteria: List[str]) -> str:
        """Форматирование критериев приёмки в HTML"""
        if not criteria:
            return ""
        
        html_parts = ["<h4>Критерии приёмки:</h4><ul>"]
        
        for criterion in criteria:
            html_parts.append(f"<li>{criterion}</li>")
        
        html_parts.append("</ul>")
        return "".join(html_parts)
    
    async def _create_user_stories_in_tfs(self, page_data: ConfluencePageData) -> Dict[str, Any]:
        """Создание User Stories в TFS"""
        created_stories = []
        errors = []
        
        for us in page_data.user_stories:
            try:
                # Создание User Story
                story_id = await self._create_single_user_story(us, page_data)
                if story_id:
                    created_stories.append(story_id)
                    logger.info(f"✅ User Story {us.title} создана с ID: {story_id}")
                else:
                    errors.append(f"Не удалось создать User Story {us.title}")
            except Exception as e:
                error_msg = f"Ошибка при создании User Story {us.title}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        if created_stories:
            return {
                "success": True,
                "created_stories": created_stories,
                "errors": errors,
                "message": f"Создано {len(created_stories)} User Stories"
            }
        else:
            return {
                "success": False,
                "created_stories": [],
                "errors": errors,
                "message": "Не удалось создать ни одной User Story"
            }

    async def _create_single_user_story(self, us: UserStoryData, page_data: ConfluencePageData) -> Optional[int]:
        """Создание одной User Story в TFS"""
        try:
            # Импортируем правильную модель для TFS
            from app.models.request_models import UserStoryData as TFSUserStoryData
            
            # Получаем проект из родительского тикета
            parent_project = await self._get_parent_project(page_data.tfs_number)
            project = parent_project if parent_project else page_data.project
        
            # Подготовка данных для создания User Story
            story_data = TFSUserStoryData(
                title=us.title,
                description=us.user_story_text,
                project=project,
                parent_work_item_id=int(page_data.tfs_number) if page_data.tfs_number else None,
                user_story_text=us.user_story_text,
                given_conditions=us.given_conditions,
                when_actions=us.when_actions,
                then_results=us.then_results,
                acceptance_criteria=us.acceptance_criteria,
                tags=[]  # Убираем теги
            )
            
            # Создание User Story в TFS
            parent_tfs_id = int(page_data.tfs_number) if page_data.tfs_number else None
            logger.info(f"🔗 Создание User Story с родительским тикетом: {parent_tfs_id}")
            
            story_id = await self.tfs_service.create_user_story(
                story_data=story_data,
                confluence_url=page_data.url,
                parent_tfs_id=parent_tfs_id
            )
            
            if story_id:
                # Комментарий уже добавлен в create_user_story
                # Добавление ссылки на Wiki (временно отключено)
                # await self._add_wiki_link(story_id, page_data.url)
                
                return story_id
            else:
                logger.error(f"❌ Не удалось создать User Story: {us.title}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при создании User Story {us.title}: {str(e)}")
            return None

    async def _add_creation_comment(self, story_id: int, confluence_url: str):
        """Добавление комментария о создании User Story"""
        if confluence_url and confluence_url.strip() and confluence_url != "не указано":
            comment = f"Создан автоматически приложением TCA из статьи: {confluence_url}"
        else:
            comment = "Создан автоматически приложением TCA"
        await self.tfs_service.add_comment(story_id, comment)
    
    async def _get_parent_project(self, tfs_number: str) -> Optional[str]:
        """Получение проекта из родительского тикета"""
        try:
            if not tfs_number:
                return None
                
            # Убираем # если есть
            clean_number = tfs_number.replace('#', '')
            parent_id = int(clean_number)
            
            # Получаем информацию о родительском тикете
            parent_work_item = await self.tfs_service.get_work_item(parent_id)
            if parent_work_item and 'fields' in parent_work_item:
                project = parent_work_item['fields'].get('ST.ImplementationProject')
                if project:
                    logger.info(f"✅ Получен проект из родительского тикета #{parent_id}: {project}")
                    return project
                else:
                    logger.warning(f"⚠️ Поле ST.ImplementationProject не найдено в родительском тикете #{parent_id}")
            else:
                logger.warning(f"⚠️ Родительский тикет #{parent_id} не найден")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при получении проекта из родительского тикета: {str(e)}")
        
        return None

    async def _add_wiki_link(self, story_id: int, wiki_url: str):
        """Добавление ссылки на Wiki в User Story"""
        try:
            logger.info(f"🔗 Добавление ссылки на Wiki для User Story {story_id}")
            
            # Используем TFS сервис для обновления Work Item
            await self.tfs_service.update_work_item_field(
                work_item_id=story_id,
                field_path="/fields/System.History",
                value=f"Ссылка на Wiki: {wiki_url}"
            )
            
            logger.info(f"✅ Ссылка на Wiki добавлена к User Story {story_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении ссылки на Wiki к User Story {story_id}: {str(e)}")
    
    async def _update_work_item_history(self, story_id: int, comment: str):
        """Обновление истории Work Item"""
        try:
            await self.tfs_service.add_comment(story_id, comment)
        except Exception as e:
            logger.error(f"Ошибка при добавлении комментария к {story_id}: {str(e)}")
    
    async def _create_parent_link(self, child_id: int, parent_tfs_number: str):
        """Создание связи с родительским тикетом"""
        try:
            parent_id = await self._find_work_item_by_number(parent_tfs_number)
            if parent_id:
                await self.tfs_service.create_work_item_link(
                    source_work_item_id=child_id,
                    target_work_item_id=parent_id,
                    link_type="ST.Backlog.LinkTypes.Hierarchy-Reverse"
                )
                logger.info(f"✅ Создана связь {child_id} -> {parent_id} (Родитель в Backlog)")
            else:
                logger.warning(f"⚠️ Родительский тикет #{parent_tfs_number} не найден")
        except Exception as e:
            logger.error(f"Ошибка при создании связи с родительским тикетом: {str(e)}")
    
    async def _find_work_item_by_number(self, tfs_number: str) -> Optional[int]:
        """Поиск Work Item по номеру"""
        try:
            # Убираем # если есть
            clean_number = tfs_number.replace('#', '')
            work_item_id = int(clean_number)
            
            # Проверяем существование Work Item
            work_item = await self.tfs_service.get_work_item(work_item_id)
            if work_item:
                return work_item_id
            else:
                return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске Work Item #{tfs_number}: {str(e)}")
            return None
    
    async def _log_creation_results(self, creation_result: Dict[str, Any], page_data: ConfluencePageData):
        """Логирование результатов создания"""
        created_stories = creation_result["created_stories"]
        errors = creation_result["errors"]
        
        # Основное логирование
        logger.info(f"✅ User Stories созданы успешно:")
        logger.info(f"   📄 Статья: {page_data.url}")
        logger.info(f"   🔗 Родительский тикет: #{page_data.tfs_number}")
        logger.info(f"   📊 Создано User Stories: {len(created_stories)}")
        
        # Детальное логирование каждой User Story
        for i, story_id in enumerate(created_stories):
            logger.info(f"   📋 US {i+1}: ID {story_id}")
            logger.info(f"      🆔 ID: {story_id}")
            logger.info(f"      🔗 Связан с: #{page_data.tfs_number} (Родитель в Backlog)")
            logger.info(f"      🔗 URL: https://tfssrv.systtech.ru/tfs/DefaultCollection/Houston/_workitems/edit/{story_id}")
        
        # Логирование ошибок
        if errors:
            logger.warning(f"   ⚠️ Ошибки при создании:")
            for error in errors:
                logger.warning(f"      {error}")
        

def extract_criteria_as_json(extracted_data: List[Dict[str, str]]) -> str:
    """
    Преобразует извлеченные данные критериев приемки в JSON формат
    
    Args:
        extracted_data: Список словарей с критериями приемки
        
    Returns:
        str: JSON строка с критериями приемки
    """
    import json
    return json.dumps(extracted_data, ensure_ascii=False, indent=2)


def extract_criteria_as_markdown_table(extracted_data: List[Dict[str, str]]) -> str:
    """
    Преобразует извлеченные данные критериев приемки в Markdown таблицу
    
    Args:
        extracted_data: Список словарей с критериями приемки
        
    Returns:
        str: Markdown таблица с критериями приемки
    """
    if not extracted_data:
        return ""
    
    markdown = "| Дано | Когда | Тогда |\n"
    markdown += "|------|-------|-------|\n"
    
    for row in extracted_data:
        dano = row.get('дано', '').replace('\n', '<br>').replace('|', '\\|')
        kogda = row.get('когда', '').replace('\n', '<br>').replace('|', '\\|') 
        togda = row.get('тогда', '').replace('\n', '<br>').replace('|', '\\|')
        markdown += f"| {dano} | {kogda} | {togda} |\n"
    
    return markdown

# Глобальный экземпляр сервиса
user_story_creator_service = UserStoryCreatorService()
