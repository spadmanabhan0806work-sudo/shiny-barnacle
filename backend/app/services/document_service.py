import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.models import UploadedDocument
from app.services.ai_service import AIService

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService(db)

    async def upload_file(self, filename: str, content: bytes, doc_type: str = "invoice") -> dict:
        safe_name = re.sub(r"[^\w.\-]", "_", filename)
        file_path = UPLOAD_DIR / safe_name
        file_path.write_bytes(content)

        text = self._extract_text(file_path, content)
        doc = UploadedDocument(
            filename=safe_name,
            doc_type=doc_type,
            file_path=str(file_path),
            extracted_text=text,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return {"document_id": doc.id, "filename": doc.filename, "doc_type": doc.doc_type}

    def _extract_text(self, file_path: Path, content: bytes) -> str:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            try:
                reader = PdfReader(str(file_path))
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception:
                return content.decode("utf-8", errors="ignore")
        return content.decode("utf-8", errors="ignore")

    async def extract_fields(self, document_id: int | None = None, filename: str | None = None) -> dict:
        doc = None
        if document_id:
            doc = self.db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
        elif filename:
            doc = self.db.query(UploadedDocument).filter(UploadedDocument.filename == filename).first()
            if not doc:
                sample_path = DATA_DIR / "invoices" / filename
                if sample_path.exists():
                    text = sample_path.read_text(encoding="utf-8")
                    return await self._parse_and_summarize(filename, "invoice", text)

        if not doc:
            raise ValueError("Document not found")

        return await self._parse_and_summarize(doc.filename, doc.doc_type, doc.extracted_text)

    async def _parse_and_summarize(self, filename: str, doc_type: str, text: str) -> dict:
        fields = self._regex_extract(text)
        line_items = self._extract_line_items(text)

        ai_summary = await self.ai.generate(
            f"Summarize this {doc_type} document",
            context={
                "vendor": fields.get("vendor", "Unknown"),
                "total_amount": fields.get("total_amount", "N/A"),
                "invoice_number": fields.get("invoice_number", "N/A"),
            },
            system="document analysis",
        )

        return {
            "document_id": None,
            "filename": filename,
            "doc_type": doc_type,
            "fields": [{"field": k, "value": v, "confidence": 0.92} for k, v in fields.items()],
            "line_items": line_items,
            "ai_summary": ai_summary,
        }

    def _regex_extract(self, text: str) -> dict[str, str]:
        fields: dict[str, str] = {}

        patterns = {
            "invoice_number": r"(?:Invoice Number|Invoice No)[:\s]+([A-Z0-9\-]+)",
            "date": r"(?:Date)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
            "due_date": r"(?:Due Date)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
            "vendor": r"(?:Vendor)[:\s]+(.+)",
            "total_amount": r"(?:TOTAL DUE|TOTAL)[:\s]+\$?([\d,]+\.?\d*)",
            "payment_terms": r"(?:Payment Terms)[:\s]+(.+)",
            "po_reference": r"(?:PO Reference|PO)[:\s]+([A-Z0-9\-]+)",
        }
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields[field] = match.group(1).strip()

        return fields

    def _extract_line_items(self, text: str) -> list[dict[str, Any]]:
        items = []
        pattern = r"(\d+)\.\s+(.+?)\s+-\s+Qty:\s*(\d+)\s*@\s*\$?([\d.]+)\s*=\s*\$?([\d,]+\.?\d*)"
        for match in re.finditer(pattern, text):
            items.append({
                "line": int(match.group(1)),
                "description": match.group(2).strip(),
                "quantity": int(match.group(3)),
                "unit_price": float(match.group(4)),
                "total": float(match.group(5).replace(",", "")),
            })
        return items

    def list_sample_documents(self) -> list[dict[str, str]]:
        invoice_dir = DATA_DIR / "invoices"
        if not invoice_dir.exists():
            return []
        return [{"filename": f.name, "path": str(f)} for f in invoice_dir.glob("*.txt")]
