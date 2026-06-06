"""Brand Agent — Creates brand identity + brand guidelines PDF.

What it produces:
- Logo (via fal.ai)
- Primary + secondary colors
- Hindi + English tagline
- Font recommendation
- Brand Guidelines PDF (color palette, typography, do's/don'ts)

Dependencies: None (runs in parallel with Payment, Outreach, Legal)
Writes to state: logo_url, primary_color, secondary_color, tagline_hindi, tagline_english
"""

from agents.state import GenesisState
from services.supabase_client import push_update
from services.fal_client import generate_logo
from services.gemini_client import generate_json
from services.brand_guidelines import generate_brand_guidelines_pdf
import traceback


async def brand_agent(state: GenesisState) -> dict:
    """Run the Brand Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Logo Generation (0% → 35%)
        # ══════════════════════════════════════
        await push_update(sid, "brand", 5, "Starting brand creation... 🎨")

        if state.get("existing_logo_url"):
            logo_url = state["existing_logo_url"]
            await push_update(sid, "brand", 25, "Using your existing logo ✅")
        else:
            await push_update(sid, "brand", 10, "Creating your logo... 🎨")
            logo_url = await generate_logo(
                state["business_name"],
                state["business_type"],
            )
            await push_update(sid, "brand", 35, "Logo generated! ✅")

        # ══════════════════════════════════════
        # PHASE 2: Brand Identity (35% → 65%)
        # ══════════════════════════════════════
        await push_update(sid, "brand", 40, "Generating colors + tagline... 🎨")

        menu_str = ""
        if state.get("menu"):
            menu_items = [f"{m['item']} (₹{m['price']})" for m in state["menu"]]
            menu_str = f"\nMenu items: {', '.join(menu_items)}"

        brand_data = await generate_json(f"""
Create a complete brand identity for an Indian small business.

Business Name: {state["business_name"]}
Business Type: {state["business_type"]}
Language: {state.get("language", "hi")}
Address: {state.get("address", "")}
{menu_str}

Return JSON with these exact keys:
{{
    "primary_color": "#hex (warm, inviting, suitable for {state["business_type"]})",
    "secondary_color": "#hex (complementary background/accent color)",
    "tagline_hindi": "catchy Hindi tagline, max 8 words, emotionally resonant",
    "tagline_english": "English translation of the Hindi tagline",
    "font": "Google Font name that fits this brand (e.g., Poppins, Nunito, Outfit)",
    "brand_mood": "3 adjective description (e.g., warm, homely, trustworthy)",
    "whatsapp_status": "WhatsApp Business status text, max 100 chars"
}}

Make the tagline feel authentic Indian — not corporate English translated to Hindi.
Think about what a local business owner would actually say proudly.
""")

        primary_color = brand_data.get("primary_color", "#FF6B35")
        secondary_color = brand_data.get("secondary_color", "#FFF8F0")
        tagline_hindi = brand_data.get("tagline_hindi", "")
        tagline_english = brand_data.get("tagline_english", "")

        await push_update(sid, "brand", 65, "Brand identity ready! 🎨")

        # ══════════════════════════════════════
        # PHASE 3: Brand Guidelines PDF (65% → 90%)
        # ══════════════════════════════════════
        await push_update(sid, "brand", 70, "Creating brand guidelines PDF... 📄")

        brand_pdf_url = await generate_brand_guidelines_pdf(
            session_id=sid,
            business_name=state["business_name"],
            tagline_hindi=tagline_hindi,
            tagline_english=tagline_english,
            primary_color=primary_color,
            secondary_color=secondary_color,
            font_name=brand_data.get("font", "Poppins"),
            brand_mood=brand_data.get("brand_mood", ""),
            logo_url=logo_url,
        )

        await push_update(sid, "brand", 90, "Brand guidelines PDF ready! 📄")

        # ══════════════════════════════════════
        # PHASE 4: Complete (90% → 100%)
        # ══════════════════════════════════════
        photo_urls = []
        if state.get("shop_photo_url"):
            photo_urls.append(state["shop_photo_url"])

        result_data = {
            "logo_url": logo_url,
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "tagline_hindi": tagline_hindi,
            "tagline_english": tagline_english,
            "font": brand_data.get("font", "Poppins"),
            "brand_mood": brand_data.get("brand_mood", ""),
            "whatsapp_status": brand_data.get("whatsapp_status", ""),
            "brand_guidelines_pdf": brand_pdf_url,
        }

        await push_update(
            sid, "brand", 100,
            "Brand identity + guidelines PDF ready! ✅",
            status="completed",
            result_data=result_data,
        )

        completed = list(state.get("completed_agents", []))
        completed.append("brand")

        return {
            "logo_url": logo_url,
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "tagline_hindi": tagline_hindi,
            "tagline_english": tagline_english,
            "photo_urls": photo_urls,
            "completed_agents": completed,
        }

    except Exception as e:
        error_msg = f"Brand Agent error: {str(e)}"
        print(f"[BrandAgent] ERROR: {traceback.format_exc()}")
        await push_update(sid, "brand", 0, error_msg, status="error")

        completed = list(state.get("completed_agents", []))
        completed.append("brand")

        return {
            "logo_url": state.get("logo_url"),
            "primary_color": "#FF6B35",
            "secondary_color": "#FFF8F0",
            "tagline_hindi": state.get("business_name", ""),
            "tagline_english": state.get("business_name", ""),
            "photo_urls": [],
            "completed_agents": completed,
        }
