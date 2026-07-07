from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Any, Dict

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class SearchRequest(BaseModel):
    cv_id: int

class CVResponse(BaseModel):
    id: int
    user_id: int
    file_url: str
    status: str
    parsed_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CVUpdate(BaseModel):
    parsed_json: Dict[str, Any]
