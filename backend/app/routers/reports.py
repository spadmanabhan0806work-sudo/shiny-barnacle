from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ExecutiveReportResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/executive", response_model=ExecutiveReportResponse)
async def generate_executive_report(db: Session = Depends(get_db)):
    ai = AIService(db)
    return await ai.generate_executive_report()
