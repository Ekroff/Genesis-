"""Outreach Agent — Finds nearby businesses + generates WhatsApp/email outreach.

What it produces:
- List of nearby businesses (via Google Places API)
- Personalized WhatsApp messages (wa.me links)
- Email templates for cold outreach
- Outreach schedule suggestion

Dependencies: None (runs in parallel with Brand, Payment, Legal)
Writes to state: nearby_businesses, whatsapp_links
"""

from agents.state import GenesisState
from services.supabase_client import push_update
from services.places_client import find_nearby_businesses
from services.gemini_client import generate_json
import urllib.parse
import traceback


async def outreach_agent(state: GenesisState) -> dict:
    """Run the Outreach Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Find Nearby Businesses (0% → 40%)
        # ══════════════════════════════════════
        await push_update(sid, "outreach", 10, "Finding nearby businesses... 📍")

        address = state.get("address", "")
        business_type = state.get("business_type", "")

        nearby = []
        if address:
            nearby = await find_nearby_businesses(address, business_type, max_results=10)
            await push_update(sid, "outreach", 35, f"Found {len(nearby)} nearby businesses! 🎯")
        else:
            await push_update(sid, "outreach", 35, "No address provided, skipping place search ⚠️")

        # ══════════════════════════════════════
        # PHASE 2: Generate Outreach Messages (40% → 75%)
        # ══════════════════════════════════════
        await push_update(sid, "outreach", 45, "Creating personalized messages... 📧")

        business_name = state["business_name"]
        phone = state.get("phone", "")
        menu = state.get("menu", [])
        language = state.get("language", "hi")

        menu_str = ""
        if menu:
            items = [f"{m['item']} (₹{m['price']})" for m in menu[:5]]
            menu_str = f"\nMenu highlights: {', '.join(items)}"

        # Generate outreach templates via Gemini
        outreach_data = await generate_json(f"""
Create outreach messages for an Indian small business trying to get customers.

Business: {business_name}
Type: {business_type}
Phone: {phone}
Language: {language}{menu_str}

Generate JSON with:
{{
    "whatsapp_intro": "Short WhatsApp intro message in Hindi (max 200 chars, include emoji, mention business name and what you offer)",
    "whatsapp_offer": "Special offer message in Hindi (max 200 chars, include a first-order discount or free delivery offer)",
    "email_subject": "Email subject line in English (professional, max 60 chars)",
    "email_body": "Short email body in English (3-4 sentences, professional, include contact info)",
    "daily_tip": "One tip for the business owner on how to get more customers (in Hindi, max 100 chars)"
}}

Make messages feel personal and warm, not salesy. Think local neighborhood business.
""")

        await push_update(sid, "outreach", 65, "Messages ready! Creating links... 🔗")

        # ══════════════════════════════════════
        # PHASE 3: Generate WhatsApp Links (75% → 100%)
        # ══════════════════════════════════════
        whatsapp_msg = outreach_data.get("whatsapp_intro", f"नमस्ते! {business_name} से बात कर रहे हैं 🙏")

        whatsapp_links = []
        for biz in nearby[:10]:
            biz_phone = biz.get("phone", "").replace(" ", "").replace("-", "")
            if biz_phone:
                # Clean phone number
                if biz_phone.startswith("+91"):
                    biz_phone = biz_phone[3:]
                elif biz_phone.startswith("0"):
                    biz_phone = biz_phone[1:]

                wa_link = f"https://wa.me/91{biz_phone}?text={urllib.parse.quote(whatsapp_msg)}"
                whatsapp_links.append({
                    "business_name": biz["name"],
                    "phone": biz_phone,
                    "wa_link": wa_link,
                    "address": biz.get("address", ""),
                })

        await push_update(sid, "outreach", 85, f"Created {len(whatsapp_links)} WhatsApp links! 📱")

        # Build result data
        result_data = {
            "nearby_businesses": nearby,
            "nearby_count": len(nearby),
            "whatsapp_links": whatsapp_links,
            "whatsapp_count": len(whatsapp_links),
            "whatsapp_intro": outreach_data.get("whatsapp_intro", ""),
            "whatsapp_offer": outreach_data.get("whatsapp_offer", ""),
            "email_subject": outreach_data.get("email_subject", ""),
            "email_body": outreach_data.get("email_body", ""),
            "daily_tip": outreach_data.get("daily_tip", ""),
        }

        await push_update(
            sid, "outreach", 100,
            f"Outreach ready! {len(nearby)} leads, {len(whatsapp_links)} WhatsApp links ✅",
            status="completed",
            result_data=result_data,
        )

        return {
            "nearby_businesses": nearby,
            "whatsapp_links": whatsapp_links,
            "completed_agents": ["outreach"],
        }

    except Exception as e:
        error_msg = f"Outreach Agent error: {str(e)}"
        print(f"[OutreachAgent] ERROR: {traceback.format_exc()}")
        await push_update(sid, "outreach", 0, error_msg, status="error")

        return {
            "nearby_businesses": [],
            "whatsapp_links": [],
            "completed_agents": ["outreach"],
        }
