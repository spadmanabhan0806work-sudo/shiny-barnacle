from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DocumentExtractRequest, DocumentExtractResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("invoice"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    service = DocumentService(db)
    return await service.upload_file(file.filename or "document.txt", content, doc_type)


@router.post("/extract", response_model=DocumentExtractResponse)
async def extract_document(request: DocumentExtractRequest, db: Session = Depends(get_db)):
    service = DocumentService(db)
    return await service.extract_fields(request.document_id, request.filename)


@router.get("/samples")
def list_samples(db: Session = Depends(get_db)):
    return DocumentService(db).list_sample_documents()
