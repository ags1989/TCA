import logging
from typing import Dict, List, Type, Optional
from app.core.interfaces import IDataExtractor, IDataAnalyzer, IDocumentGenerator, DataSourceType, AnalysisType

logger = logging.getLogger(__name__)

class ExtensionManager:
    """Менеджер расширений для управления различными источниками данных и анализаторами"""
    
    def __init__(self):
        self._extractors: Dict[DataSourceType, IDataExtractor] = {}
        self._analyzers: List[IDataAnalyzer] = []
        self._generators: Dict[str, IDocumentGenerator] = {}
    
    def register_extractor(self, source_type: DataSourceType, extractor: IDataExtractor):
        """Регистрация извлекателя данных"""
        self._extractors[source_type] = extractor
        logger.info(f"Зарегистрирован извлекатель для {source_type}")
    
    def register_analyzer(self, analyzer: IDataAnalyzer):
        """Регистрация анализатора данных"""
        self._analyzers.append(analyzer)
        supported_types = analyzer.get_supported_types()
        logger.info(f"Зарегистрирован анализатор для {supported_types}")
    
    def register_generator(self, name: str, generator: IDocumentGenerator):
        """Регистрация генератора документации"""
        self._generators[name] = generator
        templates = generator.get_available_templates()
        logger.info(f"Зарегистрирован генератор {name} с шаблонами: {templates}")
    
    def get_extractor(self, source_type: DataSourceType) -> Optional[IDataExtractor]:
        """Получение извлекателя для типа источника"""
        return self._extractors.get(source_type)
    
    def get_analyzer(self, analysis_type: AnalysisType) -> Optional[IDataAnalyzer]:
        """Получение анализатора для типа анализа"""
        for analyzer in self._analyzers:
            if analysis_type in analyzer.get_supported_types():
                return analyzer
        return None
    
    def get_generator(self, name: str) -> Optional[IDocumentGenerator]:
        """Получение генератора документации"""
        return self._generators.get(name)
    
    def get_available_sources(self) -> List[DataSourceType]:
        """Получение доступных источников данных"""
        return list(self._extractors.keys())
    
    def get_available_analysis_types(self) -> List[AnalysisType]:
        """Получение доступных типов анализа"""
        types = []
        for analyzer in self._analyzers:
            types.extend(analyzer.get_supported_types())
        return list(set(types))
    
    def get_available_generators(self) -> Dict[str, List[str]]:
        """Получение доступных генераторов и их шаблонов"""
        return {name: gen.get_available_templates() 
                for name, gen in self._generators.items()}

# Глобальный экземпляр менеджера расширений
extension_manager = ExtensionManager()
