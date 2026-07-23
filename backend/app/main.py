from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import copilot, dashboard, documents, forecast, logistics, reports, suppliers
from app.seed import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Operyx AI Supply Chain API",
    description="Intelligent Supply Chain Platform PoC",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(forecast.router)
app.include_router(suppliers.router)
app.include_router(copilot.router)
app.include_router(logistics.router)
app.include_router(documents.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_provider": settings.ai_provider}
