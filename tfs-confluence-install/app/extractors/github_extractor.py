import logging
from typing import List, Dict, Any, Optional
import aiohttp
from app.core.interfaces import IDataExtractor, DataItem, RelatedItem, DataSourceType
from app.models.extended_models import PullRequest
from app.config.settings import settings

logger = logging.getLogger(__name__)

class GitHubExtractor(IDataExtractor):
    """Извлекатель данных из GitHub"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def extract_item(self, item_id: str) -> Optional[DataItem]:
        """Извлечение PR или Issue из GitHub"""
        try:
            # Парсим ID в формате "owner/repo/pulls/123" или "owner/repo/issues/456"
            parts = item_id.split('/')
            if len(parts) < 4:
                return None
            
            owner, repo, item_type, number = parts[0], parts[1], parts[2], parts[3]
            
            url = f"{self.base_url}/repos/{owner}/{repo}/{item_type}/{number}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    return DataItem(
                        id=item_id,
                        title=data.get("title", ""),
                        content=data.get("body", ""),
                        source_type=DataSourceType.GITHUB,
                        url=data.get("html_url"),
                        metadata={
                            "state": data.get("state"),
                            "author": data.get("user", {}).get("login"),
                            "labels": [label["name"] for label in data.get("labels", [])],
                            "assignees": [assignee["login"] for assignee in data.get("assignees", [])]
                        },
                        created_date=data.get("created_at"),
                        updated_date=data.get("updated_at")
                    )
                    
        except Exception as e:
            logger.error(f"Ошибка при извлечении элемента GitHub {item_id}: {e}")
            return None
    
    async def search_items(self, query: str, filters: Dict[str, Any] = None) -> List[DataItem]:
        """Поиск элементов в GitHub"""
        # Реализация поиска через GitHub Search API
        return []
    
    async def get_related_items(self, item_id: str) -> List[RelatedItem]:
        """Получение связанных элементов из GitHub"""
        # Реализация получения связанных PR, Issues, Commits
        return []
