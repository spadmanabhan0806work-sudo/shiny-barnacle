from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ForecastRequest, ForecastResponse
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.post("/upload")
async def upload_sales_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = (await file.read()).decode("utf-8")
    service = ForecastService(db)
    result = service.upload_csv(content)
    return result


@router.post("/generate", response_model=ForecastResponse)
async def generate_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    service = ForecastService(db)
    return await service.generate_forecast(request.sku, request.horizon_months)


@router.get("/skus")
def list_skus(db: Session = Depends(get_db)):
    return ForecastService(db).get_available_skus()
