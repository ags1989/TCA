from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.api.endpoints import router as api_router
from app.api.advanced_endpoints import router as advanced_router
from app.api.confluence_routes import router as confluence_router
from app.api.tfs_routes import router as tfs_router
from app.api.user_story_routes import router as user_story_router
from app.core.startup import initialize_extensions
from app.config.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    await initialize_extensions()
    yield
    # Очистка при завершении
    pass

app = FastAPI(
    title="Расширяемая система автоматизации TFS-Confluence",
    description="""
    Модульная система для автоматизации работы с различными источниками данных:
    - Создание тикетов в TFS на основе статей Confluence
    - Анализ связанных элементов из GitHub, Jira и других систем
    - Генерация технической документации
    - Анализ покрытия тестами и требований
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Подключаем статические файлы
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Подключаем API роуты
app.include_router(api_router, prefix="/api/v1", tags=["basic"])
app.include_router(advanced_router, tags=["advanced"])
app.include_router(confluence_router, prefix="/api/v1", tags=["confluence"])
app.include_router(tfs_router, prefix="/api/v1", tags=["tfs"])
app.include_router(user_story_router, prefix="/api/v1", tags=["user-stories"])

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница приложения"""
    html_path = os.path.join(static_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

@app.get("/health")
async def health_check():
    """Проверка работоспособности приложения"""
    return {
        "status": "healthy", 
        "version": "2.0.0",
        "extensions_loaded": True
    }
