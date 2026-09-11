import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.session import engine, Base
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.rag import router as rag_router
from app.api.hallucination import router as hallucination_router
from app.api.dashboard import router as dashboard_router
from app.api.settings import router as settings_router

# Ensure all tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Full-stack RAG and Hallucination Detection API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(rag_router, prefix=settings.API_V1_PREFIX)
app.include_router(hallucination_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_router, prefix=settings.API_V1_PREFIX)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.get("/", tags=["Health"])
def root_check():
    return {
        "message": f"Welcome to {settings.APP_NAME} API. Visit /docs for OpenAPI documentation.",
        "health": "/api/health"
    }
