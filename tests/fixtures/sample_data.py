"""
Образцы данных для тестов
"""
from app.models.request_models import UserStoryData, ConfluenceArticle
from app.models.tfs_models import WorkItemInfo, ProjectInfo


def get_sample_confluence_article():
    """Возвращает образец статьи Confluence"""
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


def get_sample_user_story_data():
    """Возвращает образец данных User Story"""
    return UserStoryData(
        title="Загрузка данных от AI в БД Чикаго",
        user_story_text="Я, как пользователь системы, хочу загружать данные от AI в базу данных Чикаго, чтобы они были доступны для анализа",
        project="Houston",
        parent_work_item_id=12345,
        given_conditions="Пользователь авторизован в системе",
        when_actions="Нажимает кнопку загрузки данных",
        then_results="Данные загружаются в базу данных Чикаго",
        acceptance_criteria=[
            {
                "дано": "Пользователь авторизован в системе",
                "когда": "Нажимает кнопку загрузки данных",
                "тогда": "Данные загружаются в базу данных Чикаго"
            },
            {
                "дано": "Система работает корректно",
                "когда": "Пользователь выбирает файл для загрузки",
                "тогда": "Файл валидируется и обрабатывается"
            }
        ],
        priority=2,
        story_points=5,
        assigned_to="test.user@example.com",
        tech_lead="tech.lead@example.com",
        developers=["dev1@example.com", "dev2@example.com"],
        tags=["AI", "Data Loading", "Chicago DB"]
    )


def get_sample_work_item_info():
    """Возвращает образец WorkItemInfo"""
    return WorkItemInfo(
        id=123456,
        title="Тестовая User Story",
        work_item_type="User Story",
        state="Новый",
        area_path="Houston\\Foxtrot",
        iteration_path="Houston\\Foxtrot",
        assigned_to="test.user@example.com",
        priority=2,
        story_points=5,
        business_value=20,
        description="Описание тестовой User Story"
    )


def get_sample_project_info():
    """Возвращает образец ProjectInfo"""
    return ProjectInfo(
        id="project-123",
        name="Houston",
        description="Тестовый проект Houston",
        state="wellFormed",
        url="https://tfssrv.systtech.ru/tfs/DefaultCollection/Houston"
    )


def get_sample_tfs_response():
    """Возвращает образец ответа от TFS API"""
    return {
        "id": 123456,
        "rev": 1,
        "fields": {
            "System.Title": "Тестовая User Story",
            "System.State": "Новый",
            "System.AreaPath": "Houston\\Foxtrot",
            "System.IterationPath": "Houston\\Foxtrot",
            "System.AssignedTo": "test.user@example.com",
            "Microsoft.VSTS.Common.Priority": 2,
            "Microsoft.VSTS.Scheduling.StoryPoints": 5,
            "Microsoft.VSTS.Common.BusinessValue": 20,
            "System.Description": "Описание тестовой User Story",
            "Microsoft.VSTS.Common.AcceptanceCriteria": "<table><tr><th>Дано</th><th>Когда</th><th>Тогда</th></tr></table>"
        },
        "url": "https://tfssrv.systtech.ru/tfs/DefaultCollection/Houston/_apis/wit/workitems/123456",
        "relations": []
    }


def get_sample_confluence_response():
    """Возвращает образец ответа от Confluence API"""
    return {
        "id": "123456",
        "type": "page",
        "title": "Тестовая статья для User Stories",
        "space": {
            "id": "12345",
            "key": "TEST",
            "name": "Test Space"
        },
        "version": {
            "number": 1,
            "when": "2023-01-01T00:00:00.000Z"
        },
        "body": {
            "storage": {
                "value": """
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
                        <th>Дано</th>
                        <th>Когда</th>
                        <th>Тогда</th>
                    </tr>
                    <tr>
                        <td>US 1</td>
                        <td>Загрузка данных от AI в БД Чикаго</td>
                        <td>Пользователь авторизован в системе</td>
                        <td>Нажимает кнопку загрузки данных</td>
                        <td>Данные загружаются в базу данных Чикаго</td>
                    </tr>
                </table>
                """,
                "representation": "storage"
            }
        },
        "_links": {
            "webui": "/pages/viewpage.action?pageId=123456"
        }
    }


def get_sample_html_content():
    """Возвращает образец HTML контента"""
    return """
    <h1>Тестовая статья</h1>
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
            <th>Дано</th>
            <th>Когда</th>
            <th>Тогда</th>
        </tr>
        <tr>
            <td>US 1</td>
            <td>Загрузка данных от AI в БД Чикаго</td>
            <td>Пользователь авторизован в системе</td>
            <td>Нажимает кнопку загрузки данных</td>
            <td>Данные загружаются в базу данных Чикаго</td>
        </tr>
        <tr>
            <td>US 2</td>
            <td>Отображение статистики</td>
            <td>Данные загружены в систему</td>
            <td>Пользователь открывает страницу статистики</td>
            <td>Отображается актуальная статистика</td>
        </tr>
    </table>
    """


def get_sample_user_story_blocks():
    """Возвращает образец блоков User Stories"""
    return [
        """
        <tr>
            <td>US 1</td>
            <td>Загрузка данных от AI в БД Чикаго</td>
            <td>Пользователь авторизован в системе</td>
            <td>Нажимает кнопку загрузки данных</td>
            <td>Данные загружаются в базу данных Чикаго</td>
        </tr>
        """,
        """
        <tr>
            <td>US 2</td>
            <td>Отображение статистики</td>
            <td>Данные загружены в систему</td>
            <td>Пользователь открывает страницу статистики</td>
            <td>Отображается актуальная статистика</td>
        </tr>
        """
    ]


def get_sample_acceptance_criteria():
    """Возвращает образец критериев приемки"""
    return [
        {
            "дано": "Пользователь авторизован в системе",
            "когда": "Нажимает кнопку загрузки данных",
            "тогда": "Данные загружаются в базу данных Чикаго"
        },
        {
            "дано": "Система работает корректно",
            "когда": "Пользователь выбирает файл для загрузки",
            "тогда": "Файл валидируется и обрабатывается"
        }
    ]


def get_sample_preview_data():
    """Возвращает образец данных preview"""
    return {
        "confluence_url": "https://confluence.example.com/pages/viewpage.action?pageId=123456",
        "article_title": "Тестовая статья для User Stories",
        "project": "Houston",
        "parent_ticket": "12345",
        "user_stories_count": 2,
        "team": "Foxtrot",
        "area_path": "Houston\\Foxtrot",
        "iteration_path": "Houston\\Foxtrot",
        "user_stories": [
            {
                "title": "Загрузка данных от AI в БД Чикаго",
                "description": "Я, как пользователь системы, хочу загружать данные от AI в базу данных Чикаго, чтобы они были доступны для анализа",
                "acceptance_criteria": ["<table>...</table>"],
                "us_number": "US1",
                "given_conditions": "Пользователь авторизован в системе",
                "when_actions": "Нажимает кнопку загрузки данных",
                "then_results": "Данные загружаются в базу данных Чикаго"
            },
            {
                "title": "Отображение статистики",
                "description": "Я, как пользователь системы, хочу видеть статистику, чтобы анализировать данные",
                "acceptance_criteria": ["<table>...</table>"],
                "us_number": "US2",
                "given_conditions": "Данные загружены в систему",
                "when_actions": "Пользователь открывает страницу статистики",
                "then_results": "Отображается актуальная статистика"
            }
        ]
    }
