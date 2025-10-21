"""
Справочник типов связей TFS/Azure DevOps
"""
from enum import Enum
from typing import Dict, List, Set


class LinkType(Enum):
    """Типы связей в TFS/Azure DevOps"""
    
    # Стандартные иерархические связи
    HIERARCHY_FORWARD = "System.LinkTypes.Hierarchy-Forward"
    HIERARCHY_REVERSE = "System.LinkTypes.Hierarchy-Reverse"
    
    # Связи зависимостей
    DEPENDENCY_FORWARD = "System.LinkTypes.Dependency-Forward"
    DEPENDENCY_REVERSE = "System.LinkTypes.Dependency-Reverse"
    
    # Связанные элементы
    RELATED = "System.LinkTypes.Related"
    
    # Кастомные связи ST.Backlog
    ST_BACKLOG_HIERARCHY_FORWARD = "ST.Backlog.LinkTypes.Hierarchy-Forward"
    ST_BACKLOG_HIERARCHY_REVERSE = "ST.Backlog.LinkTypes.Hierarchy-Reverse"
    
    # Связи с файлами
    ATTACHED_FILE = "AttachedFile"
    
    # Связи с ветками
    BRANCH = "System.LinkTypes.Branch"
    
    # Связи с изменениями
    CHANGESET = "System.LinkTypes.Changeset"
    
    # Связи с коммитами
    COMMIT = "System.LinkTypes.Commit"
    
    # Связи с pull requests
    PULL_REQUEST = "System.LinkTypes.PullRequest"


class LinkDirection(Enum):
    """Направления связей"""
    FORWARD = "forward"  # Исходящая связь (родитель -> дочерний)
    REVERSE = "reverse"  # Входящая связь (дочерний -> родитель)
    BIDIRECTIONAL = "bidirectional"  # Двунаправленная связь


class LinkCategory(Enum):
    """Категории связей"""
    HIERARCHY = "hierarchy"  # Иерархические связи
    DEPENDENCY = "dependency"  # Связи зависимостей
    RELATED = "related"  # Связанные элементы
    ATTACHMENT = "attachment"  # Вложения
    VERSION_CONTROL = "version_control"  # Система контроля версий
    CUSTOM = "custom"  # Кастомные связи


# Справочник типов связей с их характеристиками
LINK_TYPES_INFO: Dict[LinkType, Dict] = {
    LinkType.HIERARCHY_FORWARD: {
        "name": "Дочерний элемент",
        "direction": LinkDirection.FORWARD,
        "category": LinkCategory.HIERARCHY,
        "description": "Стандартная иерархическая связь (родитель -> дочерний)",
        "search_fields": ["System.Links.SourceWorkItemId"],
        "reverse_type": LinkType.HIERARCHY_REVERSE
    },
    
    LinkType.HIERARCHY_REVERSE: {
        "name": "Родительское",
        "direction": LinkDirection.REVERSE,
        "category": LinkCategory.HIERARCHY,
        "description": "Обратная иерархическая связь (дочерний -> родитель)",
        "search_fields": ["System.Links.TargetWorkItemId"],
        "reverse_type": LinkType.HIERARCHY_FORWARD
    },
    
    LinkType.ST_BACKLOG_HIERARCHY_FORWARD: {
        "name": "Дочерний в продукте",
        "direction": LinkDirection.FORWARD,
        "category": LinkCategory.CUSTOM,
        "description": "Кастомная иерархическая связь ST.Backlog (родитель -> дочерний)",
        "search_fields": ["System.Links.SourceWorkItemId"],
        "reverse_type": LinkType.ST_BACKLOG_HIERARCHY_REVERSE
    },
    
    LinkType.ST_BACKLOG_HIERARCHY_REVERSE: {
        "name": "Родитель в backlog",
        "direction": LinkDirection.REVERSE,
        "category": LinkCategory.CUSTOM,
        "description": "Обратная кастомная иерархическая связь ST.Backlog (дочерний -> родитель)",
        "search_fields": ["System.Links.TargetWorkItemId"],
        "reverse_type": LinkType.ST_BACKLOG_HIERARCHY_FORWARD
    },
    
    LinkType.RELATED: {
        "name": "Связанные",
        "direction": LinkDirection.BIDIRECTIONAL,
        "category": LinkCategory.RELATED,
        "description": "Связь между связанными элементами",
        "search_fields": ["System.Links.TargetWorkItemId", "System.Links.SourceWorkItemId"],
        "reverse_type": LinkType.RELATED
    },
    
    LinkType.DEPENDENCY_FORWARD: {
        "name": "Последователь",
        "direction": LinkDirection.FORWARD,
        "category": LinkCategory.DEPENDENCY,
        "description": "Связь зависимости (предшественник -> последователь)",
        "search_fields": ["System.Links.SourceWorkItemId"],
        "reverse_type": LinkType.DEPENDENCY_REVERSE
    },
    
    LinkType.DEPENDENCY_REVERSE: {
        "name": "Предшественник",
        "direction": LinkDirection.REVERSE,
        "category": LinkCategory.DEPENDENCY,
        "description": "Обратная связь зависимости (последователь -> предшественник)",
        "search_fields": ["System.Links.TargetWorkItemId"],
        "reverse_type": LinkType.DEPENDENCY_FORWARD
    },
    
    LinkType.ATTACHED_FILE: {
        "name": "Вложение",
        "direction": LinkDirection.FORWARD,
        "category": LinkCategory.ATTACHMENT,
        "description": "Связь с прикрепленным файлом",
        "search_fields": ["System.Links.TargetWorkItemId"],
        "reverse_type": None
    },
    
    LinkType.BRANCH: {
        "name": "Ветка",
        "direction": LinkDirection.FORWARD,
        "category": LinkCategory.VERSION_CONTROL,
        "description": "Связь с веткой Git",
        "search_fields": ["System.Links.TargetWorkItemId"],
        "reverse_type": None
    },
    
    LinkType.CHANGESET: {
        "name": "Набор изменений",
        "direction": LinkDirection.FORWARD,
        "category": LinkCategory.VERSION_CONTROL,
        "description": "Связь с набором изменений",
        "search_fields": ["System.Links.TargetWorkItemId"],
        "reverse_type": None
    },
    
    LinkType.COMMIT: {
        "name": "Коммит",
        "direction": LinkDirection.FORWARD,
        "category": LinkCategory.VERSION_CONTROL,
        "description": "Связь с коммитом Git",
        "search_fields": ["System.Links.TargetWorkItemId"],
        "reverse_type": None
    },
    
    LinkType.PULL_REQUEST: {
        "name": "Pull Request",
        "direction": LinkDirection.FORWARD,
        "category": LinkCategory.VERSION_CONTROL,
        "description": "Связь с Pull Request",
        "search_fields": ["System.Links.TargetWorkItemId"],
        "reverse_type": None
    }
}


# Группировка типов связей по категориям
LINK_TYPES_BY_CATEGORY: Dict[LinkCategory, List[LinkType]] = {
    LinkCategory.HIERARCHY: [
        LinkType.HIERARCHY_FORWARD,
        LinkType.HIERARCHY_REVERSE,
        LinkType.ST_BACKLOG_HIERARCHY_FORWARD,
        LinkType.ST_BACKLOG_HIERARCHY_REVERSE
    ],
    LinkCategory.DEPENDENCY: [
        LinkType.DEPENDENCY_FORWARD,
        LinkType.DEPENDENCY_REVERSE
    ],
    LinkCategory.RELATED: [
        LinkType.RELATED
    ],
    LinkCategory.ATTACHMENT: [
        LinkType.ATTACHED_FILE
    ],
    LinkCategory.VERSION_CONTROL: [
        LinkType.BRANCH,
        LinkType.CHANGESET,
        LinkType.COMMIT,
        LinkType.PULL_REQUEST
    ],
    LinkCategory.CUSTOM: [
        LinkType.ST_BACKLOG_HIERARCHY_FORWARD,
        LinkType.ST_BACKLOG_HIERARCHY_REVERSE
    ]
}


# Типы связей для поиска дочерних элементов (багов, тестов и т.д.)
CHILD_SEARCH_LINK_TYPES: List[LinkType] = [
    LinkType.HIERARCHY_FORWARD,
    LinkType.ST_BACKLOG_HIERARCHY_FORWARD
]

# Типы связей для поиска связанных элементов
RELATED_SEARCH_LINK_TYPES: List[LinkType] = [
    LinkType.RELATED,
    LinkType.DEPENDENCY_FORWARD,
    LinkType.DEPENDENCY_REVERSE
]

# Типы связей для поиска багов
BUG_SEARCH_LINK_TYPES: List[LinkType] = [
    LinkType.HIERARCHY_FORWARD,
    LinkType.ST_BACKLOG_HIERARCHY_FORWARD,
    LinkType.RELATED
]

# Типы связей для поиска тестов
TEST_SEARCH_LINK_TYPES: List[LinkType] = [
    LinkType.HIERARCHY_FORWARD,
    LinkType.ST_BACKLOG_HIERARCHY_FORWARD,
    LinkType.RELATED
]


def get_link_type_info(link_type: LinkType) -> Dict:
    """Получить информацию о типе связи"""
    return LINK_TYPES_INFO.get(link_type, {})


def get_link_types_by_category(category: LinkCategory) -> List[LinkType]:
    """Получить типы связей по категории"""
    return LINK_TYPES_BY_CATEGORY.get(category, [])


def get_search_fields_for_link_type(link_type: LinkType) -> List[str]:
    """Получить поля для поиска по типу связи"""
    info = get_link_type_info(link_type)
    return info.get("search_fields", [])


def get_all_search_fields_for_types(link_types: List[LinkType]) -> Set[str]:
    """Получить все поля для поиска для списка типов связей"""
    fields = set()
    for link_type in link_types:
        fields.update(get_search_fields_for_link_type(link_type))
    return fields


def is_hierarchy_link(link_type: LinkType) -> bool:
    """Проверить, является ли связь иерархической"""
    return link_type in LINK_TYPES_BY_CATEGORY[LinkCategory.HIERARCHY]


def is_related_link(link_type: LinkType) -> bool:
    """Проверить, является ли связь связью связанных элементов"""
    return link_type in LINK_TYPES_BY_CATEGORY[LinkCategory.RELATED]


def is_dependency_link(link_type: LinkType) -> bool:
    """Проверить, является ли связь связью зависимостей"""
    return link_type in LINK_TYPES_BY_CATEGORY[LinkCategory.DEPENDENCY]


def get_wiql_condition_for_link_types(link_types: List[LinkType], work_item_ids: List[str], 
                                    direction: LinkDirection = None) -> str:
    """Создать WIQL условие для поиска по типам связей"""
    conditions = []
    
    for link_type in link_types:
        info = get_link_type_info(link_type)
        if not info:
            continue
            
        # Фильтр по направлению, если указан
        if direction and info.get("direction") != direction and info.get("direction") != LinkDirection.BIDIRECTIONAL:
            continue
            
        search_fields = info.get("search_fields", [])
        for field in search_fields:
            if field == "System.Links.SourceWorkItemId":
                conditions.append(f"[System.Links.SourceWorkItemId] IN ({','.join(work_item_ids)})")
            elif field == "System.Links.TargetWorkItemId":
                conditions.append(f"[System.Links.TargetWorkItemId] IN ({','.join(work_item_ids)})")
    
    return " OR ".join(conditions) if conditions else "1=0"


def get_link_type_by_name(name: str) -> LinkType:
    """Найти тип связи по имени"""
    for link_type, info in LINK_TYPES_INFO.items():
        if info.get("name") == name:
            return link_type
    return None
