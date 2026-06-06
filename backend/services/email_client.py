"""Gmail SMTP service — sends outreach emails via Gmail App Password.

Setup:
1. Go to Google Account > Security > 2-Step Verification > App Passwords
2. Generate an App Password for "Mail"
3. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env

Usage:
    from services.email_client import send_outreach_email
    await send_outreach_email(to, subject, body, from_name)
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


async def send_outreach_email(
    to_email: str,
    subject: str,
    html_body: str,
    from_name: str = "GENESIS",
) -> dict:
    """Send an email via Gmail SMTP. Returns status dict."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return {"sent": False, "error": "Gmail SMTP not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD."}

    def _send():
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{from_name} <{GMAIL_ADDRESS}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = GMAIL_ADDRESS

        # HTML email body
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return {"sent": True, "to": to_email, "subject": subject}

    try:
        result = await asyncio.to_thread(_send)
        return result
    except Exception as e:
        return {"sent": False, "error": str(e), "to": to_email}


def build_outreach_email_html(
    business_name: str,
    tagline: str,
    logo_url: str,
    primary_color: str,
    phone: str,
    address: str,
    wa_link: str,
    email_body_text: str,
) -> str:
    """Build a beautiful HTML email template for outreach."""
    logo_html = f'<img src="{logo_url}" alt="{business_name}" style="width:60px;height:60px;border-radius:14px;object-fit:cover;">' if logo_url and logo_url.startswith("http") else f'<div style="width:60px;height:60px;border-radius:14px;background:{primary_color};color:white;display:inline-flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:700;">{business_name[0]}</div>'

    return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;background:#f5f5f5;">
    <div style="max-width:560px;margin:20px auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <!-- Header -->
        <div style="background:linear-gradient(135deg,{primary_color},{primary_color}dd);color:white;padding:32px 28px;text-align:center;">
            {logo_html}
            <h1 style="margin:16px 0 6px;font-size:1.4rem;font-weight:700;">{business_name}</h1>
            <p style="margin:0;font-size:0.9rem;opacity:0.9;">{tagline}</p>
        </div>

        <!-- Body -->
        <div style="padding:28px;">
            <p style="font-size:0.95rem;color:#333;line-height:1.7;margin:0 0 20px;">{email_body_text}</p>

            <!-- CTA Button -->
            <div style="text-align:center;margin:24px 0;">
                <a href="{wa_link}" style="display:inline-block;padding:14px 36px;background:#25D366;color:white;border-radius:50px;text-decoration:none;font-weight:600;font-size:0.95rem;">💬 Order on WhatsApp</a>
            </div>

            <!-- Contact Info -->
            <div style="background:#f8f8f8;border-radius:12px;padding:18px;margin-top:20px;">
                <p style="margin:0 0 6px;font-size:0.85rem;color:#666;">📞 <a href="tel:+91{phone}" style="color:{primary_color};text-decoration:none;">{phone}</a></p>
                <p style="margin:0;font-size:0.85rem;color:#666;">📍 {address}</p>
            </div>
        </div>

        <!-- Footer -->
        <div style="text-align:center;padding:16px 28px;border-top:1px solid #eee;font-size:0.75rem;color:#999;">
            Sent with ❤️ by {business_name} • Powered by GENESIS AI
        </div>
    </div>
</body>
</html>'''
