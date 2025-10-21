"""
Конфигурация pytest для интеграционных тестов
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.services.confluence_service import ConfluenceService
from app.services.tfs_service import TFSService
from app.services.user_story_creator_service import UserStoryCreatorService
from app.models.request_models import UserStoryData, ConfluenceArticle


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всех тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_app():
    """Фикстура для тестового приложения"""
    return app


@pytest.fixture
def mock_confluence_service():
    """Мок Confluence сервиса"""
    service = MagicMock(spec=ConfluenceService)
    service.get_article_by_id = AsyncMock()
    service.get_article_storage_by_id = AsyncMock()
    return service


@pytest.fixture
def mock_tfs_service():
    """Мок TFS сервиса"""
    service = MagicMock(spec=TFSService)
    service.create_user_story = AsyncMock()
    service.get_work_item = AsyncMock()
    service.test_connection = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_user_story_creator_service():
    """Мок User Story Creator сервиса"""
    service = MagicMock(spec=UserStoryCreatorService)
    service.create_user_stories_from_confluence = AsyncMock()
    return service


@pytest.fixture
def sample_confluence_article():
    """Образец статьи Confluence для тестов"""
    return ConfluenceArticle(
        id="123456",
        title="Тестовая статья для User Stories",
        space_key="TEST",
        content="""
        <h1>Тестовая статья для User Stories</h1>
        <p>№TFS: 12345</p>
        <p>Команда: Foxtrot</p>
        <p>Продукт: Test Product</p>
        <p>Тех.лид: tech.lead@example.com</p>
        <p>Разработчики: dev1@example.com, dev2@example.com</p>

        <h2>User Stories</h2>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>US</th>
                <th>Название</th>
                <th>User Story</th>
                <th>Дано</th>
                <th>Когда</th>
                <th>Тогда</th>
            </tr>
            <tr>
                <td>US 1</td>
                <td>Загрузка данных от AI в БД Чикаго</td>
                <td>Я, как пользователь системы, хочу загружать данные от AI в базу данных Чикаго, чтобы они были доступны для анализа</td>
                <td>Пользователь авторизован в системе</td>
                <td>Нажимает кнопку загрузки данных</td>
                <td>Данные загружаются в базу данных Чикаго</td>
            </tr>
            <tr>
                <td>US 2</td>
                <td>Отображение статистики</td>
                <td>Я, как пользователь системы, хочу видеть статистику, чтобы анализировать данные</td>
                <td>Данные загружены в систему</td>
                <td>Пользователь открывает страницу статистики</td>
                <td>Отображается актуальная статистика</td>
            </tr>
        </table>
        """,
        url="https://confluence.example.com/pages/viewpage.action?pageId=123456"
    )


@pytest.fixture
def sample_user_story_data():
    """Образец данных User Story для тестов"""
    return UserStoryData(
        title="Загрузка данных от AI в БД Чикаго",
        user_story_text="Я, как пользователь, хочу загружать данные, чтобы они сохранялись в системе",
        project="Houston",
        parent_work_item_id=12345,
        given_conditions="Пользователь авторизован",
        when_actions="Нажимает кнопку загрузки",
        then_results="Данные загружаются в систему",
        acceptance_criteria=[
            {
                "дано": "Пользователь авторизован",
                "когда": "Нажимает кнопку загрузки", 
                "тогда": "Данные загружаются в систему"
            }
        ],
        priority=2,
        story_points=5,
        assigned_to="test.user@example.com"
    )


@pytest.fixture
def sample_tfs_response():
    """Образец ответа от TFS API"""
    return {
        "id": 123456,
        "fields": {
            "System.Title": "Тестовая User Story",
            "System.State": "Новый",
            "System.AreaPath": "Houston\\Foxtrot",
            "System.IterationPath": "Houston\\Foxtrot"
        },
        "url": "https://tfssrv.systtech.ru/tfs/DefaultCollection/Houston/_apis/wit/workitems/123456"
    }


@pytest.fixture
def test_settings():
    """Настройки для тестов"""
    return {
        "CONFLUENCE_URL": "https://confluence.example.com",
        "CONFLUENCE_USERNAME": "test_user",
        "CONFLUENCE_PASSWORD": "test_password",
        "TFS_URL": "https://tfssrv.systtech.ru/tfs/DefaultCollection",
        "TFS_PAT": "test_pat_token",
        "TFS_PROJECT": "Houston",
        "TFS_ORGANIZATION": "test_org"
    }


@pytest.fixture(autouse=True)
def mock_settings(test_settings):
    """Мок настроек приложения"""
    with patch('app.config.settings.settings') as mock_settings:
        for key, value in test_settings.items():
            setattr(mock_settings, key, value)
        yield mock_settings
