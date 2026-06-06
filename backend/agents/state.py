from typing import TypedDict, List, Optional


class MenuItem(TypedDict):
    item: str
    price: float


class GenesisState(TypedDict):
    """Shared state that ALL agents read from and write to.
    
    This is the ONLY communication channel between agents.
    No agent talks directly to another — they all go through state.
    LangGraph manages state merging automatically.
    """

    # ── INPUT (from TruGen conversation + Chat uploads) ──
    session_id: str
    user_id: str
    business_name: str
    business_type: str
    menu: List[MenuItem]
    address: str
    phone: str
    language: str             # hi, ta, te, bn, etc.
    upi_id: str               # e.g. 9876543210@paytm
    shop_photo_url: Optional[str]
    existing_logo_url: Optional[str]

    # ── SUPERVISOR STATE ──
    completed_agents: List[str]

    # ── BRAND AGENT OUTPUT ──
    logo_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    tagline_hindi: Optional[str]
    tagline_english: Optional[str]
    photo_urls: List[str]

    # ── WEBSITE AGENT OUTPUT ──
    website_url: Optional[str]

    # ── PAYMENT AGENT OUTPUT ──
    upi_qr_url: Optional[str]
    invoice_page_url: Optional[str]

    # ── OUTREACH AGENT OUTPUT ──
    nearby_businesses: List[dict]
    whatsapp_links: List[dict]

    # ── GMB AGENT OUTPUT ──
    gmb_status: Optional[str]

    # ── LEGAL AGENT OUTPUT ──
    legal_pdf_url: Optional[str]
    legal_checklist: List[dict]
