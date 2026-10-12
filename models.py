from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(Text, nullable=True)
    provider = Column(String(20), default="email")
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="author")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    category = Column(String(100), default="سایر")
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    logo = Column(String(10), nullable=True)
    color = Column(String(50), default="bg-slate-500")
    domain = Column(String(200), nullable=True)
    icon = Column(String(50), default="fa-store")
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="business_rel")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    business_name = Column(String(200), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    helpful = Column(Integer, default=0)
    images = Column(Text, default="[]")  # JSON array as text
    hidden = Column(Boolean, default=False)
    edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="reviews")
    business_rel = relationship("Business", back_populates="reviews")


class ReviewLike(Base):
    __tablename__ = "review_likes"
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="uq_like"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReviewReport(Base):
    __tablename__ = "review_reports"
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="uq_report"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    reason = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OwnedBusiness(Base):
    __tablename__ = "owned_businesses"

    id = Column(String(36), primary_key=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), default="سایر")
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    plan = Column(String(50), default="رایگان")
    created_at = Column(DateTime, default=datetime.utcnow)


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
