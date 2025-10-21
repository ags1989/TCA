import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.interfaces import IDataExtractor, DataItem, RelatedItem, DataSourceType
from app.models.extended_models import TFSWorkItem
from app.services.tfs_service import TFSService

logger = logging.getLogger(__name__)

class TFSExtractor(IDataExtractor):
    """Извлекатель данных из TFS/Azure DevOps"""
    
    def __init__(self, tfs_service: TFSService):
        self.tfs_service = tfs_service
    
    async def extract_item(self, item_id: str) -> Optional[DataItem]:
        """Извлечение рабочего элемента из TFS"""
        try:
            # Получаем детальную информацию о рабочем элементе
            work_item = await self._get_work_item_details(int(item_id))
            if not work_item:
                return None
            
            return DataItem(
                id=str(work_item.id),
                title=work_item.title,
                content=f"{work_item.description}\n\nТип: {work_item.work_item_type}\nСостояние: {work_item.state}",
                source_type=DataSourceType.TFS,
                url=f"{self.tfs_service.base_url}/{self.tfs_service.project}/_workitems/edit/{work_item.id}",
                metadata={
                    "work_item_type": work_item.work_item_type,
                    "state": work_item.state,
                    "assigned_to": work_item.assigned_to,
                    "story_points": work_item.story_points,
                    "priority": work_item.priority,
                    "tags": work_item.tags,
                    "area_path": work_item.area_path
                },
                created_date=work_item.created_date.isoformat(),
                updated_date=work_item.changed_date.isoformat()
            )
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении элемента TFS {item_id}: {e}")
            return None
    
    async def search_items(self, query: str, filters: Dict[str, Any] = None) -> List[DataItem]:
        """Поиск рабочих элементов в TFS"""
        try:
            # Формируем WIQL запрос
            wiql_query = self._build_wiql_query(query, filters or {})
            work_items = await self._execute_wiql_query(wiql_query)
            
            result = []
            for wi in work_items:
                item = await self.extract_item(str(wi.id))
                if item:
                    result.append(item)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при поиске в TFS: {e}")
            return []
    
    async def get_related_items(self, item_id: str) -> List[RelatedItem]:
        """Получение связанных элементов"""
        try:
            work_item = await self._get_work_item_details(int(item_id))
            if not work_item:
                return []
            
            related_items = []
            
            # Родительские элементы
            if work_item.parent_id:
                parent_item = await self.extract_item(str(work_item.parent_id))
                if parent_item:
                    related_items.append(RelatedItem(
                        item=parent_item,
                        relation_type="parent"
                    ))
            
            # Дочерние элементы
            for child_id in work_item.child_ids:
                child_item = await self.extract_item(str(child_id))
                if child_item:
                    related_items.append(RelatedItem(
                        item=child_item,
                        relation_type="child"
                    ))
            
            # Связанные элементы
            for related_id in work_item.related_ids:
                related_item = await self.extract_item(str(related_id))
                if related_item:
                    related_items.append(RelatedItem(
                        item=related_item,
                        relation_type="related"
                    ))
            
            return related_items
            
        except Exception as e:
            logger.error(f"Ошибка при получении связанных элементов TFS: {e}")
            return []
    
    async def _get_work_item_details(self, work_item_id: int) -> Optional[TFSWorkItem]:
        """Получение детальной информации о рабочем элементе"""
        # Здесь должна быть реализация получения данных через TFS API
        # Возвращаем заглушку для примера
        return None
    
    def _build_wiql_query(self, query: str, filters: Dict[str, Any]) -> str:
        """Построение WIQL запроса"""
        base_query = f"""
        SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State]
        FROM WorkItems 
        WHERE [System.TeamProject] = '{self.tfs_service.project}'
        """
        
        if query:
            base_query += f" AND [System.Title] CONTAINS '{query}'"
        
        if "work_item_types" in filters:
            types = "', '".join(filters["work_item_types"])
            base_query += f" AND [System.WorkItemType] IN ('{types}')"
        
        if "states" in filters:
            states = "', '".join(filters["states"])
            base_query += f" AND [System.State] IN ('{states}')"
        
        return base_query
    
    async def _execute_wiql_query(self, query: str) -> List[TFSWorkItem]:
        """Выполнение WIQL запроса"""
        # Здесь должна быть реализация выполнения WIQL запроса
        return []
