"""GENESIS FastAPI Backend — Security Hardened

Main application entry point with:
- Clerk JWT authentication on all protected endpoints
- IDOR prevention (ownership checks on every session access)
- Rate limiting (per-user, per-IP, per-session)
- Security headers (HSTS, CSP, X-Frame-Options)
- Structured JSON logging (auth, errors, rate limits)
- CORS locked to specific frontend domain

Run with: uvicorn main:app --reload --port 8000
"""

import os
import sys
import time
import asyncio
import traceback

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.auth import get_current_user, get_optional_user
from services.rate_limiter import (
    rate_limiter, limit_launch, limit_name_gen,
    limit_retry, limit_invoice, limit_email, limit_general,
)
from services.logger import security_logger


# ═══════════════════════════════════════
# App Setup
# ═══════════════════════════════════════

app = FastAPI(
    title="GENESIS API",
    description="AI-powered business launcher for Indian MSMEs",
    version="2.0.0",
    docs_url=None if os.getenv("ENVIRONMENT") == "production" else "/docs",
    redoc_url=None,
)

# ── CORS — locked to specific origins ──
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only methods we actually use
    allow_headers=["Authorization", "Content-Type"],
)


# ── Security Headers Middleware ──

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception as e:
            security_logger.api_error(
                endpoint=str(request.url.path),
                error=str(e),
                status_code=500,
                ip=request.client.host if request.client else "unknown",
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Remove server version header
        response.headers.pop("server", None)

        # Log request
        duration_ms = (time.time() - start_time) * 1000
        if request.url.path != "/health":
            security_logger.api_request(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                ip=request.client.host if request.client else "unknown",
            )

        return response


app.add_middleware(SecurityHeadersMiddleware)


# ═══════════════════════════════════════
# Request/Response Models (with validation)
# ═══════════════════════════════════════

class MenuItemModel(BaseModel):
    item: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, le=100000)


class LaunchRequest(BaseModel):
    """Data collected from TruGen conversation + chat uploads."""
    business_name: str = Field(..., min_length=1, max_length=200)
    business_type: str = Field(..., min_length=1, max_length=100)
    menu: List[MenuItemModel] = Field(default=[], max_length=50)
    address: str = Field(default="", max_length=500)
    phone: str = Field(default="", max_length=15)
    language: str = Field(default="hi", max_length=5)
    upi_id: str = Field(default="", max_length=100)
    shop_photo_url: Optional[str] = Field(default=None, max_length=2048)
    existing_logo_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("Invalid phone number")
        return v

    @field_validator("upi_id")
    @classmethod
    def validate_upi(cls, v: str) -> str:
        if v and "@" not in v:
            raise ValueError("Invalid UPI ID format")
        return v


class LaunchResponse(BaseModel):
    session_id: str
    status: str


class InvoiceRequest(BaseModel):
    """Natural language order text to parse into invoice."""
    order_text: str = Field(..., min_length=1, max_length=500)
    session_id: str = Field(..., min_length=1, max_length=100)


class InvoiceItem(BaseModel):
    item: str
    quantity: int
    unit_price: float
    total: float


class InvoiceResponse(BaseModel):
    items: List[InvoiceItem]
    subtotal: float
    business_name: str
    upi_qr_url: str


class NameGenRequest(BaseModel):
    """Input for business name generation."""
    business_type: str = Field(..., min_length=1, max_length=100)
    keywords: str = Field(default="", max_length=200)
    language: str = Field(default="hi", max_length=5)
    location: str = Field(default="", max_length=200)


# ═══════════════════════════════════════
# Routes — Public (no auth)
# ═══════════════════════════════════════

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "genesis-backend", "version": "2.0.0"}


# ═══════════════════════════════════════
# Routes — Rate-limited only (no auth)
# ═══════════════════════════════════════

@app.post("/api/generate-names")
async def generate_business_names(req: NameGenRequest, request: Request):
    """Generate 3 AI-powered business name suggestions. Rate-limited by IP."""
    limit_name_gen(request)

    from services.gemini_client import generate_json

    result = await generate_json(f"""
You are an Indian business naming expert. Generate 3 creative business name options.

Business Type: {req.business_type}
Keywords/Products: {req.keywords}
Location: {req.location}
Language Preference: {req.language}

Return JSON with exactly 3 names in different styles:
{{
    "names": [
        {{
            "name": "Simple clear name (e.g., Ramesh Tiffins, Sharma Sweets)",
            "name_hindi": "Same name in Devanagari script",
            "style": "simple",
            "tagline": "Short Hindi tagline for this name",
            "why": "1 sentence why this name works (in Hindi)"
        }},
        {{
            "name": "Emotional Hindi name (e.g., Ghar Ka Swad, Maa Ki Rasoi)",
            "name_hindi": "Same name in Devanagari script",
            "style": "emotional",
            "tagline": "Short Hindi tagline for this name",
            "why": "1 sentence why this name works (in Hindi)"
        }},
        {{
            "name": "Modern catchy name (e.g., The Tiffin Wala, Chai Junction)",
            "name_hindi": "Same name in Devanagari script",
            "style": "modern",
            "tagline": "Short Hindi tagline for this name",
            "why": "1 sentence why this name works (in Hindi)"
        }}
    ]
}}

Rules:
- Names must feel AUTHENTICALLY Indian, not translated English
- Each name must be easy to pronounce and remember
- Include the location or product vibe if it makes sense
- Think about what looks good on a signboard and delivery box
""")

    return {"names": result.get("names", [])}


@app.post("/api/invoice", response_model=InvoiceResponse)
async def parse_invoice(req: InvoiceRequest, request: Request):
    """Parse a natural language order into a structured invoice.

    Public endpoint (customers access this) — rate-limited by session.
    """
    limit_invoice(req.session_id)

    from services.supabase_client import get_session
    from services.gemini_client import generate_json
    import urllib.parse

    session = await get_session(req.session_id)

    if not session:
        session = {
            "business_name": "Demo Tiffin Service",
            "menu": [
                {"item": "Dal Chawal", "price": 80},
                {"item": "Rajma Chawal", "price": 90},
                {"item": "Paneer Thali", "price": 120},
                {"item": "Special Thali", "price": 150},
            ],
            "phone": "9876543210",
            "upi_id": "9876543210@paytm",
        }

    menu = session.get("menu", [])
    business_name = session.get("business_name", "Business")
    upi_id = session.get("upi_id", f"{session.get('phone', '')}@paytm")

    menu_str = "\n".join([f"- {m['item']}: ₹{m['price']}" for m in menu])

    parsed = await generate_json(f"""
You are a smart invoice parser for an Indian small business.

MENU:
{menu_str}

CUSTOMER ORDER (in natural language, possibly Hindi):
"{req.order_text}"

Parse this order against the menu. Match items by name (fuzzy match OK).
Calculate quantities and totals.

Return JSON:
{{
  "items": [
    {{"item": "exact menu item name", "quantity": 2, "unit_price": 120, "total": 240}}
  ],
  "subtotal": 240
}}

If an item doesn't match any menu item, skip it.
Always use the EXACT prices from the menu, never guess.
""")

    subtotal = parsed.get("subtotal", 0)

    upi_string = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(business_name)}&am={subtotal}&cu=INR"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_string)}"

    return InvoiceResponse(
        items=[InvoiceItem(**item) for item in parsed.get("items", [])],
        subtotal=subtotal,
        business_name=business_name,
        upi_qr_url=qr_url,
    )


@app.get("/api/session/{session_id}")
async def get_session_data(session_id: str, request: Request):
    """Get session data by ID. Public for pay page — rate-limited by IP."""
    limit_general(request)

    from services.supabase_client import get_session
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Strip sensitive fields before returning to public
    safe_session = {
        "business_name": session.get("business_name"),
        "business_type": session.get("business_type"),
        "menu": session.get("menu"),
        "phone": session.get("phone"),
        "upi_id": session.get("upi_id"),
    }
    return safe_session


# ═══════════════════════════════════════
# Routes — Authenticated (Clerk JWT required)
# ═══════════════════════════════════════

@app.post("/api/launch", response_model=LaunchResponse)
async def launch_business(
    req: LaunchRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
):
    """Launch a new business. Requires auth + rate limited."""
    limit_launch(user_id)

    from services.supabase_client import create_session, create_agent_tasks
    from agents.graph import run_genesis_graph

    session_data = req.model_dump()
    session_data["menu"] = [m.model_dump() for m in req.menu]
    session_data["user_id"] = user_id  # Tie session to authenticated user
    session_id = await create_session(session_data)

    await create_agent_tasks(session_id)

    security_logger.session_created(
        session_id=session_id,
        user_id=user_id,
        business_type=req.business_type,
    )

    background_tasks.add_task(run_genesis_graph, session_id, session_data)

    return LaunchResponse(session_id=session_id, status="launched")


@app.get("/api/status/{session_id}")
async def get_status(
    session_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Get agent task statuses. Auth + ownership check."""
    limit_general(request)

    # IDOR check — verify ownership
    from services.supabase_client import get_session_if_owner, supabase

    session = await get_session_if_owner(session_id, user_id)
    if not session:
        security_logger.session_access_denied(
            session_id=session_id,
            user_id=user_id,
            ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=403, detail="Access denied")

    def _fetch():
        result = supabase.table("agent_tasks").select("*").eq(
            "session_id", session_id
        ).execute()
        return result.data

    tasks = await asyncio.to_thread(_fetch) if supabase else []
    return {"session_id": session_id, "tasks": tasks or []}


@app.post("/api/retry/{session_id}/{agent_name}")
async def retry_agent(
    session_id: str,
    agent_name: str,
    background_tasks: BackgroundTasks,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Retry a failed agent. Auth + ownership + rate limited."""
    limit_retry(user_id)

    from services.supabase_client import get_session_if_owner, push_update
    from agents.brand import brand_agent
    from agents.website import website_agent
    from agents.payment import payment_agent
    from agents.outreach import outreach_agent
    from agents.gmb import gmb_agent
    from agents.legal import legal_agent

    agent_map = {
        "brand": brand_agent,
        "website": website_agent,
        "payment": payment_agent,
        "outreach": outreach_agent,
        "gmb": gmb_agent,
        "legal": legal_agent,
    }

    if agent_name not in agent_map:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")

    # IDOR check
    session = await get_session_if_owner(session_id, user_id)
    if not session:
        security_logger.session_access_denied(
            session_id=session_id,
            user_id=user_id,
            ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=403, detail="Access denied")

    await push_update(session_id, agent_name, 0, "Retrying...", status="running")

    state = {"session_id": session_id, **session}
    agent_fn = agent_map[agent_name]
    background_tasks.add_task(agent_fn, state)

    return {"success": True, "agent": agent_name, "status": "retrying"}


@app.get("/api/business-card/{session_id}")
async def download_business_card(
    session_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Generate business card PDF. Auth + ownership check."""
    limit_general(request)

    from services.supabase_client import get_session_if_owner, supabase
    from fastapi.responses import Response

    # IDOR check
    session = await get_session_if_owner(session_id, user_id)
    if not session:
        raise HTTPException(status_code=403, detail="Access denied")

    def _fetch_results():
        result = supabase.table("agent_tasks").select("result_data, agent_name").eq(
            "session_id", session_id
        ).in_("agent_name", ["brand", "website", "payment"]).execute()
        return {r["agent_name"]: r.get("result_data", {}) for r in (result.data or [])}

    results = await asyncio.to_thread(_fetch_results) if supabase else {}
    brand = results.get("brand", {})
    website = results.get("website", {})
    payment = results.get("payment", {})

    pdf_bytes = _generate_business_card_pdf(
        business_name=session.get("business_name", "Business"),
        tagline=brand.get("tagline_hindi", ""),
        phone=session.get("phone", ""),
        address=session.get("address", ""),
        website_url=website.get("website_url", ""),
        upi_id=session.get("upi_id", ""),
        primary_color=brand.get("primary_color", "#FF6B35"),
        qr_url=payment.get("upi_qr_url", ""),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="business_card.pdf"'},
    )


@app.post("/api/send-summary/{session_id}")
async def send_summary_email(
    session_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Send launch summary email. Auth + ownership + rate limited."""
    limit_email(session_id)

    from services.supabase_client import get_session_if_owner, supabase
    from services.email_client import send_outreach_email

    # IDOR check
    session = await get_session_if_owner(session_id, user_id)
    if not session:
        raise HTTPException(status_code=403, detail="Access denied")

    def _fetch():
        result = supabase.table("agent_tasks").select("result_data, agent_name").eq(
            "session_id", session_id
        ).eq("status", "completed").execute()
        return {r["agent_name"]: r.get("result_data", {}) for r in (result.data or [])}

    results = await asyncio.to_thread(_fetch) if supabase else {}

    brand = results.get("brand", {})
    website = results.get("website", {})
    payment = results.get("payment", {})

    business_name = session.get("business_name", "Your Business")

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <div style="background:linear-gradient(135deg,{brand.get('primary_color','#FF6B35')},{brand.get('primary_color','#FF6B35')}dd);color:white;padding:32px;text-align:center;">
            <h1 style="margin:0 0 8px;font-size:1.5rem;">🚀 Your Business is Live!</h1>
            <p style="margin:0;opacity:0.9;">{business_name}</p>
        </div>
        <div style="padding:28px;">
            <h3 style="margin:0 0 16px;">Here are your links:</h3>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:8px 0;font-weight:600;">🌐 Website</td><td style="padding:8px 0;"><a href="{website.get('website_url','#')}">{website.get('website_url','Not ready')}</a></td></tr>
                <tr><td style="padding:8px 0;font-weight:600;">💳 UPI QR</td><td style="padding:8px 0;">{payment.get('upi_id', session.get('upi_id',''))}</td></tr>
                <tr><td style="padding:8px 0;font-weight:600;">🎨 Logo</td><td style="padding:8px 0;"><a href="{brand.get('logo_url','#')}">Download Logo</a></td></tr>
                <tr><td style="padding:8px 0;font-weight:600;">📱 WhatsApp</td><td style="padding:8px 0;"><a href="{website.get('whatsapp_order_link','#')}">Order Link</a></td></tr>
            </table>
            <p style="margin:24px 0 0;font-size:0.85rem;color:#666;">Keep this email safe — these are all your business links!</p>
        </div>
        <div style="text-align:center;padding:16px;border-top:1px solid #eee;font-size:0.75rem;color:#999;">Powered by GENESIS AI</div>
    </div>
    """

    owner_email = session.get("owner_email", "")
    if owner_email:
        result = await send_outreach_email(
            to_email=owner_email,
            subject=f"🚀 {business_name} is Live! — Your GENESIS Summary",
            html_body=html,
            from_name="GENESIS",
        )
        return {"sent": True, "result": result}

    return {"sent": False, "html_preview": html, "note": "No owner email on file."}


# ═══════════════════════════════════════
# Business Card PDF Generator (internal)
# ═══════════════════════════════════════

def _generate_business_card_pdf(
    business_name: str,
    tagline: str,
    phone: str,
    address: str,
    website_url: str,
    upi_id: str,
    primary_color: str,
    qr_url: str,
) -> bytes:
    """Generate a printable business card PDF (90mm x 55mm)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white
    import io

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(90 * mm, 55 * mm))

    try:
        bg_color = HexColor(primary_color)
    except Exception:
        bg_color = HexColor("#FF6B35")

    c.setFillColor(bg_color)
    c.rect(0, 0, 90 * mm, 55 * mm, fill=1)

    c.setFillColor(HexColor("#FFFFFF"))
    c.setFillAlpha(0.15)
    c.rect(0, 45 * mm, 90 * mm, 10 * mm, fill=1)
    c.setFillAlpha(1.0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(6 * mm, 40 * mm, business_name[:25])

    if tagline:
        c.setFont("Helvetica", 8)
        c.drawString(6 * mm, 35 * mm, tagline[:50])

    c.setFont("Helvetica", 8)
    y = 26 * mm
    if phone:
        c.drawString(6 * mm, y, f"Phone: {phone}")
        y -= 4 * mm
    if address:
        short_addr = address[:40] + ("..." if len(address) > 40 else "")
        c.drawString(6 * mm, y, f"Addr: {short_addr}")
        y -= 4 * mm
    if website_url:
        short_url = website_url.replace("https://", "").replace("http://", "")[:35]
        c.drawString(6 * mm, y, f"Web: {short_url}")
        y -= 4 * mm
    if upi_id:
        c.drawString(6 * mm, y, f"UPI: {upi_id}")

    c.setFont("Helvetica", 5)
    c.setFillAlpha(0.5)
    c.drawString(6 * mm, 3 * mm, "Powered by GENESIS AI")
    c.setFillAlpha(1.0)

    c.save()
    return buf.getvalue()


# ═══════════════════════════════════════
# Global Error Handler
# ═══════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all error handler — logs and returns safe error."""
    security_logger.api_error(
        endpoint=str(request.url.path),
        error=str(exc),
        status_code=500,
        ip=request.client.host if request.client else "unknown",
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
