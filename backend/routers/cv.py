import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, CV
from schemas import CVResponse
from auth import get_current_user

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=CVResponse)
def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(('.pdf', '.doc', '.docx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, and DOCX are allowed.")
    
    file_location = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    
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
