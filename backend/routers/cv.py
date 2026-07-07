import os
import re
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, CV
from schemas import CVResponse
from auth import get_current_user

router = APIRouter()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = (".pdf", ".doc", ".docx")
DOC_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
DOCX_SIGNATURE = b"PK"
PDF_SIGNATURE = b"%PDF"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    sanitized_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)
    name, extension = os.path.splitext(sanitized_name)
    return sanitized_name if name else f"upload{extension}"


def has_allowed_signature(file: UploadFile, extension: str) -> bool:
    signature = file.file.read(8)
    file.file.seek(0)

    if extension == ".pdf":
        return signature.startswith(PDF_SIGNATURE)
    if extension == ".doc":
        return signature.startswith(DOC_SIGNATURE)
    if extension == ".docx":
        return signature.startswith(DOCX_SIGNATURE)
    return False

@router.post("/upload", response_model=CVResponse)
def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, and DOCX are allowed.")

    if not has_allowed_signature(file, extension):
        raise HTTPException(status_code=400, detail="Uploaded file content does not match its extension.")

    safe_filename = sanitize_filename(file.filename)
    file_location = os.path.join(UPLOAD_DIR, f"{current_user.id}_{safe_filename}")
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    new_cv = CV(
        user_id=current_user.id,
        file_url=file_location,
        status="pending"
    )
    db.add(new_cv)
    db.commit()
    db.refresh(new_cv)
    
    return new_cv
