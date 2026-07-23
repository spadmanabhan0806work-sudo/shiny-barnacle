from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    copilot,
    dashboard,
    documents,
    forecast,
    logistics,
    reports,
    suppliers,
)
from app.seed import init_db
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Operyx AI Supply Chain & Analytics API",
    description="PoC monolith: Supply chain platform & trade intent extraction",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = settings.cors_origin_list
is_wildcard = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else cors_origins,
    allow_origin_regex=r"https?://.*" if is_wildcard else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

# Supply Chain Routers
app.include_router(dashboard.router)
app.include_router(forecast.router)
app.include_router(suppliers.router)
app.include_router(copilot.router)
app.include_router(logistics.router)
app.include_router(documents.router)
app.include_router(reports.router)

# Audio & Intent Extraction Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(annotations.router, prefix="/api/v1")
app.include_router(calls.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")
app.include_router(exports.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "ai_provider": settings.llm_provider}
