from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CopilotRequest, CopilotResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

SUGGESTED_FOLLOWUPS = [
    "Which suppliers are delayed?",
    "Show high risk vendors.",
    "What inventory is low?",
    "Show recent purchase orders.",
    "Warehouse capacity status?",
]


@router.post("/chat", response_model=CopilotResponse)
async def chat(request: CopilotRequest, db: Session = Depends(get_db)):
    ai = AIService(db)
    reply = await ai.generate(
        request.message,
        context={
            "history": [h.model_dump() for h in request.history],
            "history_length": len(request.history),
        },
        system="Procurement Copilot AI assistant for supply chain management and logistics queries",
    )
    followups = [f for f in SUGGESTED_FOLLOWUPS if f.lower() not in request.message.lower()][:3]
    return CopilotResponse(reply=reply, suggested_followups=followups)

