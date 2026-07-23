from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DashboardChartsResponse, InsightItem, KPIResponse
from app.services.ai_service import AIService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=KPIResponse)
def get_kpis(db: Session = Depends(get_db)):
    return DashboardService(db).get_kpis()


@router.get("/charts", response_model=DashboardChartsResponse)
def get_charts(db: Session = Depends(get_db)):
    return DashboardService(db).get_charts()


@router.get("/insights", response_model=list[InsightItem])
async def get_insights(db: Session = Depends(get_db)):
    ai = AIService(db)
    return await ai.generate_insights()
