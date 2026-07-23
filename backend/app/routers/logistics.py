from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LogisticsAlert, ShipmentResponse, VehicleResponse, WarehouseResponse
from app.services.logistics_service import LogisticsService

router = APIRouter(prefix="/api/logistics", tags=["logistics"])


@router.get("/shipments", response_model=list[ShipmentResponse])
def list_shipments(status: str | None = Query(None), db: Session = Depends(get_db)):
    return LogisticsService(db).list_shipments(status)


@router.get("/warehouses", response_model=list[WarehouseResponse])
def list_warehouses(db: Session = Depends(get_db)):
    return LogisticsService(db).list_warehouses()


@router.get("/vehicles", response_model=list[VehicleResponse])
def list_vehicles(db: Session = Depends(get_db)):
    return LogisticsService(db).list_vehicles()


@router.get("/alerts", response_model=list[LogisticsAlert])
def get_alerts(db: Session = Depends(get_db)):
    return LogisticsService(db).get_alerts()
