"""
Optimized Checklist Service with performance improvements
"""

import asyncio
import aiohttp
import base64
import time
import logging
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from app.services.tfs_service import TFSService
from app.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: float = 300  # 5 минут по умолчанию
    
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl

class IntelligentCache:
    """Интеллектуальное кэширование с LRU eviction"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._access_count: Dict[str, int] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Получение из кэша с проверкой TTL"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            if key in self._access_count:
                del self._access_count[key]
            return None
        
        # Увеличиваем счетчик обращений
        self._access_count[key] = self._access_count.get(key, 0) + 1
        return entry.data
    
    def set(self, key: str, data: Any, ttl: float = 300) -> None:
        """Сохранение в кэш с LRU eviction"""
        # Удаляем старые записи если кэш переполнен
        if len(self._cache) >= self._max_size:
            self._evict_lru()
        
        self._cache[key] = CacheEntry(data, time.time(), ttl)
    
    def _evict_lru(self) -> None:
        """Удаление наименее используемых записей"""
        if not self._access_count:
            # Если нет данных об использовании, удаляем случайную запись
            key_to_remove = next(iter(self._cache.keys()))
        else:
            # Удаляем запись с наименьшим количеством обращений
            key_to_remove = min(self._access_count.keys(), key=lambda k: self._access_count[k])
        
        del self._cache[key_to_remove]
        if key_to_remove in self._access_count:
            del self._access_count[key_to_remove]
    
    def clear(self) -> None:
        """Очистка кэша"""
        self._cache.clear()
        self._access_count.clear()

class AsyncTFSService:
    """Асинхронный TFS сервис для оптимизации производительности"""
    
    def __init__(self):
        self.base_url = settings.TFS_URL.rstrip('/')
        self.pat = settings.TFS_PAT
        self.session = None
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Basic {base64.b64encode(f":{self.pat}".encode()).decode()}',
                'Content-Type': 'application/json-patch+json',
                'Accept': 'application/json'
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_work_item_async(self, work_item_id: int) -> Dict[str, Any]:
        """Асинхронное получение work item"""
        url = f"{self.base_url}/_apis/wit/workitems/{work_item_id}?api-version=4.1&$expand=all"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
    
    async def get_work_items_batch_async(self, work_item_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Асинхронное получение множества work items через Batch API"""
        if not work_item_ids:
            return {}
        
        try:
            # Используем Batch API для получения множества элементов
            batch_url = f"{self.base_url}/_apis/wit/workitemsbatch"
            batch_data = {
                "ids": work_item_ids,
                "fields": ["System.Id", "System.Title", "System.WorkItemType", "System.Description", "System.Relations"]
            }
            
            async with self.session.post(batch_url, json=batch_data) as response:
                if response.status == 200:
                    batch_result = await response.json()
                    work_items = batch_result.get("value", [])
                    
                    # Обрабатываем результаты
                    results = {}
                    for item in work_items:
                        item_id = item.get("id")
                        if item_id:
                            results[item_id] = item
                    
                    logger.info(f"✅ Batch loaded {len(results)} work items")
                    return results
                else:
                    logger.warning(f"Batch API failed: {response.status}")
                    return await self._fallback_individual_requests(work_item_ids)
                    
        except Exception as e:
            logger.error(f"Batch API error: {e}")
            return await self._fallback_individual_requests(work_item_ids)
    
    async def _fallback_individual_requests(self, work_item_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Fallback к индивидуальным запросам при ошибке Batch API"""
        results = {}
        
        # Параллельные запросы с ограничением concurrency
        semaphore = asyncio.Semaphore(5)  # Максимум 5 одновременных запросов
        
        async def fetch_item(item_id):
            async with semaphore:
                try:
                    item = await self.get_work_item_async(item_id)
                    return item_id, item
                except Exception as e:
                    logger.error(f"Error fetching item {item_id}: {e}")
                    return item_id, None
        
        tasks = [fetch_item(item_id) for item_id in work_item_ids]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results_list:
            if isinstance(result, tuple) and result[1] is not None:
                results[result[0]] = result[1]
        
        return results

class OptimizedWIQLService:
    """Оптимизированный сервис для WIQL запросов"""
    
    def __init__(self, async_tfs_service: AsyncTFSService):
        self.async_tfs_service = async_tfs_service
    
    async def search_work_items_optimized(self, search_terms: List[str], work_item_types: List[str]) -> Set[str]:
        """Оптимизированный поиск work items одним WIQL запросом"""
        if not search_terms or not work_item_types:
            return set()
        
        # Создаем один комплексный WIQL запрос
        work_item_type_condition = " OR ".join([f"[System.WorkItemType] = '{wt}'" for wt in work_item_types])
        search_condition = " OR ".join([f"([System.Title] CONTAINS '{term}' OR [System.Description] CONTAINS '{term}')" for term in search_terms])
        
        wiql_query = f"""
        SELECT [System.Id], [System.Title], [System.WorkItemType]
        FROM WorkItems 
        WHERE ({work_item_type_condition})
        AND ({search_condition})
        ORDER BY [System.ChangedDate] DESC
        """
        
        try:
            url = f"{self.async_tfs_service.base_url}/_apis/wit/wiql"
            params = {"api-version": "4.1"}
            
            # Выполняем запрос
            async with self.async_tfs_service.session.post(
                url, 
                params=params, 
                json={"query": wiql_query}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    work_items = data.get("workItems", [])
                    
                    # Возвращаем URL'ы
                    urls = set()
                    for item in work_items:
                        item_id = item.get("id")
                        if item_id:
                            urls.add(f"{settings.TFS_URL}/_workitems/edit/{item_id}")
                    
                    logger.info(f"✅ WIQL search found {len(urls)} items")
                    return urls
                else:
                    logger.error(f"WIQL query failed: {response.status}")
                    return set()
                    
        except Exception as e:
            logger.error(f"WIQL query error: {e}")
            return set()

def performance_monitor(func):
    """Декоратор для мониторинга производительности"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"✅ {func.__name__} completed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper

class OptimizedChecklistService:
    """Оптимизированный сервис для создания чек-листов с улучшенной производительностью"""
    
    def __init__(self):
        self.tfs_service = TFSService()
        self.cache = IntelligentCache(max_size=1000)
        self._log_lock = asyncio.Lock()
    
    async def _log_debug(self, text: str):
        """Асинхронное логирование"""
        try:
            async with self._log_lock:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._write_log_sync, text)
        except Exception as e:
            logger.error(f"Ошибка при записи в checklist_debug.log: {e}")
    
    def _write_log_sync(self, text: str):
        """Синхронная запись в лог"""
        with open("checklist_debug.log", "a", encoding="utf-8") as debug_log:
            debug_log.write(text if text.endswith("\n") else text + "\n")
    
    @performance_monitor
    async def create_checklist_optimized(self, work_item_id: int) -> str:
        """Создание оптимизированного чек-листа с параллельной обработкой"""
        try:
            logger.info(f"Creating optimized checklist for work item ID: {work_item_id}")
            await self._log_debug(f"\n=== OPTIMIZED CHECKLIST for {work_item_id} at {datetime.now().isoformat()} ===\n")
            
            # 1. Получаем все связанные work items (оптимизированно)
            all_items = await self._get_all_related_work_items_optimized(work_item_id)
            
            # 2. Подготавливаем поисковые параметры
            user_story_ids = {str(wi["id"]) for wi in all_items if wi.get("work_item_type", "").lower() == "user story"}
            user_story_titles = {wi["title"] for wi in all_items if wi.get("work_item_type", "").lower() == "user story"}
            all_work_item_ids = [wi["id"] for wi in all_items]
            
            await self._log_debug(f"Found {len(all_items)} work items, {len(user_story_ids)} user stories\n")
            
            # 3. Параллельный поиск всех типов элементов
            async with AsyncTFSService() as async_tfs:
                wiql_service = OptimizedWIQLService(async_tfs)
                
                search_tasks = [
                    self._search_test_plans_parallel(wiql_service, all_work_item_ids, user_story_ids, user_story_titles),
                    self._search_integration_tests_parallel(wiql_service, all_work_item_ids),
                    self._search_bugs_parallel(wiql_service, all_work_item_ids, user_story_ids, user_story_titles)
                ]
                
                # Выполняем все поиски параллельно
                results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                test_plan_urls = results[0] if not isinstance(results[0], Exception) else set()
                integration_test_urls = results[1] if not isinstance(results[1], Exception) else set()
                bug_urls = results[2] if not isinstance(results[2], Exception) else set()
            
            # 4. Формируем чек-лист
            checklist = self._format_checklist(test_plan_urls, integration_test_urls, bug_urls)
            
            await self._log_debug(f"Optimized checklist result:\n{checklist}\n")
            logger.info(f"✅ Optimized checklist created successfully")
            return checklist
            
        except Exception as e:
            logger.error(f"Error creating optimized checklist: {e}")
            await self._log_debug(f"Error creating optimized checklist: {e}\n")
            return f"Ошибка при создании чек-листа: {e}"
    
    async def _get_all_related_work_items_optimized(self, work_item_id: int) -> List[Dict[str, Any]]:
        """Оптимизированное получение всех связанных work items"""
        try:
            # Проверяем кэш
            cache_key = f"related_items_{work_item_id}"
            cached_items = self.cache.get(cache_key)
            if cached_items:
                logger.debug(f"Cache hit for related items of {work_item_id}")
                return cached_items
            
            # Получаем основной work item
            main_item = await self.tfs_service.get_work_item(work_item_id)
            all_items = [{
                "id": main_item.id,
                "title": main_item.title,
                "work_item_type": main_item.work_item_type,
                "project": getattr(main_item, 'project', 'Backlog')
            }]
            
            # Получаем ID связанных элементов
            related_ids = set()
            for rel in getattr(main_item, 'relations', []) or []:
                url = rel.get("url", "")
                if url and not url.endswith("workItems/"):
                    try:
                        rel_id = int(url.split("/")[-1])
                        related_ids.add(rel_id)
                    except (ValueError, IndexError):
                        continue
            
            # Получаем связанные элементы батчем
            if related_ids:
                async with AsyncTFSService() as async_tfs:
                    related_items = await async_tfs.get_work_items_batch_async(list(related_ids))
                    
                    for item_id, item_data in related_items.items():
                        all_items.append({
                            "id": item_id,
                            "title": item_data.get("fields", {}).get("System.Title", ""),
                            "work_item_type": item_data.get("fields", {}).get("System.WorkItemType", ""),
                            "project": "Backlog"  # Можно извлечь из item_data если нужно
                        })
            
            # Кэшируем результат на 5 минут
            self.cache.set(cache_key, all_items, ttl=300)
            
            logger.info(f"Found {len(all_items)} related work items")
            return all_items
            
        except Exception as e:
            logger.error(f"Error getting related work items: {e}")
            return []
    
    async def _search_test_plans_parallel(self, wiql_service: OptimizedWIQLService, work_item_ids: List[int], user_story_ids: Set[str], user_story_titles: Set[str]) -> Set[str]:
        """Параллельный поиск тест-планов"""
        search_terms = list(user_story_ids) + list(user_story_titles)
        work_item_types = ["Тестовый случай", "План тестирования", "Test Case", "Test Plan"]
        
        return await wiql_service.search_work_items_optimized(search_terms, work_item_types)
    
    async def _search_integration_tests_parallel(self, wiql_service: OptimizedWIQLService, work_item_ids: List[int]) -> Set[str]:
        """Параллельный поиск интеграционных тестов"""
        search_terms = ["integration test", "интеграционный тест", "e2e test", "end-to-end test"]
        work_item_types = ["Тестовый случай", "Test Case"]
        
        return await wiql_service.search_work_items_optimized(search_terms, work_item_types)
    
    async def _search_bugs_parallel(self, wiql_service: OptimizedWIQLService, work_item_ids: List[int], user_story_ids: Set[str], user_story_titles: Set[str]) -> Set[str]:
        """Параллельный поиск багов"""
        search_terms = list(user_story_ids) + list(user_story_titles)
        work_item_types = ["Ошибка", "Bug"]
        
        return await wiql_service.search_work_items_optimized(search_terms, work_item_types)
    
    def _format_checklist(self, test_plan_urls: Set[str], integration_test_urls: Set[str], bug_urls: Set[str]) -> str:
        """Форматирование чек-листа"""
        checklist = "## БДК ЗЗЛ - Чек-лист\n\n"
        
        if test_plan_urls:
            checklist += "### 📋 Тест-планы\n"
            for url in sorted(test_plan_urls):
                checklist += f"- [ ] [Тест-план]({url})\n"
            checklist += "\n"
        
        if integration_test_urls:
            checklist += "### 🔗 Интеграционные тесты\n"
            for url in sorted(integration_test_urls):
                checklist += f"- [ ] [Интеграционный тест]({url})\n"
            checklist += "\n"
        
        if bug_urls:
            checklist += "### 🐛 Связанные баги\n"
            for url in sorted(bug_urls):
                checklist += f"- [ ] [Баг]({url})\n"
            checklist += "\n"
        
        if not any([test_plan_urls, integration_test_urls, bug_urls]):
            checklist += "### ℹ️ Информация\n"
            checklist += "Связанные элементы не найдены.\n"
        
        return checklist

# Глобальный экземпляр
optimized_checklist_service = OptimizedChecklistService()
