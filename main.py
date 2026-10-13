"""
تراست‌فا — FastAPI + SQLAlchemy + PostgreSQL (or SQLite fallback)
"""
import json
import os
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config import UPLOAD_DIR, CORS_ORIGINS, GOOGLE_CLIENT_ID, ADMIN_EMAILS, SECRET_KEY
from database import engine, Base, get_db, SessionLocal
from models import (
    User, Business, Review, ReviewLike, ReviewReport, OwnedBusiness, ContactMessage
)
from schemas import (
    RegisterIn, LoginIn, GoogleIn, GoogleTokenIn, ProfileUpdateIn, TokenOut, UserOut,
    BusinessOut, BusinessCreateIn, ReviewOut, ReviewCreateIn, ReviewUpdateIn,
    ReportIn, ContactIn,
)
from auth import (
    hash_password, verify_password, create_token, get_current_user,
    get_optional_user, new_user_id,
)
from seed import seed_businesses

os.makedirs(UPLOAD_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)

def _ensure_columns():
    """Add new columns on existing DBs (SQLite/Postgres)."""
    from sqlalchemy import text, inspect
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    with engine.begin() as conn:
        if "is_admin" not in cols:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            except Exception:
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                except Exception:
                    pass

_ensure_columns()

# seed
_db = SessionLocal()
try:
    seed_businesses(_db)
    # promote admin emails
    for em in ADMIN_EMAILS:
        u = _db.query(User).filter(User.email == em).first()
        if u and not u.is_admin:
            u.is_admin = True
            _db.commit()
finally:
    _db.close()

app = FastAPI(title="تراست‌فا API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.abspath(os.path.dirname(__file__))  # index.html کنار main.py


def user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id, name=u.name, email=u.email,
        phone=u.phone or "", avatar=u.avatar, provider=u.provider or "email",
        is_admin=bool(getattr(u, "is_admin", False)),
    )


def require_admin(user: User = None):
    if not user or not getattr(user, "is_admin", False):
        raise HTTPException(403, "دسترسی ادمین لازم است")
    return user


def is_admin_email(email: str) -> bool:
    return (email or "").strip().lower() in ADMIN_EMAILS

def ensure_admin_flag(user: User, db: Session) -> User:
    """اگر ایمیل در ADMIN_EMAILS باشد، is_admin را در دیتابیس فعال می‌کند."""
    if not user:
        return user
    if is_admin_email(user.email) and not bool(getattr(user, "is_admin", False)):
        user.is_admin = True
        db.add(user)
        db.commit()
        db.refresh(user)
    return user



def business_out(b: Business) -> dict:
    return {
        "id": b.id,
        "name": b.name,
        "category": b.category,
        "rating": b.rating or 0,
        "reviews": b.reviews_count or 0,
        "logo": b.logo or (b.name[:1] if b.name else "?"),
        "color": b.color or "bg-slate-500",
        "domain": b.domain or "",
        "icon": b.icon or "fa-store",
        "verified": bool(b.verified),
    }


def review_out(r: Review, author: Optional[User] = None) -> dict:
    try:
        images = json.loads(r.images or "[]")
    except Exception:
        images = []
    name = author.name if author else "کاربر"
    avatar = author.avatar if author else None
    if author is None and hasattr(r, "author") and r.author:
        name = r.author.name
        avatar = r.author.avatar
    delta = datetime.utcnow() - (r.created_at or datetime.utcnow())
    if delta.days <= 0:
        date = "همین الان" if r.edited else "امروز"
    elif delta.days == 1:
        date = "۱ روز پیش"
    elif delta.days < 7:
        date = f"{delta.days} روز پیش"
    else:
        date = f"{delta.days // 7} هفته پیش"
    if r.edited:
        date = date + " · ویرایش‌شده" if "ویرایش" not in date else date
    return {
        "id": r.id,
        "userId": r.user_id,
        "user": name,
        "avatar": avatar,
        "business": r.business_name,
        "rating": r.rating,
        "title": r.title,
        "text": r.text,
        "date": date,
        "helpful": r.helpful or 0,
        "images": images,
        "hidden": bool(r.hidden),
        "edited": bool(r.edited),
    }


# ---------- Health ----------
@app.get("/api/health")
def health():
    return {"ok": True, "service": "trustfa", "db": "sqlalchemy"}


# ---------- Auth ----------
@app.post("/api/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "این ایمیل قبلاً ثبت شده")
    if body.phone:
        phone = body.phone.replace(" ", "")
        if db.query(User).filter(User.phone == phone).first():
            raise HTTPException(400, "این موبایل قبلاً ثبت شده")
    else:
        phone = ""
    user = User(
        id=new_user_id(),
        name=body.name.strip(),
        email=email,
        phone=phone,
        password_hash=hash_password(body.password),
        provider="email",
        is_admin=is_admin_email(email),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(token=create_token(user), user=user_out(user))


@app.post("/api/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    ident = body.identifier.strip().lower()
    user = (
        db.query(User)
        .filter(
            (User.email == ident)
            | (User.phone == ident)
            | (User.phone == body.identifier.replace(" ", ""))
        )
        .first()
    )
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "ایمیل/موبایل یا رمز اشتباه است")
    user = ensure_admin_flag(user, db)
    return TokenOut(token=create_token(user), user=user_out(user))


@app.get("/api/config")
def public_config():
    """تنظیمات عمومی برای فرانت (Client ID گوگل و …)."""
    return {
        "googleClientId": GOOGLE_CLIENT_ID or "",
        "googleEnabled": bool(GOOGLE_CLIENT_ID),
    }


@app.post("/api/auth/google", response_model=TokenOut)
def google_login_demo(body: GoogleIn, db: Session = Depends(get_db)):
    """حالت دمو (بدون GOOGLE_CLIENT_ID) — فقط برای توسعه."""
    if GOOGLE_CLIENT_ID:
        raise HTTPException(400, "از دکمه رسمی گوگل استفاده کنید (credential)")
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.name = body.name
        user.provider = "google"
        if body.avatar:
            user.avatar = body.avatar
        if is_admin_email(email):
            user.is_admin = True
    else:
        user = User(
            id=new_user_id(),
            name=body.name.strip(),
            email=email,
            phone="",
            password_hash=hash_password("google-" + email + uuid.uuid4().hex[:8]),
            avatar=body.avatar,
            provider="google",
            is_admin=is_admin_email(email),
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(token=create_token(user), user=user_out(user))


@app.post("/api/auth/google/token", response_model=TokenOut)
def google_login_token(body: GoogleTokenIn, db: Session = Depends(get_db)):
    """ورود واقعی با ID Token از Google Identity Services."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(400, "GOOGLE_CLIENT_ID روی سرور تنظیم نشده")
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        info = google_id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception as e:
        raise HTTPException(401, f"توکن گوگل نامعتبر است: {e}")

    email = (info.get("email") or "").strip().lower()
    if not email or not info.get("email_verified", True):
        raise HTTPException(400, "ایمیل گوگل تأیید نشده")
    name = info.get("name") or email.split("@")[0]
    avatar = info.get("picture")

    user = db.query(User).filter(User.email == email).first()
    if user:
        user.name = name
        user.provider = "google"
        if avatar:
            user.avatar = avatar
        if is_admin_email(email):
            user.is_admin = True
    else:
        user = User(
            id=new_user_id(),
            name=name,
            email=email,
            phone="",
            password_hash=hash_password("google-" + email + uuid.uuid4().hex[:12]),
            avatar=avatar,
            provider="google",
            is_admin=is_admin_email(email),
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(token=create_token(user), user=user_out(user))


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = ensure_admin_flag(user, db)
    return user_out(user)


@app.put("/api/auth/profile", response_model=TokenOut)
def update_profile(body: ProfileUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.name:
        user.name = body.name.strip()
    if body.email:
        em = body.email.strip().lower()
        exists = db.query(User).filter(User.email == em, User.id != user.id).first()
        if exists:
            raise HTTPException(400, "ایمیل تکراری است")
        user.email = em
    if body.phone is not None:
        user.phone = body.phone.replace(" ", "")
    if body.avatar is not None:
        user.avatar = body.avatar
    if body.password and len(body.password) >= 6:
        user.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(user)
    return TokenOut(token=create_token(user), user=user_out(user))


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "فقط تصویر مجاز است")
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "حجم فایل بیش از ۵ مگابایت")
    with open(path, "wb") as f:
        f.write(data)
    return {"url": f"/uploads/{name}"}


# ---------- Businesses ----------
@app.get("/api/businesses")
def list_businesses(q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Business)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter((Business.name.ilike(like)) | (Business.category.ilike(like)))
    items = query.order_by(Business.rating.desc()).all()
    return {"businesses": [business_out(b) for b in items]}


@app.get("/api/businesses/{biz_id}")
def get_business(biz_id: int, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == biz_id).first()
    if not b:
        raise HTTPException(404, "یافت نشد")
    return {"business": business_out(b)}


@app.post("/api/businesses")
def create_business(body: BusinessCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = db.query(Business).filter(Business.name == body.name.strip()).first()
    if not biz:
        domain = (body.website or "").replace("https://", "").replace("http://", "").split("/")[0]
        biz = Business(
            name=body.name.strip(),
            category=body.category or "سایر",
            logo=body.name.strip()[:1],
            domain=domain,
            verified=False,
        )
        db.add(biz)
        db.flush()
    owned = OwnedBusiness(
        id=str(uuid.uuid4()),
        owner_id=user.id,
        name=body.name.strip(),
        category=body.category or "سایر",
        website=body.website or "",
        description=body.desc or "",
        plan="رایگان",
    )
    db.add(owned)
    db.commit()
    db.refresh(biz)
    return {"business": business_out(biz)}


@app.get("/api/my-businesses")
def my_businesses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(OwnedBusiness).filter(OwnedBusiness.owner_id == user.id).all()
    return {
        "businesses": [
            {
                "id": o.id,
                "name": o.name,
                "category": o.category,
                "website": o.website,
                "desc": o.description,
                "plan": o.plan,
                "createdAt": o.created_at.isoformat() if o.created_at else None,
            }
            for o in items
        ]
    }


# ---------- Reviews ----------
@app.get("/api/reviews")
def list_reviews(
    rating: Optional[str] = None,
    business: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Review).filter(Review.hidden == False)  # noqa: E712
    if rating and rating != "all":
        q = q.filter(Review.rating == int(rating))
    if business:
        q = q.filter(Review.business_name == business)
    items = q.order_by(Review.created_at.desc()).limit(100).all()
    # load authors
    user_ids = {r.user_id for r in items}
    authors = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return {"reviews": [review_out(r, authors.get(r.user_id)) for r in items]}


@app.post("/api/reviews")
def create_review(body: ReviewCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    biz = db.query(Business).filter(Business.name == body.business.strip()).first()
    if not biz:
        biz = Business(
            name=body.business.strip(),
            category="سایر",
            logo=body.business.strip()[:1],
            rating=float(body.rating),
            reviews_count=0,
        )
        db.add(biz)
        db.flush()

    review = Review(
        user_id=user.id,
        business_id=biz.id,
        business_name=biz.name,
        rating=body.rating,
        title=body.title.strip(),
        text=body.text.strip(),
        images=json.dumps(body.images or []),
    )
    db.add(review)

    n = (biz.reviews_count or 0) + 1
    biz.rating = round((((biz.rating or 0) * (n - 1) + body.rating) / n), 1)
    biz.reviews_count = n

    db.commit()
    db.refresh(review)
    return {"review": review_out(review, user)}


@app.put("/api/reviews/{review_id}")
def update_review(
    review_id: int,
    body: ReviewUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(404, "نظر یافت نشد")
    if r.user_id != user.id:
        raise HTTPException(403, "اجازه ندارید")
    if body.rating is not None:
        r.rating = body.rating
    if body.title is not None:
        r.title = body.title.strip()
    if body.text is not None:
        r.text = body.text.strip()
    r.edited = True
    r.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(r)
    return {"review": review_out(r, user)}


@app.delete("/api/reviews/{review_id}")
def delete_review(review_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(404, "نظر یافت نشد")
    if r.user_id != user.id:
        raise HTTPException(403, "اجازه ندارید")
    biz = db.query(Business).filter(Business.id == r.business_id).first()
    if biz and (biz.reviews_count or 0) > 0:
        biz.reviews_count -= 1
    db.delete(r)
    db.commit()
    return {"ok": True}


@app.post("/api/reviews/{review_id}/helpful")
def helpful(review_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(404, "نظر یافت نشد")
    exists = (
        db.query(ReviewLike)
        .filter(ReviewLike.user_id == user.id, ReviewLike.review_id == review_id)
        .first()
    )
    if exists:
        raise HTTPException(400, "قبلاً لایک کرده‌اید")
    db.add(ReviewLike(user_id=user.id, review_id=review_id))
    r.helpful = (r.helpful or 0) + 1
    db.commit()
    return {"helpful": r.helpful}


@app.post("/api/reviews/{review_id}/report")
def report(review_id: int, body: ReportIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(404, "نظر یافت نشد")
    exists = (
        db.query(ReviewReport)
        .filter(ReviewReport.user_id == user.id, ReviewReport.review_id == review_id)
        .first()
    )
    if exists:
        raise HTTPException(400, "قبلاً گزارش کرده‌اید")
    db.add(ReviewReport(user_id=user.id, review_id=review_id, reason=body.reason))
    db.commit()
    count = db.query(ReviewReport).filter(ReviewReport.review_id == review_id).count()
    if count >= 3:
        r.hidden = True
        db.commit()
    return {"ok": True, "reportCount": count}


@app.get("/api/likes/me")
def my_likes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    likes = db.query(ReviewLike).filter(ReviewLike.user_id == user.id).all()
    return {"likes": [str(l.review_id) for l in likes]}


@app.post("/api/contact")
def contact(body: ContactIn, db: Session = Depends(get_db)):
    db.add(ContactMessage(name=body.name, email=body.email, message=body.message))
    db.commit()
    return {"ok": True}



# ---------- Admin ----------
@app.get("/api/admin/stats")
def admin_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    return {
        "users": db.query(User).count(),
        "businesses": db.query(Business).count(),
        "reviews": db.query(Review).count(),
        "hiddenReviews": db.query(Review).filter(Review.hidden == True).count(),  # noqa: E712
        "reports": db.query(ReviewReport).count(),
        "messages": db.query(ContactMessage).count(),
        "owned": db.query(OwnedBusiness).count(),
    }


@app.get("/api/admin/users")
def admin_users(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    items = db.query(User).order_by(User.created_at.desc()).limit(200).all()
    return {
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "phone": u.phone or "",
                "provider": u.provider,
                "is_admin": bool(u.is_admin),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in items
        ]
    }


@app.patch("/api/admin/users/{user_id}/admin")
def admin_toggle_admin(user_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(404, "کاربر یافت نشد")
    if target.id == user.id:
        raise HTTPException(400, "نمی‌توانید نقش خودتان را تغییر دهید")
    target.is_admin = not bool(target.is_admin)
    db.commit()
    return {"ok": True, "is_admin": target.is_admin}


@app.get("/api/admin/reviews")
def admin_reviews(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    items = db.query(Review).order_by(Review.created_at.desc()).limit(200).all()
    user_ids = {r.user_id for r in items}
    authors = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return {"reviews": [review_out(r, authors.get(r.user_id)) for r in items]}


@app.patch("/api/admin/reviews/{review_id}/hide")
def admin_hide_review(review_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(404, "نظر یافت نشد")
    r.hidden = not bool(r.hidden)
    db.commit()
    return {"ok": True, "hidden": r.hidden}


@app.delete("/api/admin/reviews/{review_id}")
def admin_delete_review(review_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(404, "نظر یافت نشد")
    db.delete(r)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/businesses")
def admin_businesses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    items = db.query(Business).order_by(Business.id.desc()).all()
    return {"businesses": [business_out(b) for b in items]}


@app.patch("/api/admin/businesses/{biz_id}/verify")
def admin_verify_business(biz_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    b = db.query(Business).filter(Business.id == biz_id).first()
    if not b:
        raise HTTPException(404, "یافت نشد")
    b.verified = not bool(b.verified)
    db.commit()
    return {"ok": True, "verified": b.verified}


@app.get("/api/admin/messages")
def admin_messages(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    items = db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).limit(100).all()
    return {
        "messages": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "message": m.message,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in items
        ]
    }


@app.get("/api/admin/reports")
def admin_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    items = db.query(ReviewReport).order_by(ReviewReport.created_at.desc()).limit(100).all()
    return {
        "reports": [
            {
                "id": r.id,
                "review_id": r.review_id,
                "user_id": r.user_id,
                "reason": r.reason,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ]
    }



# Static files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")

    @app.get("/")
    def index():
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"message": "frontend/index.html not found"}
