from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from app.models import DocumentResponse, DriveIngestionRequest
from app.services.document_service import get_document_service, DocumentService
from app.services.google_drive_service import get_drive_service, GoogleDriveService
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    document_service: DocumentService = Depends(get_document_service)
):
    try:
        documents = await document_service.list_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
):
    """Upload a document (txt or pdf) and add it to the database"""
    try:
        # Save the uploaded file temporarily
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        response = await document_service.process_uploaded_file(
            file_path=file_path,
            document_name=file.filename,
            source="uploaded"
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drive", response_model=List[DocumentResponse])
async def ingest_from_drive(
    request: DriveIngestionRequest,
    drive_service: GoogleDriveService = Depends(get_drive_service),
    document_service: DocumentService = Depends(get_document_service)
):
    try:
        # Fetch files from Drive
        files = await drive_service.fetch_files(request.folder_id)
        
        results = []
        for file in files:
            # Download and process each file
            content = await drive_service.download_file(file["id"])
            if content:
                document = await document_service.process_document(
                    content=content,
                    document_name=file["name"],
                    source=f"google_drive:{file['id']}"
                )
                results.append(document)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    try:
        success = await document_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "success", "message": "Document deleted"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))