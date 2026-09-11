import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "RAG-Based Hallucination Detection System"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    SECRET_KEY: str = "rag-hallucination-secret-key-change-in-production-2026-secure-random-seed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/rag_hallucination.db"

    UPLOAD_DIR: str = str(BASE_DIR.parent / "data" / "documents")
    VECTOR_DB_DIR: str = str(BASE_DIR.parent / "data" / "vectors")
    MAX_UPLOAD_SIZE_MB: int = 25

    DEFAULT_TOP_K: int = 4
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 50
    DEFAULT_TEMPERATURE: float = 0.2
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LLM_PROVIDER: str = "extractive-grounded"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    ML_MODEL_PATH: str = str(BASE_DIR.parent / "training" / "model" / "classifier.joblib")

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_DB_DIR, exist_ok=True)
os.makedirs(Path(settings.ML_MODEL_PATH).parent, exist_ok=True)
