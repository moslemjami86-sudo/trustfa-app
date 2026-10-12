from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = ""
    avatar: Optional[str] = None
    provider: str = "email"
    is_admin: bool = False

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    token: str
    user: UserOut


class RegisterIn(BaseModel):
    name: str = Field(min_length=2)
    email: str
    phone: Optional[str] = ""
    password: str = Field(min_length=6)


class LoginIn(BaseModel):
    identifier: str
    password: str


class GoogleIn(BaseModel):
    name: str
    email: str
    avatar: Optional[str] = None


class GoogleTokenIn(BaseModel):
    """ID token از Google Identity Services"""
    credential: str


class ProfileUpdateIn(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    avatar: Optional[str] = None


class BusinessOut(BaseModel):
    id: int
    name: str
    category: str
    rating: float
    reviews: int
    logo: Optional[str] = None
    color: str = "bg-slate-500"
    domain: Optional[str] = ""
    icon: str = "fa-store"
    verified: bool = False

    class Config:
        from_attributes = True


class BusinessCreateIn(BaseModel):
    name: str
    category: str = "سایر"
    website: Optional[str] = ""
    desc: Optional[str] = ""


class ReviewOut(BaseModel):
    id: int
    userId: str
    user: str
    avatar: Optional[str] = None
    business: str
    rating: int
    title: str
    text: str
    date: str
    helpful: int = 0
    images: List[str] = []
    hidden: bool = False
    edited: bool = False


class ReviewCreateIn(BaseModel):
    business: str
    rating: int = Field(ge=1, le=5)
    title: str
    text: str
    images: Optional[List[str]] = []


class ReviewUpdateIn(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    title: Optional[str] = None
    text: Optional[str] = None


class ReportIn(BaseModel):
    reason: str


class ContactIn(BaseModel):
    name: str
    email: str
    message: str
