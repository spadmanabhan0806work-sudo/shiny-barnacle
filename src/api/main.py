from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.auth import AuthMiddleware
from src.api.routes import (
    analytics,
    annotations,
    calls,
    evaluations,
    exports,
    health,
    prompts,
    reviews,
)
from src.infrastructure.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="Operyx AI",
    description="PoC monolith: call audio → transcript → trade intent extraction",
    version="0.2.0-poc",
)

cors_origins = settings.get("api.cors_origins", ["http://localhost:3000"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

app.include_router(health.router, prefix="/api/v1")
app.include_router(annotations.router, prefix="/api/v1")
app.include_router(calls.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")
app.include_router(exports.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
