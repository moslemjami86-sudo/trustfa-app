# تراست‌فا | TrustFa

پلتفرم نظرات و اعتماد کاربران — FastAPI + PostgreSQL + HTML/Tailwind

## ساختار (تخت برای موبایل و Render)

همه فایل‌ها در **ریشه** ریپو:

- `main.py` — سرور
- `index.html` — فرانت
- `requirements.txt`
- `render.yaml`

## دیپلوی روی Render

1. همین فایل‌ها را در GitHub آپلود کن (همه در ریشه، بدون پوشه)
2. Render → Blueprint → ریپو `trustfa`
3. Environment:
   - `ADMIN_EMAILS` = ایمیل خودت
   - `GOOGLE_CLIENT_ID` = (اختیاری)
4. Manual Deploy

## اجرای محلی

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
