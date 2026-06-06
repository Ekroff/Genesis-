"""Website Agent — Builds and deploys a branded website for the business.

What it produces:
- Selects best HTML template based on business type
- Injects brand data (logo, colors, tagline, menu)
- Generates the full HTML
- Saves to Supabase Storage (accessible via public URL)
- Future: Deploy to Render

Dependencies: Brand Agent must complete first (needs logo, colors, tagline)
Writes to state: website_url
"""

from agents.state import GenesisState
from services.supabase_client import push_update, upload_to_storage
from services.gemini_client import generate_text
import traceback
import urllib.parse


async def website_agent(state: GenesisState) -> dict:
    """Run the Website Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Select Template (0% → 20%)
        # ══════════════════════════════════════
        await push_update(sid, "website", 10, "Selecting best template... 🌐")

        business_type = state.get("business_type", "")
        template_name = _select_template(business_type)

        await push_update(sid, "website", 20, f"Using '{template_name}' template 🎨")

        # ══════════════════════════════════════
        # PHASE 2: Build Website HTML (20% → 60%)
        # ══════════════════════════════════════
        await push_update(sid, "website", 30, "Building your website... 🔨")

        # Collect all brand data
        business_name = state["business_name"]
        logo_url = state.get("logo_url", "")
        primary_color = state.get("primary_color", "#FF6B35")
        secondary_color = state.get("secondary_color", "#FFF8F0")
        tagline_hindi = state.get("tagline_hindi", "")
        tagline_english = state.get("tagline_english", "")
        phone = state.get("phone", "")
        address = state.get("address", "")
        upi_id = state.get("upi_id", "")
        menu = state.get("menu", [])
        upi_qr_url = state.get("upi_qr_url", "")
        invoice_url = state.get("invoice_page_url", "")

        # Build menu HTML
        menu_html = ""
        if menu:
            items_html = ""
            for m in menu:
                items_html += f"""
                <div class="menu-item">
                    <span class="item-name">{m['item']}</span>
                    <span class="item-price">₹{m['price']}</span>
                </div>"""
            menu_html = f"""
            <section class="menu" id="menu">
                <h2>📋 Our Menu</h2>
                <div class="menu-grid">{items_html}
                </div>
            </section>"""

        # WhatsApp order link
        wa_msg = urllib.parse.quote(f"Hi! I'd like to place an order from {business_name}")
        wa_link = f"https://wa.me/91{phone}?text={wa_msg}" if phone else "#"

        # Build full HTML
        html = _build_website_html(
            business_name=business_name,
            tagline_hindi=tagline_hindi,
            tagline_english=tagline_english,
            logo_url=logo_url,
            primary_color=primary_color,
            secondary_color=secondary_color,
            phone=phone,
            address=address,
            menu_html=menu_html,
            wa_link=wa_link,
            upi_qr_url=upi_qr_url,
            template_name=template_name,
        )

        await push_update(sid, "website", 55, "Website built! Uploading... 🚀")

        # ══════════════════════════════════════
        # PHASE 3: Upload to Supabase Storage (60% → 85%)
        # ══════════════════════════════════════
        await push_update(sid, "website", 65, "Deploying your website... 🌐")

        html_path = f"websites/{sid}/index.html"
        website_url = await upload_to_storage(
            "genesis-assets",
            html_path,
            html.encode("utf-8"),
            content_type="text/html",
        )

        await push_update(sid, "website", 85, "Website deployed! ✅")

        # ══════════════════════════════════════
        # PHASE 4: Complete (85% → 100%)
        # ══════════════════════════════════════
        result_data = {
            "website_url": website_url,
            "template": template_name,
            "has_menu": bool(menu),
            "has_qr": bool(upi_qr_url),
            "whatsapp_order_link": wa_link,
        }

        await push_update(
            sid, "website", 100,
            "Website is LIVE! 🎉",
            status="completed",
            result_data=result_data,
        )

        return {
            "website_url": website_url,
            "completed_agents": ["website"],
        }

    except Exception as e:
        error_msg = f"Website Agent error: {str(e)}"
        print(f"[WebsiteAgent] ERROR: {traceback.format_exc()}")
        await push_update(sid, "website", 0, error_msg, status="error")

        return {
            "website_url": None,
            "completed_agents": ["website"],
        }


def _select_template(business_type: str) -> str:
    """Select best template based on business type."""
    food_types = {"tiffin_delivery", "home_baker", "cloud_kitchen", "restaurant", "cafe"}
    service_types = {"salon", "tailor", "laundry", "plumber", "electrician"}
    education_types = {"tutor", "coaching", "teacher", "school"}
    retail_types = {"kirana", "shop", "store", "retail"}

    if business_type in food_types:
        return "food"
    elif business_type in service_types:
        return "services"
    elif business_type in education_types:
        return "education"
    elif business_type in retail_types:
        return "retail"
    else:
        return "professional"


def _build_website_html(
    business_name: str,
    tagline_hindi: str,
    tagline_english: str,
    logo_url: str,
    primary_color: str,
    secondary_color: str,
    phone: str,
    address: str,
    menu_html: str,
    wa_link: str,
    upi_qr_url: str,
    template_name: str,
) -> str:
    """Generate a complete, mobile-first HTML website."""

    # Determine accent based on template
    gradients = {
        "food": f"linear-gradient(135deg, {primary_color}, #FFD700)",
        "services": f"linear-gradient(135deg, {primary_color}, #8B5CF6)",
        "education": f"linear-gradient(135deg, {primary_color}, #3B82F6)",
        "retail": f"linear-gradient(135deg, {primary_color}, #10B981)",
        "professional": f"linear-gradient(135deg, {primary_color}, #6366F1)",
    }
    gradient = gradients.get(template_name, gradients["professional"])

    logo_html = f'<img src="{logo_url}" alt="{business_name}" class="logo-img">' if logo_url and logo_url.startswith("http") else f'<div class="logo-text">{business_name[0]}</div>'

    contact_html = ""
    if phone:
        contact_html += f'<a href="tel:+91{phone}" class="contact-btn">📞 Call Now</a>'
    if address:
        maps_q = urllib.parse.quote(address)
        contact_html += f'<a href="https://maps.google.com/?q={maps_q}" class="contact-btn" target="_blank">📍 Get Directions</a>'

    qr_section = ""
    if upi_qr_url:
        qr_section = f"""
        <section class="payment" id="payment">
            <h2>💳 Pay Easily</h2>
            <p>Scan the QR code to pay via UPI</p>
            <img src="{upi_qr_url}" alt="UPI QR Code" class="qr-img">
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} — Order Online</title>
    <meta name="description" content="{tagline_english or business_name}">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: {secondary_color};
            color: #1a1a2e;
            line-height: 1.6;
        }}
        .hero {{
            background: {gradient};
            color: white;
            padding: 60px 24px 48px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .hero::after {{
            content: '';
            position: absolute;
            bottom: -30px;
            left: 0;
            right: 0;
            height: 60px;
            background: {secondary_color};
            border-radius: 50% 50% 0 0;
        }}
        .logo-img {{
            width: 80px;
            height: 80px;
            border-radius: 20px;
            object-fit: cover;
            margin-bottom: 16px;
            border: 3px solid rgba(255,255,255,0.3);
        }}
        .logo-text {{
            width: 80px;
            height: 80px;
            border-radius: 20px;
            background: rgba(255,255,255,0.2);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 16px;
        }}
        h1 {{
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 8px;
        }}
        .tagline {{
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 4px;
        }}
        .tagline-en {{
            font-size: 0.85rem;
            opacity: 0.7;
        }}
        .cta-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 20px;
            padding: 14px 32px;
            background: white;
            color: {primary_color};
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 700;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            transition: transform 0.2s;
        }}
        .cta-btn:hover {{ transform: scale(1.05); }}
        section {{
            padding: 40px 24px;
            max-width: 600px;
            margin: 0 auto;
        }}
        h2 {{
            font-size: 1.4rem;
            font-weight: 800;
            margin-bottom: 20px;
            color: {primary_color};
        }}
        .menu-grid {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .menu-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 18px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .item-name {{
            font-weight: 600;
            font-size: 0.95rem;
        }}
        .item-price {{
            font-weight: 800;
            color: {primary_color};
            font-size: 1.05rem;
        }}
        .contact-section {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .contact-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 14px;
            background: white;
            border-radius: 12px;
            text-decoration: none;
            color: #1a1a2e;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: transform 0.2s;
        }}
        .contact-btn:hover {{ transform: scale(1.02); }}
        .qr-img {{
            width: 200px;
            height: 200px;
            margin: 16px auto;
            display: block;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .payment {{ text-align: center; }}
        footer {{
            text-align: center;
            padding: 24px;
            font-size: 0.8rem;
            color: #888;
            border-top: 1px solid #eee;
        }}
        @media (max-width: 400px) {{
            h1 {{ font-size: 1.4rem; }}
            .hero {{ padding: 40px 16px 36px; }}
        }}
    </style>
</head>
<body>
    <header class="hero">
        {logo_html}
        <h1>{business_name}</h1>
        <p class="tagline">{tagline_hindi}</p>
        <p class="tagline-en">{tagline_english}</p>
        <a href="{wa_link}" class="cta-btn" target="_blank">
            📱 Order on WhatsApp
        </a>
    </header>

    {menu_html}

    <section class="contact" id="contact">
        <h2>📞 Contact Us</h2>
        <div class="contact-section">
            {contact_html}
            <a href="{wa_link}" class="contact-btn" target="_blank" style="background:{primary_color};color:white;">
                💬 WhatsApp Order
            </a>
        </div>
    </section>

    {qr_section}

    <footer>
        <p>Made with ❤️ by GENESIS AI • {business_name}</p>
    </footer>
</body>
</html>"""
