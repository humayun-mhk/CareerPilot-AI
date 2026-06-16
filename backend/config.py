import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]


def _path_from_env(name: str, default: str) -> Path:
    value = os.getenv(name, default)
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


DATABASE_PATH = _path_from_env("DATABASE_PATH", "database/careerpilot.db")
CHROMA_PATH = _path_from_env("CHROMA_PATH", "database/chroma")
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
ALLOWED_ORIGINS = list(dict.fromkeys(DEFAULT_ORIGINS + [FRONTEND_ORIGIN]))
