from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

class DataSourceType(str, Enum):
    CONFLUENCE = "confluence"
    TFS = "tfs"
    GITHUB = "github" 
    GITLAB = "gitlab"
    JIRA = "jira"
    TESTNG = "testng"
    SELENIUM = "selenium"

class AnalysisType(str, Enum):
    CREATE_TICKETS = "create_tickets"
    GENERATE_DOCUMENTATION = "generate_documentation"
    ANALYZE_COVERAGE = "analyze_coverage"
    SYNC_DATA = "sync_data"
    EXTRACT_REQUIREMENTS = "extract_requirements"

class DataItem(BaseModel):
    """Базовая модель для любого элемента данных"""
    id: str
    title: str
    content: str
    source_type: DataSourceType
    url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_date: Optional[str] = None
    updated_date: Optional[str] = None

class RelatedItem(BaseModel):
    """Связанный элемент"""
    item: DataItem
    relation_type: str  # "parent", "child", "related", "blocks", etc.
    relation_metadata: Dict[str, Any] = {}

class AnalysisResult(BaseModel):
    """Результат анализа данных"""
    source_items: List[DataItem]
    related_items: List[RelatedItem] = []
    extracted_data: Dict[str, Any]
    confidence_score: float
    processing_notes: List[str] = []

class IDataExtractor(ABC):
    """Интерфейс для извлечения данных из различных источников"""
    
    @abstractmethod
    async def extract_item(self, item_id: str) -> Optional[DataItem]:
        """Извлечение одного элемента по ID"""
        pass
    
    @abstractmethod
    async def search_items(self, query: str, filters: Dict[str, Any] = None) -> List[DataItem]:
        """Поиск элементов по запросу"""
        pass
    
    @abstractmethod
    async def get_related_items(self, item_id: str) -> List[RelatedItem]:
        """Получение связанных элементов"""
        pass

class IDataAnalyzer(ABC):
    """Интерфейс для анализа данных"""
    
    @abstractmethod
    async def analyze(self, items: List[DataItem], analysis_type: AnalysisType) -> AnalysisResult:
        """Анализ элементов данных"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[AnalysisType]:
        """Получение поддерживаемых типов анализа"""
        pass

class IDocumentGenerator(ABC):
    """Интерфейс для генерации документации"""
    
    @abstractmethod
    async def generate_document(self, analysis_result: AnalysisResult, template: str) -> str:
        """Генерация документа на основе анализа"""
        pass
    
    @abstractmethod
    def get_available_templates(self) -> List[str]:
        """Получение доступных шаблонов"""
        pass
