from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.interfaces import DataSourceType, AnalysisType

class TFSWorkItem(BaseModel):
    """Расширенная модель рабочего элемента TFS"""
    id: int
    title: str
    work_item_type: str
    state: str
    assigned_to: Optional[str] = None
    description: str
    acceptance_criteria: Optional[str] = None
    
    # Связи
    parent_id: Optional[int] = None
    child_ids: List[int] = []
    related_ids: List[int] = []
    
    # Метаданные
    area_path: str
    iteration_path: Optional[str] = None
    story_points: Optional[int] = None
    priority: int
    tags: List[str] = []
    
    # Временные метки
    created_date: datetime
    changed_date: datetime
    resolved_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    
    # Дополнительные поля
    original_estimate: Optional[float] = None
    remaining_work: Optional[float] = None
    completed_work: Optional[float] = None
    
    # Комментарии и история
    comments: List[Dict[str, Any]] = []
    history: List[Dict[str, Any]] = []

class TestCase(BaseModel):
    """Модель тест-кейса"""
    id: str
    title: str
    description: str
    steps: List[str]
    expected_result: str
    
    # Связи с другими элементами
    related_work_items: List[int] = []
    related_requirements: List[str] = []
    
    # Метаданные теста
    test_suite: Optional[str] = None
    priority: str = "Medium"
    automation_status: str = "Not Automated"  # Manual, Automated, Not Automated
    
    # Результаты выполнения
    last_run_date: Optional[datetime] = None
    last_run_result: Optional[str] = None  # Pass, Fail, Blocked, Not Run
    
    # Дополнительные данные
    environment: Optional[str] = None
    browser: Optional[str] = None
    test_data: Dict[str, Any] = {}

class PullRequest(BaseModel):
    """Модель Pull Request"""
    id: str
    title: str
    description: str
    source_branch: str
    target_branch: str
    author: str
    
    # Статус
    state: str  # Open, Merged, Closed
    is_draft: bool = False
    
    # Связи
    related_work_items: List[int] = []
    fixes_issues: List[str] = []
    
    # Файлы и изменения
    changed_files: List[str] = []
    additions: int = 0
    deletions: int = 0
    
    # Ревью
    reviewers: List[str] = []
    approvals: List[str] = []
    
    # Временные метки
    created_date: datetime
    updated_date: datetime
    merged_date: Optional[datetime] = None
    
    # Дополнительные данные
    labels: List[str] = []
    build_status: Optional[str] = None
    test_results: Dict[str, Any] = {}

class DocumentationRequest(BaseModel):
    """Запрос на создание документации"""
    template_type: str
    source_items: List[str]  # ID элементов для анализа
    include_related: bool = True
    depth_level: int = 2  # Глубина анализа связанных элементов
    
    # Параметры генерации
    language: str = "ru"
    format: str = "markdown"  # markdown, html, pdf, docx
    include_diagrams: bool = True
    include_test_coverage: bool = True
    
    # Фильтры
    date_range: Optional[Dict[str, str]] = None
    work_item_types: List[str] = []
    states: List[str] = []

class AnalysisConfiguration(BaseModel):
    """Конфигурация анализа"""
    enabled_sources: List[DataSourceType]
    analysis_types: List[AnalysisType]
    
    # Настройки AI
    ai_model: str = "gpt-4"
    ai_temperature: float = 0.3
    
    # Настройки извлечения данных
    max_related_depth: int = 3
    include_history: bool = False
    include_attachments: bool = False
    
    # Настройки документации
    default_template: str = "technical_spec"
    include_metrics: bool = True
    generate_diagrams: bool = True
