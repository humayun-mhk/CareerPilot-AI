import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
BASE_DIR = BACKEND_DIR
PROJECT_NAME = os.getenv("PROJECT_NAME", "CareerPilot AI API")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")


def _database_driver(database_url: str) -> str:
    if database_url.startswith(("postgresql://", "postgres://")):
        return "postgresql"
    return "sqlite"


DATABASE_DRIVER = _database_driver(DATABASE_URL)


def _path_from_env(name: str, default: str) -> Path:
    value = os.getenv(name, default)
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def _database_path() -> Path:
    if DATABASE_URL.startswith("sqlite:///"):
        raw_path = DATABASE_URL.replace("sqlite:///", "", 1)
        path = Path(raw_path)
        return path if path.is_absolute() else BASE_DIR / path
    return _path_from_env("DATABASE_PATH", "database/careerpilot.db")


DATABASE_PATH = _database_path()
CHROMA_PATH = _path_from_env("CHROMA_PATH", "database/chroma")
UPLOAD_DIR = _path_from_env("UPLOAD_DIR", "uploads")
EXPORT_DIR = _path_from_env("EXPORT_DIR", "exports")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
FRONTEND_API_URL = os.getenv("FRONTEND_API_URL", "http://localhost:8000")

DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def _origins_from_env(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = list(dict.fromkeys(DEFAULT_ORIGINS + _origins_from_env(CORS_ORIGINS)))
