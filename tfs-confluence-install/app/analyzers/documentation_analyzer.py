import logging
from typing import List, Dict, Any
from app.core.interfaces import IDataAnalyzer, DataItem, AnalysisResult, AnalysisType
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class DocumentationAnalyzer(IDataAnalyzer):
    """Анализатор для создания документации"""
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
    
    def get_supported_types(self) -> List[AnalysisType]:
        return [
            AnalysisType.GENERATE_DOCUMENTATION,
            AnalysisType.EXTRACT_REQUIREMENTS,
            AnalysisType.ANALYZE_COVERAGE
        ]
    
    async def analyze(self, items: List[DataItem], analysis_type: AnalysisType) -> AnalysisResult:
        """Анализ элементов для создания документации"""
        
        if analysis_type == AnalysisType.GENERATE_DOCUMENTATION:
            return await self._analyze_for_documentation(items)
        elif analysis_type == AnalysisType.EXTRACT_REQUIREMENTS:
            return await self._extract_requirements(items)
        elif analysis_type == AnalysisType.ANALYZE_COVERAGE:
            return await self._analyze_coverage(items)
        else:
            raise ValueError(f"Неподдерживаемый тип анализа: {analysis_type}")
    
    async def _analyze_for_documentation(self, items: List[DataItem]) -> AnalysisResult:
        """Анализ элементов для создания технической документации"""
        
        # Группируем элементы по типам
        grouped_items = self._group_items_by_type(items)
        
        # Анализируем каждую группу через OpenAI
        extracted_data = {}
        processing_notes = []
        
        # Анализируем User Stories и требования
        if "User Story" in grouped_items or "requirement" in grouped_items:
            requirements_analysis = await self._analyze_requirements_group(
                grouped_items.get("User Story", []) + grouped_items.get("requirement", [])
            )
            extracted_data["requirements"] = requirements_analysis
            processing_notes.append(f"Проанализировано {len(requirements_analysis.get('items', []))} требований")
        
        # Анализируем задачи и реализацию
        if "Task" in grouped_items:
            tasks_analysis = await self._analyze_tasks_group(grouped_items["Task"])
            extracted_data["implementation"] = tasks_analysis
            processing_notes.append(f"Проанализировано {len(tasks_analysis.get('items', []))} задач")
        
        # Анализируем тесты
        test_items = [item for item in items if "test" in item.title.lower() or "тест" in item.title.lower()]
        if test_items:
            tests_analysis = await self._analyze_tests_group(test_items)
            extracted_data["testing"] = tests_analysis
            processing_notes.append(f"Проанализировано {len(test_items)} тестовых элементов")
        
        # Анализируем архитектуру и дизайн
        architecture_analysis = await self._analyze_architecture(items)
        extracted_data["architecture"] = architecture_analysis
        
        return AnalysisResult(
            source_items=items,
            extracted_data=extracted_data,
            confidence_score=0.85,  # Базовая оценка уверенности
            processing_notes=processing_notes
        )
    
    async def _analyze_requirements_group(self, items: List[DataItem]) -> Dict[str, Any]:
        """Анализ группы требований"""
        
        combined_content = "\n\n".join([f"# {item.title}\n{item.content}" for item in items])
        
        system_prompt = """
        Проанализируй группу требований и извлеки структурированную информацию:
        
        Верни JSON с полями:
        - functional_requirements: список функциональных требований
        - non_functional_requirements: список нефункциональных требований  
        - business_rules: список бизнес-правил
        - acceptance_criteria: список критериев приемки
        - stakeholders: список заинтересованных лиц
        - components_affected: список затрагиваемых компонентов
        - priority_items: приоритизированный список требований
        """
        
        try:
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": combined_content[:4000]}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            result["items"] = items
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при анализе требований: {e}")
            return {"items": items, "error": str(e)}
    
    async def _analyze_tasks_group(self, items: List[DataItem]) -> Dict[str, Any]:
        """Анализ группы задач реализации"""
        
        combined_content = "\n\n".join([f"# {item.title}\n{item.content}" for item in items])
        
        system_prompt = """
        Проанализируй задачи реализации и извлеки:
        
        Верни JSON:
        - implementation_phases: фазы реализации
        - technical_components: технические компоненты
        - dependencies: зависимости между задачами
        - estimated_effort: оценка трудозатрат
        - risk_areas: области риска
        - integration_points: точки интеграции
        """
        
        try:
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": combined_content[:4000]}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            result["items"] = items
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при анализе задач: {e}")
            return {"items": items, "error": str(e)}
    
    async def _analyze_tests_group(self, items: List[DataItem]) -> Dict[str, Any]:
        """Анализ тестового покрытия"""
        
        return {
            "test_coverage": {
                "unit_tests": len([i for i in items if "unit" in i.title.lower()]),
                "integration_tests": len([i for i in items if "integration" in i.title.lower()]),
                "e2e_tests": len([i for i in items if "e2e" in i.title.lower() or "end" in i.title.lower()])
            },
            "test_scenarios": [item.title for item in items],
            "coverage_gaps": [],  # Можно расширить анализом пробелов
            "items": items
        }
    
    async def _analyze_architecture(self, items: List[DataItem]) -> Dict[str, Any]:
        """Анализ архитектурных аспектов"""
        
        # Извлекаем упоминания компонентов и технологий
        all_content = " ".join([item.content for item in items])
        
        system_prompt = """
        Проанализируй технический контент и извлеки архитектурную информацию:
        
        Верни JSON:
        - system_components: список компонентов системы
        - technologies: используемые технологии
        - integration_patterns: паттерны интеграции
        - data_flow: описание потоков данных
        - deployment_considerations: соображения по развертыванию
        """
        
        try:
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": all_content[:3000]}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Ошибка при анализе архитектуры: {e}")
            return {"error": str(e)}
    
    def _group_items_by_type(self, items: List[DataItem]) -> Dict[str, List[DataItem]]:
        """Группировка элементов по типам"""
        
        groups = {}
        for item in items:
            item_type = item.metadata.get("work_item_type", "Unknown")
            if item_type not in groups:
                groups[item_type] = []
            groups[item_type].append(item)
        
        return groups
    
    async def _extract_requirements(self, items: List[DataItem]) -> AnalysisResult:
        """Извлечение требований из элементов"""
        # Реализация извлечения требований
        pass
    
    async def _analyze_coverage(self, items: List[DataItem]) -> AnalysisResult:
        """Анализ покрытия тестами"""
        # Реализация анализа покрытия
        pass
