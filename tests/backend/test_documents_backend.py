import pytest
from app.services.document_service import DocumentService

@pytest.mark.asyncio
async def test_list_document_samples(backend_client):
    response = await backend_client.get("/api/documents/samples")
    assert response.status_code == 200
    samples = response.json()
    assert isinstance(samples, list)

@pytest.mark.asyncio
async def test_upload_document(backend_client):
    file_content = b"INVOICE #12345\nSupplier: Acme Logistics\nTotal: $1,250.00\nDate: 2026-07-22"
    files = {"file": ("invoice_12345.txt", file_content, "text/plain")}
    data = {"doc_type": "invoice"}
    response = await backend_client.post("/api/documents/upload", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert "document_id" in res
    assert res["doc_type"] == "invoice"

@pytest.mark.asyncio
async def test_extract_document_fields(backend_client):
    file_content = b"INVOICE #12345\nSupplier: Acme Logistics\nTotal: $1,250.00\nDate: 2026-07-22"
    files = {"file": ("invoice_12345.txt", file_content, "text/plain")}
    upload_res = await backend_client.post("/api/documents/upload", files=files, data={"doc_type": "invoice"})
    doc_id = upload_res.json()["document_id"]
    
    extract_payload = {"document_id": doc_id, "filename": "invoice_12345.txt"}
    response = await backend_client.post("/api/documents/extract", json=extract_payload)
    assert response.status_code == 200
    extracted = response.json()
    assert "fields" in extracted
    assert len(extracted["fields"]) > 0
    assert "field" in extracted["fields"][0]
    assert "value" in extracted["fields"][0]
    assert "confidence" in extracted["fields"][0]
