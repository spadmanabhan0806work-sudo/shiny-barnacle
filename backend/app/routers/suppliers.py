from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SupplierAnalysisResponse, SupplierResponse
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(risk_level: str | None = Query(None), db: Session = Depends(get_db)):
    return SupplierService(db).list_suppliers(risk_level)


@router.get("/{supplier_id}/analysis", response_model=SupplierAnalysisResponse)
async def analyze_supplier(supplier_id: int, db: Session = Depends(get_db)):
    result = await SupplierService(db).analyze_supplier(supplier_id)
    return {
        "supplier": result["supplier"],
        "risk_factors": result["risk_factors"],
        "recommendations": result["recommendations"],
        "ai_analysis": result["ai_analysis"],
    }
