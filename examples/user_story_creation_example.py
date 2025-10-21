"""
Пример использования API для создания User Stories из Confluence

Этот скрипт демонстрирует, как использовать новый API для создания
User Stories на основе страниц Confluence.
"""

import requests
import json
from typing import Dict, Any

# Базовый URL API
BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_user_stories_from_confluence(confluence_url: str) -> Dict[str, Any]:
    """
    Создание User Stories из страницы Confluence
    
    Args:
        confluence_url: URL страницы Confluence
        
    Returns:
        Результат операции
    """
    
    # Шаг 1: Получение предварительного просмотра
    print(f"🔍 Анализ страницы Confluence: {confluence_url}")
    
    preview_response = requests.post(
        f"{BASE_URL}/user-stories/create-from-confluence",
        json={"confluence_url": confluence_url}
    )
    
    if preview_response.status_code != 200:
        print(f"❌ Ошибка при получении предварительного просмотра: {preview_response.text}")
        return {"success": False, "error": "Ошибка API"}
    
    preview_data = preview_response.json()
    
    if not preview_data["success"]:
        print(f"❌ Ошибка: {preview_data.get('error', 'Неизвестная ошибка')}")
        return preview_data
    
    if preview_data.get("needs_confirmation", False):
        # Показываем предварительный просмотр
        print("\n📋 Предварительный просмотр User Stories:")
        print("=" * 60)
        
        preview = preview_data["preview"]
        print(f"📄 Статья: {preview['confluence_url']}")
        print(f"🏷️ Проект: {preview['project']}")
        print(f"🔗 Родительский тикет: #{preview['parent_ticket']}")
        print(f"📊 Найдено User Stories: {preview['user_stories_count']}")
        print()
        
        for i, us in enumerate(preview["user_stories"], 1):
            print(f"┌─ US{i}: {us['title']}")
            print(f"├─ Описание: {us['description']}")
            print(f"├─ Критерии приёмки:")
            for criterion in us['acceptance_criteria']:
                print(f"│  • {criterion}")
            print(f"└─ Номер: {us['us_number']}")
            print()
        
        # Запрашиваем подтверждение у пользователя
        confirmation = input("❓ Создать указанные User Stories в TFS? (Да/Нет): ")
        
        if confirmation.lower() in ['да', 'yes', 'создать', 'create']:
            # Подтверждаем создание
            print("\n✅ Подтверждение получено. Создание User Stories...")
            
            confirm_response = requests.post(
                f"{BASE_URL}/user-stories/confirm-creation",
                params={
                    "confluence_url": confluence_url,
                    "user_confirmation": confirmation
                }
            )
            
            if confirm_response.status_code != 200:
                print(f"❌ Ошибка при подтверждении: {confirm_response.text}")
                return {"success": False, "error": "Ошибка подтверждения"}
            
            result = confirm_response.json()
            
            if result["success"]:
                print("\n🎉 User Stories успешно созданы!")
                print("=" * 60)
                
                for story in result["created_stories"]:
                    print(f"📋 {story['us_number']}: {story['title']}")
                    print(f"   🆔 ID: {story['id']}")
                    print(f"   🔗 URL: {story['url']}")
                    print()
                
                print(f"🔗 Родительский тикет: #{result['parent_ticket']}")
                print(f"📄 Статья Confluence: {result['confluence_url']}")
                
                return result
            else:
                print(f"❌ Ошибка при создании: {result.get('error', 'Неизвестная ошибка')}")
                return result
        else:
            print("❌ Операция отменена пользователем")
            return {"success": False, "error": "Операция отменена"}
    
    return preview_data

def test_api_health():
    """Проверка состояния API"""
    try:
        response = requests.get(f"{BASE_URL}/user-stories/health")
        if response.status_code == 200:
            print("✅ API User Stories работает корректно")
            return True
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Пример создания User Stories из Confluence")
    print("=" * 60)
    
    # Проверяем состояние API
    if not test_api_health():
        return
    
    # URL страницы Confluence для тестирования
    confluence_url = "https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861"
    
    print(f"\n📄 Тестирование с URL: {confluence_url}")
    
    # Создаем User Stories
    result = create_user_stories_from_confluence(confluence_url)
    
    if result["success"]:
        print("\n✅ Операция завершена успешно!")
    else:
        print(f"\n❌ Операция завершена с ошибкой: {result.get('error', 'Неизвестная ошибка')}")

if __name__ == "__main__":
    main()
