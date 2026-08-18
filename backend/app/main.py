from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.session import init_db
from app.routes.admin_auth import router as admin_auth_router
from app.routes.admin_data import router as admin_data_router
from app.routes.chat import router as chat_router
from app.routes.knowledge import router as knowledge_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Datamart LangChain Agent API",
    version="0.2.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(knowledge_router)
app.include_router(admin_auth_router)
app.include_router(admin_data_router)


@app.get("/")
def root():
    return {
        "name": "Datamart LangChain Agent API",
        "status": "running",
        "framework": "LangChain",
        "n8n": False,
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
    }