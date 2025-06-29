from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserResponse(BaseModel):
    username: str
    email: str
    user_id: str

class UserWithId(UserResponse):
    id: str