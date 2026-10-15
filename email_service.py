"""ارسال ایمیل تایید برای محیط واقعی (Production)"""
from __future__ import annotations

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("trustfa.email")

APP_URL = os.getenv("APP_URL", "").rstrip("/")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@trustfa.ir")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "").strip()
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587") or "587")
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() in ("1", "true", "yes")


def email_configured() -> bool:
    return bool(SENDGRID_API_KEY) or bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def _html_body(verify_link: str) -> str:
    return f"""
    <div dir="rtl" style="font-family:Tahoma,Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;background:#f8fafc;border-radius:16px">
      <div style="background:#fff;padding:28px;border-radius:14px;border:1px solid #e2e8f0">
        <h2 style="color:#059669;margin:0 0 12px">خوش آمدید به تراست‌فا</h2>
        <p style="color:#334155;line-height:1.8;margin:0 0 20px">
          برای فعال‌سازی حساب، ایمیل خود را تایید کنید:
        </p>
        <p style="text-align:center;margin:28px 0">
          <a href="{verify_link}"
             style="background:#10b981;color:#fff;padding:14px 28px;text-decoration:none;border-radius:999px;display:inline-block;font-weight:700">
            تایید ایمیل
          </a>
        </p>
        <p style="color:#64748b;font-size:13px;line-height:1.7;word-break:break-all">
          اگر دکمه کار نکرد، این لینک را در مرورگر باز کنید:<br/>
          <a href="{verify_link}" style="color:#059669">{verify_link}</a>
        </p>
        <p style="color:#94a3b8;font-size:12px;margin-top:24px;border-top:1px solid #e2e8f0;padding-top:16px">
          این لینک تا ۲۴ ساعت اعتبار دارد. اگر شما ثبت‌نام نکرده‌اید، این پیام را نادیده بگیرید.
        </p>
      </div>
    </div>
    """


def _send_sendgrid(to_email: str, subject: str, html: str) -> None:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html,
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    resp = sg.send(message)
    if resp.status_code >= 400:
        raise RuntimeError(f"SendGrid status {resp.status_code}")


def _send_smtp(to_email: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        if SMTP_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())


def send_verification_email(to_email: str, token: str) -> bool:
    if not APP_URL:
        raise RuntimeError(
            "APP_URL روی سرور تنظیم نشده. در Render مقدار APP_URL را برابر آدرس سایت بگذارید."
        )
    if not email_configured():
        raise RuntimeError(
            "سرویس ایمیل پیکربندی نشده. SENDGRID_API_KEY یا SMTP را در Environment تنظیم کنید."
        )

    verify_link = f"{APP_URL}/api/auth/verify-email?token={token}"
    subject = "تایید ایمیل در تراست‌فا"
    html = _html_body(verify_link)

    try:
        if SENDGRID_API_KEY:
            _send_sendgrid(to_email, subject, html)
        else:
            _send_smtp(to_email, subject, html)
        logger.info("Verification email sent to %s", to_email)
        return True
    except Exception as e:
        logger.exception("Failed to send verification email to %s: %s", to_email, e)
        raise RuntimeError(f"ارسال ایمیل تایید ناموفق بود: {e}") from e
