from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Any

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
    created_at: datetime

    class Config:
        from_attributes = True
