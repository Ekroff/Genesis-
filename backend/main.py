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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
