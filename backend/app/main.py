from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.routes import router as v1_router
from .core.config import ALLOWED_ORIGINS, PROJECT_NAME, UPLOAD_DIR
from .db.session import init_db
from .services.rag_memory import rag_memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rag_memory.init()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=PROJECT_NAME, version="4.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(v1_router)
