from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.extended_models import DocumentationRequest, AnalysisConfiguration
from app.models.response_models import DetailedProcessingResult
from app.core.extension_manager import extension_manager
from app.core.interfaces import DataSourceType, AnalysisType

router = APIRouter()

@router.post("/analyze-comprehensive")
async def analyze_comprehensive(
    source_items: List[str],
    analysis_types: List[AnalysisType],
    include_related: bool = True,
    depth_level: int = 2
) -> DetailedProcessingResult:
    """
    Комплексный анализ элементов из различных источников
    """
    
    result = DetailedProcessingResult(
        success=False,
        user_query=f"Анализ {len(source_items)} элементов",
        processing_start=datetime.now(),
        summary="Комплексный анализ не завершен"
    )
    
    try:
        all_items = []
        
        # Извлекаем данные из всех источников
        for item_id in source_items:
            # Определяем тип источника по ID
            source_type = _determine_source_type(item_id)
            extractor = extension_manager.get_extractor(source_type)
            
            if not extractor:
                result.warnings.append(f"Нет извлекателя для {source_type}")
                continue
            
            item = await extractor.extract_item(item_id)
            if item:
                all_items.append(item)
                
                # Получаем связанные элементы если нужно
                if include_related:
                    related_items = await extractor.get_related_items(item_id)
                    for related in related_items[:depth_level]:  # Ограничиваем глубину
                        all_items.append(related.item)
        
        # Выполняем различные типы анализа
        analysis_results = {}
        for analysis_type in analysis_types:
            analyzer = extension_manager.get_analyzer(analysis_type)
            if analyzer:
                analysis_result = await analyzer.analyze(all_items, analysis_type)
                analysis_results[analysis_type.value] = analysis_result
        
        result.extracted_data = analysis_results
        result.summary = f"Успешно проанализировано {len(all_items)} элементов"
        result.success = True
        
        return result
        
    except Exception as e:
        result.summary = f"Ошибка при комплексном анализе: {str(e)}"
        return result

@router.post("/generate-documentation")
async def generate_documentation(request: DocumentationRequest) -> Dict[str, Any]:
    """
    Генерация документации на основе анализа элементов
    """
    
    try:
        # Извлекаем и анализируем данные
        all_items = []
        for item_id in request.source_items:
            source_type = _determine_source_type(item_id)
            extractor = extension_manager.get_extractor(source_type)
            
            if extractor:
                item = await extractor.extract_item(item_id)
                if item:
                    all_items.append(item)
        
        # Анализируем для документации
        analyzer = extension_manager.get_analyzer(AnalysisType.GENERATE_DOCUMENTATION)
        if not analyzer:
            raise HTTPException(status_code=500, detail="Анализатор документации недоступен")
        
        analysis_result = await analyzer.analyze(all_items, AnalysisType.GENERATE_DOCUMENTATION)
        
        # Генерируем документ
        generator = extension_manager.get_generator("markdown")
        if not generator:
            raise HTTPException(status_code=500, detail="Генератор документации недоступен")
        
        document_content = await generator.generate_document(analysis_result, request.template_type)
        
        return {
            "success": True,
            "document_content": document_content,
            "analysis_summary": {
                "items_analyzed": len(all_items),
                "confidence_score": analysis_result.confidence_score,
                "processing_notes": analysis_result.processing_notes
            },
            "metadata": {
                "template": request.template_type,
                "format": request.format,
                "language": request.language,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации документации: {str(e)}")

@router.get("/available-extensions")
async def get_available_extensions():
    """
    Получение списка доступных расширений и их возможностей
    """
    
    return {
        "data_sources": [source.value for source in extension_manager.get_available_sources()],
        "analysis_types": [atype.value for atype in extension_manager.get_available_analysis_types()],
        "document_generators": extension_manager.get_available_generators()
    }

@router.post("/register-configuration")
async def register_configuration(config: AnalysisConfiguration):
    """
    Регистрация конфигурации для анализа
    """
    
    # Здесь можно сохранить конфигурацию и настроить расширения
    return {
        "success": True,
        "message": "Конфигурация зарегистрирована",
        "config": config.dict()
    }

def _determine_source_type(item_id: str) -> DataSourceType:
    """Определение типа источника по ID элемента"""
    
    if item_id.isdigit():
        return DataSourceType.TFS
    elif "/" in item_id and ("github.com" in item_id or "pulls" in item_id or "issues" in item_id):
        return DataSourceType.GITHUB
    elif "confluence" in item_id.lower():
        return DataSourceType.CONFLUENCE
    else:
        return DataSourceType.TFS  # По умолчанию
