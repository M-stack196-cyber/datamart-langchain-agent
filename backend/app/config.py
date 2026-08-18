from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # Embeddings / RAG
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Database
    database_url: str = f"sqlite:///{BASE_DIR / 'datamart_agent.db'}"

    # Chroma
    chroma_persist_dir: str = str(BASE_DIR / "chroma_db")
    chroma_collection: str = "datamart_knowledge"

    # Frontend / CORS
    cors_origins: str = "http://localhost:5173"

    # Admin authentication
    admin_username: str = "admin"
    admin_password_hash: str = ""
    admin_session_secret: str = ""
    admin_session_hours: int = 8
    admin_cookie_secure: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()