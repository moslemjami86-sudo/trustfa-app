import os

_BASE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_SQLITE = "sqlite:///" + os.path.join(_BASE, "trustfa.db").replace("\\", "/")


def _normalize_db_url(url: str) -> str:
    """Render gives postgres:// — SQLAlchemy needs postgresql+psycopg2://"""
    if not url:
        return _DEFAULT_SQLITE
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL", _DEFAULT_SQLITE))

SECRET_KEY = os.getenv("SECRET_KEY", "trustfa-change-me-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(_BASE, "uploads"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
ADMIN_EMAILS = [
    e.strip().lower()
    for e in os.getenv("ADMIN_EMAILS", "admin@trustfa.ir").split(",")
    if e.strip()
]
