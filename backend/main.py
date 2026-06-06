"""GENESIS FastAPI Backend

Main application entry point. Handles:
- POST /api/launch — Creates session + fires LangGraph agents
- POST /api/verify — Photo upload processing  
- POST /api/invoice — Smart Invoice order parsing
- GET /health — Health check

Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="GENESIS API",
    description="AI-powered business launcher for Indian MSMEs",
    version="1.0.0",
)

# CORS — allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════

class MenuItemModel(BaseModel):
    item: str
    price: float


class LaunchRequest(BaseModel):
    """Data collected from TruGen conversation + chat uploads."""
    business_name: str
    business_type: str
    menu: List[MenuItemModel] = []
    address: str = ""
    phone: str = ""
    language: str = "hi"
    upi_id: str = ""
    shop_photo_url: Optional[str] = None
    existing_logo_url: Optional[str] = None
    user_id: str = "anonymous"


class LaunchResponse(BaseModel):
    session_id: str
    status: str


class InvoiceRequest(BaseModel):
    """Natural language order text to parse into invoice."""
    order_text: str
    session_id: str


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


# ═══════════════════════════════════════
# Routes
# ═══════════════════════════════════════

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "genesis-backend"}


@app.post("/api/launch", response_model=LaunchResponse)
async def launch_business(req: LaunchRequest, background_tasks: BackgroundTasks):
    """Launch a new business.
    
    1. Creates a session in Supabase
    2. Creates 6 agent_tasks rows (one per agent)
    3. Starts LangGraph supervisor in background
    4. Returns session_id immediately (agents run async)
    """
    from services.supabase_client import create_session, create_agent_tasks
    from agents.graph import run_genesis_graph

    # Create session
    session_data = req.model_dump()
    session_data["menu"] = [m.model_dump() for m in req.menu]
    session_id = await create_session(session_data)

    # Create 6 agent task rows (all start as "pending")
    await create_agent_tasks(session_id)

    # Start LangGraph in background — returns immediately to frontend
    background_tasks.add_task(run_genesis_graph, session_id, session_data)

    return LaunchResponse(session_id=session_id, status="launched")


@app.post("/api/invoice", response_model=InvoiceResponse)
async def parse_invoice(req: InvoiceRequest):
    """Parse a natural language order into a structured invoice.
    
    Example input: "2 paneer thali 1 dal chawal"
    Returns: line items with quantities, prices, total, and exact-amount UPI QR.
    """
    from services.supabase_client import get_session
    from services.gemini_client import generate_json
    import urllib.parse

    # Get session data (menu, business name, UPI)
    session = await get_session(req.session_id)

    if not session:
        # Fallback demo data
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

    # Gemini parses natural language order against menu
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

    # Generate exact-amount UPI QR
    upi_string = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(business_name)}&am={subtotal}&cu=INR"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_string)}"

    return InvoiceResponse(
        items=[InvoiceItem(**item) for item in parsed.get("items", [])],
        subtotal=subtotal,
        business_name=business_name,
        upi_qr_url=qr_url,
    )


@app.get("/api/session/{session_id}")
async def get_session_data(session_id: str):
    """Get session data by ID. Used by invoice page."""
    from services.supabase_client import get_session
    session = await get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    return session


@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """Get all agent task statuses for a session. Used by dashboard polling and E2E tests."""
    from services.supabase_client import supabase
    import asyncio

    if not supabase:
        return {"session_id": session_id, "tasks": []}

    def _fetch():
        result = supabase.table("agent_tasks").select("*").eq(
            "session_id", session_id
        ).execute()
        return result.data

    tasks = await asyncio.to_thread(_fetch)
    return {"session_id": session_id, "tasks": tasks or []}


@app.post("/api/retry/{session_id}/{agent_name}")
async def retry_agent(session_id: str, agent_name: str, background_tasks: BackgroundTasks):
    """Retry a single failed agent without restarting the whole pipeline."""
    from services.supabase_client import get_session, push_update
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
        return {"error": f"Unknown agent: {agent_name}"}

    # Get session data to rebuild state
    session = await get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    # Reset agent to running
    await push_update(session_id, agent_name, 0, "Retrying...", status="running")

    # Build state from session
    state = {
        "session_id": session_id,
        **session,
    }

    # Run the single agent in background
    agent_fn = agent_map[agent_name]
    background_tasks.add_task(agent_fn, state)

    return {"success": True, "agent": agent_name, "status": "retrying"}


@app.get("/api/business-card/{session_id}")
async def download_business_card(session_id: str):
    """Generate and return a printable business card PDF."""
    from services.supabase_client import get_session
    from fastapi.responses import Response
    import asyncio

    session = await get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    # Get agent results for brand data
    from services.supabase_client import supabase

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
        headers={"Content-Disposition": f'attachment; filename="{session.get("business_name", "card")}_business_card.pdf"'},
    )


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

    # Background
    try:
        bg_color = HexColor(primary_color)
    except Exception:
        bg_color = HexColor("#FF6B35")

    c.setFillColor(bg_color)
    c.rect(0, 0, 90 * mm, 55 * mm, fill=1)

    # White accent stripe at top
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFillAlpha(0.15)
    c.rect(0, 45 * mm, 90 * mm, 10 * mm, fill=1)
    c.setFillAlpha(1.0)

    # Business Name
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(6 * mm, 40 * mm, business_name[:25])

    # Tagline
    if tagline:
        c.setFont("Helvetica", 8)
        c.drawString(6 * mm, 35 * mm, tagline[:50])

    # Contact details
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

    # GENESIS watermark
    c.setFont("Helvetica", 5)
    c.setFillAlpha(0.5)
    c.drawString(6 * mm, 3 * mm, "Powered by GENESIS AI")
    c.setFillAlpha(1.0)

    c.save()
    return buf.getvalue()


@app.post("/api/send-summary/{session_id}")
async def send_summary_email(session_id: str):
    """Send a launch summary email to the business owner with all links."""
    from services.supabase_client import get_session, supabase
    from services.email_client import send_outreach_email
    import asyncio

    session = await get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    # Get all agent results
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

    return {"sent": False, "html_preview": html, "note": "No owner email on file. Add owner_email to session data."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

