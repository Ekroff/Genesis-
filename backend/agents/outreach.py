"""Outreach Agent — Finds nearby businesses + generates WhatsApp/email outreach.

What it produces:
- List of nearby businesses (via Google Places API)
- Personalized WhatsApp messages (wa.me links)
- Actual Gmail SMTP emails sent to leads
- Email templates for cold outreach
- Outreach schedule suggestion

Dependencies: None (runs in parallel with Brand, Payment, Legal)
Writes to state: nearby_businesses, whatsapp_links
"""

from agents.state import GenesisState
from services.supabase_client import push_update
from services.places_client import find_nearby_businesses
from services.gemini_client import generate_json
from services.email_client import send_outreach_email, build_outreach_email_html
from config import GMAIL_ADDRESS
import urllib.parse
import traceback


async def outreach_agent(state: GenesisState) -> dict:
    """Run the Outreach Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Find Nearby Businesses (0% → 30%)
        # ══════════════════════════════════════
        await push_update(sid, "outreach", 10, "Finding nearby businesses... 📍")

        address = state.get("address", "")
        business_type = state.get("business_type", "")

        nearby = []
        if address:
            nearby = await find_nearby_businesses(address, business_type, max_results=10)
            await push_update(sid, "outreach", 30, f"Found {len(nearby)} nearby businesses! 🎯")
        else:
            await push_update(sid, "outreach", 30, "No address provided, skipping place search ⚠️")

        # ══════════════════════════════════════
        # PHASE 2: Generate Outreach Messages (30% → 55%)
        # ══════════════════════════════════════
        await push_update(sid, "outreach", 35, "Creating personalized messages... 📧")

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
    "email_body": "Short email body in English (3-4 sentences, professional, include contact info and a warm intro about the business)",
    "email_body_hindi": "Same email body but in Hindi (3-4 sentences, warm and personal)",
    "daily_tip": "One tip for the business owner on how to get more customers (in Hindi, max 100 chars)"
}}

Make messages feel personal and warm, not salesy. Think local neighborhood business.
""")

        await push_update(sid, "outreach", 55, "Messages ready! Creating links... 🔗")

        # ══════════════════════════════════════
        # PHASE 3: Generate WhatsApp Links (55% → 70%)
        # ══════════════════════════════════════
        whatsapp_msg = outreach_data.get("whatsapp_intro", f"नमस्ते! {business_name} से बात कर रहे हैं 🙏")

        whatsapp_links = []
        for biz in nearby[:10]:
            biz_phone = biz.get("phone", "").replace(" ", "").replace("-", "")
            if biz_phone:
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
                    "email": biz.get("email", ""),
                })

        await push_update(sid, "outreach", 70, f"Created {len(whatsapp_links)} WhatsApp links! 📱")

        # ══════════════════════════════════════
        # PHASE 4: Send Emails via Gmail SMTP (70% → 90%)
        # ══════════════════════════════════════
        emails_sent = 0
        email_results = []

        if GMAIL_ADDRESS:
            await push_update(sid, "outreach", 75, "Sending outreach emails... 📧")

            # Build the branded HTML email
            wa_msg = urllib.parse.quote(f"Hi! I'd like to place an order from {business_name}")
            wa_link = f"https://wa.me/91{phone}?text={wa_msg}" if phone else "#"

            email_html = build_outreach_email_html(
                business_name=business_name,
                tagline=state.get("tagline_hindi", state.get("tagline_english", business_name)),
                logo_url=state.get("logo_url", ""),
                primary_color=state.get("primary_color", "#FF6B35"),
                phone=phone,
                address=address,
                wa_link=wa_link,
                email_body_text=outreach_data.get("email_body", f"We are {business_name}, your new neighborhood partner."),
            )

            email_subject = outreach_data.get("email_subject", f"Introducing {business_name} — Your New Local Favorite!")

            # Send to leads that have email addresses
            for lead in nearby[:5]:  # Limit to 5 emails per session to avoid spam
                lead_email = lead.get("email", "")
                if lead_email and "@" in lead_email:
                    result = await send_outreach_email(
                        to_email=lead_email,
                        subject=email_subject,
                        html_body=email_html,
                        from_name=business_name,
                    )
                    email_results.append(result)
                    if result.get("sent"):
                        emails_sent += 1

            # Also send a copy to the business owner as a preview
            owner_email = state.get("owner_email", "")
            if owner_email and "@" in owner_email:
                preview_result = await send_outreach_email(
                    to_email=owner_email,
                    subject=f"[Preview] {email_subject}",
                    html_body=email_html,
                    from_name="GENESIS — Email Preview",
                )
                email_results.append(preview_result)

            await push_update(sid, "outreach", 88, f"Sent {emails_sent} outreach emails! ✉️")
        else:
            await push_update(sid, "outreach", 88, "Gmail not configured — email templates saved 📝")

        # ══════════════════════════════════════
        # PHASE 5: Complete (90% → 100%)
        # ══════════════════════════════════════

        result_data = {
            "nearby_businesses": nearby,
            "nearby_count": len(nearby),
            "whatsapp_links": whatsapp_links,
            "whatsapp_count": len(whatsapp_links),
            "whatsapp_intro": outreach_data.get("whatsapp_intro", ""),
            "whatsapp_offer": outreach_data.get("whatsapp_offer", ""),
            "email_subject": outreach_data.get("email_subject", ""),
            "email_body": outreach_data.get("email_body", ""),
            "email_body_hindi": outreach_data.get("email_body_hindi", ""),
            "emails_sent": emails_sent,
            "email_results": email_results,
            "gmail_configured": bool(GMAIL_ADDRESS),
            "daily_tip": outreach_data.get("daily_tip", ""),
        }

        status_msg = f"Outreach ready! {len(nearby)} leads, {len(whatsapp_links)} WhatsApp, {emails_sent} emails ✅"
        await push_update(
            sid, "outreach", 100,
            status_msg,
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
