"""Website Agent — Builds and deploys a premium branded website for the business.

What it produces:
- Selects the best template from 5 DISTINCT premium designs based on business type
- Each template has unique layout, animations, sections, and visual identity
- Injects brand data (logo, colors, tagline, menu)
- Deploys to Supabase Storage (accessible via public URL)

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
        await push_update(sid, "website", 30, "Building your premium website... 🔨")

        # Collect all brand data
        context = {
            "business_name": state["business_name"],
            "logo_url": state.get("logo_url", ""),
            "primary_color": state.get("primary_color", "#FF6B35"),
            "secondary_color": state.get("secondary_color", "#FFF8F0"),
            "tagline_hindi": state.get("tagline_hindi", ""),
            "tagline_english": state.get("tagline_english", ""),
            "phone": state.get("phone", ""),
            "address": state.get("address", ""),
            "upi_id": state.get("upi_id", ""),
            "menu": state.get("menu", []),
            "upi_qr_url": state.get("upi_qr_url", ""),
            "invoice_page_url": state.get("invoice_page_url", ""),
        }

        # WhatsApp order link
        wa_msg = urllib.parse.quote(f"Hi! I'd like to place an order from {context['business_name']}")
        context["wa_link"] = f"https://wa.me/91{context['phone']}?text={wa_msg}" if context["phone"] else "#"

        # Build full HTML using the selected template
        template_builders = {
            "food": _build_food_template,
            "services": _build_services_template,
            "education": _build_education_template,
            "retail": _build_retail_template,
            "professional": _build_professional_template,
        }

        builder = template_builders.get(template_name, _build_professional_template)
        html = builder(context)

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
            "has_menu": bool(context["menu"]),
            "has_qr": bool(context["upi_qr_url"]),
            "whatsapp_order_link": context["wa_link"],
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
    food_types = {"tiffin_delivery", "home_baker", "cloud_kitchen", "restaurant", "cafe", "bakery"}
    service_types = {"salon", "tailor", "laundry", "plumber", "electrician", "mechanic"}
    education_types = {"tutor", "coaching", "teacher", "school"}
    retail_types = {"kirana", "shop", "store", "retail", "grocery", "clothing"}

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


# ═══════════════════════════════════════════════════════════
# SHARED HELPERS
# ═══════════════════════════════════════════════════════════

def _logo_html(ctx: dict) -> str:
    if ctx["logo_url"] and ctx["logo_url"].startswith("http"):
        return f'<img src="{ctx["logo_url"]}" alt="{ctx["business_name"]}" class="logo-img">'
    return f'<div class="logo-text">{ctx["business_name"][0]}</div>'


def _menu_items_html(menu: list, style: str = "card") -> str:
    if not menu:
        return ""
    items = ""
    for m in menu:
        if style == "card":
            items += f'''
            <div class="menu-card">
                <div class="menu-card-inner">
                    <span class="item-name">{m['item']}</span>
                    <span class="item-price">₹{m['price']}</span>
                </div>
            </div>'''
        elif style == "row":
            items += f'''
            <div class="menu-row">
                <span class="item-name">{m['item']}</span>
                <span class="item-dots"></span>
                <span class="item-price">₹{m['price']}</span>
            </div>'''
        elif style == "grid":
            items += f'''
            <div class="menu-tile">
                <div class="tile-price">₹{m['price']}</div>
                <div class="tile-name">{m['item']}</div>
            </div>'''
    return items


def _contact_buttons(ctx: dict) -> str:
    html = ""
    if ctx["phone"]:
        html += f'<a href="tel:+91{ctx["phone"]}" class="contact-btn phone-btn">📞 Call Now</a>'
    if ctx["address"]:
        maps_q = urllib.parse.quote(ctx["address"])
        html += f'<a href="https://maps.google.com/?q={maps_q}" class="contact-btn map-btn" target="_blank">📍 Directions</a>'
    if ctx["wa_link"] != "#":
        html += f'<a href="{ctx["wa_link"]}" class="contact-btn wa-btn" target="_blank">💬 WhatsApp</a>'
    return html


def _qr_section(ctx: dict) -> str:
    if not ctx["upi_qr_url"]:
        return ""
    return f'''
    <section class="payment-section" id="pay">
        <h2>💳 Quick Pay</h2>
        <p>Scan to pay via UPI — Google Pay, PhonePe, Paytm</p>
        <img src="{ctx['upi_qr_url']}" alt="UPI QR Code" class="qr-img">
    </section>'''


def _footer(ctx: dict) -> str:
    return f'''
    <footer>
        <p>Made with ❤️ by <strong>GENESIS AI</strong></p>
        <p class="footer-sub">{ctx["business_name"]} • {ctx.get("address", "")}</p>
    </footer>'''


# ═══════════════════════════════════════════════════════════
# TEMPLATE 1: FOOD — Warm, appetizing, menu-first design
# Unique: Floating food emojis, warm gradient hero, card-based menu,
#         sticky WhatsApp order button, testimonial-style layout
# ═══════════════════════════════════════════════════════════

def _build_food_template(ctx: dict) -> str:
    pc = ctx["primary_color"]
    sc = ctx["secondary_color"]
    menu_cards = _menu_items_html(ctx["menu"], "card")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ctx["business_name"]} — Fresh Food, Delivered with Love</title>
    <meta name="description" content="{ctx['tagline_english'] or ctx['business_name']} — Order fresh homemade food online">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Nunito', sans-serif; background: #FFFAF5; color: #2D1B00; overflow-x: hidden; }}

        /* ── Floating food emojis ── */
        .float-emoji {{ position: fixed; font-size: 2rem; opacity: 0.08; z-index: 0; animation: floatUp 15s linear infinite; pointer-events: none; }}
        .float-emoji:nth-child(1) {{ left: 5%; animation-delay: 0s; }}
        .float-emoji:nth-child(2) {{ left: 25%; animation-delay: 3s; font-size: 1.5rem; }}
        .float-emoji:nth-child(3) {{ left: 55%; animation-delay: 6s; }}
        .float-emoji:nth-child(4) {{ left: 80%; animation-delay: 9s; font-size: 2.5rem; }}
        .float-emoji:nth-child(5) {{ left: 40%; animation-delay: 12s; }}
        @keyframes floatUp {{ 0% {{ transform: translateY(100vh) rotate(0deg); opacity: 0.08; }} 100% {{ transform: translateY(-100px) rotate(360deg); opacity: 0; }} }}

        /* ── Hero ── */
        .hero {{
            background: linear-gradient(135deg, {pc}, {pc}dd, #FF8C42);
            color: white;
            padding: 80px 24px 70px;
            text-align: center;
            position: relative;
            clip-path: ellipse(120% 100% at 50% 0%);
        }}
        .logo-img {{ width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 4px solid rgba(255,255,255,0.4); margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); }}
        .logo-text {{ width: 90px; height: 90px; border-radius: 50%; background: rgba(255,255,255,0.2); display: inline-flex; align-items: center; justify-content: center; font-size: 2.2rem; font-weight: 800; margin-bottom: 20px; backdrop-filter: blur(10px); }}
        h1 {{ font-size: 2rem; font-weight: 800; margin-bottom: 10px; text-shadow: 0 2px 10px rgba(0,0,0,0.15); }}
        .tagline {{ font-size: 1.15rem; opacity: 0.95; font-weight: 600; }}
        .tagline-en {{ font-size: 0.85rem; opacity: 0.7; margin-top: 4px; }}
        .hero-cta {{
            display: inline-flex; align-items: center; gap: 10px;
            margin-top: 28px; padding: 16px 36px;
            background: white; color: {pc};
            border: none; border-radius: 60px;
            font-size: 1.05rem; font-weight: 700;
            text-decoration: none;
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }}
        .hero-cta:hover {{ transform: translateY(-3px) scale(1.03); box-shadow: 0 12px 40px rgba(0,0,0,0.25); }}

        /* ── Sections ── */
        .section {{ padding: 48px 20px; max-width: 640px; margin: 0 auto; position: relative; z-index: 1; }}
        .section h2 {{ font-size: 1.5rem; font-weight: 800; color: {pc}; margin-bottom: 24px; text-align: center; }}

        /* ── Menu Cards ── */
        .menu-grid {{ display: grid; grid-template-columns: 1fr; gap: 14px; }}
        .menu-card {{
            background: white; border-radius: 16px; overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            transition: all 0.3s ease;
            border: 1px solid rgba(0,0,0,0.04);
        }}
        .menu-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0,0,0,0.1); }}
        .menu-card-inner {{ display: flex; justify-content: space-between; align-items: center; padding: 18px 22px; }}
        .item-name {{ font-weight: 700; font-size: 1rem; color: #2D1B00; }}
        .item-price {{
            font-weight: 800; font-size: 1.15rem; color: {pc};
            background: {pc}15; padding: 6px 16px; border-radius: 30px;
        }}

        /* ── Why Us ── */
        .features {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; text-align: center; }}
        .feature {{ padding: 24px 12px; background: white; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }}
        .feature-icon {{ font-size: 2rem; margin-bottom: 10px; }}
        .feature-title {{ font-weight: 700; font-size: 0.85rem; color: #2D1B00; }}

        /* ── Contact ── */
        .contact-grid {{ display: grid; gap: 12px; }}
        .contact-btn {{
            display: flex; align-items: center; justify-content: center; gap: 10px;
            padding: 16px; border-radius: 14px; text-decoration: none;
            font-weight: 700; font-size: 0.95rem; transition: all 0.3s ease;
        }}
        .contact-btn:hover {{ transform: translateY(-2px); }}
        .phone-btn {{ background: #E8F5E9; color: #2E7D32; }}
        .map-btn {{ background: #E3F2FD; color: #1565C0; }}
        .wa-btn {{ background: #25D366; color: white; box-shadow: 0 4px 15px rgba(37,211,102,0.3); }}

        /* ── Payment ── */
        .payment-section {{ text-align: center; }}
        .payment-section p {{ color: #666; margin-bottom: 20px; }}
        .qr-img {{ width: 200px; height: 200px; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); margin: 0 auto; display: block; }}

        /* ── Footer ── */
        footer {{ text-align: center; padding: 32px 20px; color: #999; font-size: 0.8rem; border-top: 1px solid #f0e8e0; }}
        .footer-sub {{ margin-top: 4px; font-size: 0.75rem; }}

        /* ── Sticky Order Bar ── */
        .sticky-bar {{
            position: fixed; bottom: 0; left: 0; right: 0;
            background: {pc}; color: white;
            padding: 14px 20px; text-align: center;
            font-weight: 700; font-size: 1rem;
            z-index: 100; box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
        }}
        .sticky-bar a {{ color: white; text-decoration: none; }}

        /* ── Animate in ── */
        .fade-in {{ opacity: 0; transform: translateY(30px); animation: fadeIn 0.6s ease forwards; }}
        .fade-in:nth-child(2) {{ animation-delay: 0.15s; }}
        .fade-in:nth-child(3) {{ animation-delay: 0.3s; }}
        @keyframes fadeIn {{ to {{ opacity: 1; transform: translateY(0); }} }}

        @media (max-width: 480px) {{
            .hero {{ padding: 60px 16px 50px; }}
            h1 {{ font-size: 1.6rem; }}
            .features {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="float-emoji">🍛</div><div class="float-emoji">🥘</div><div class="float-emoji">🍲</div><div class="float-emoji">🌶️</div><div class="float-emoji">🍚</div>

    <header class="hero">
        {_logo_html(ctx)}
        <h1>{ctx["business_name"]}</h1>
        <p class="tagline">{ctx["tagline_hindi"]}</p>
        <p class="tagline-en">{ctx["tagline_english"]}</p>
        <a href="{ctx['wa_link']}" class="hero-cta" target="_blank">📱 Order on WhatsApp</a>
    </header>

    {"" if not ctx["menu"] else f"""
    <section class="section fade-in">
        <h2>🍽️ Our Menu</h2>
        <div class="menu-grid">{menu_cards}</div>
    </section>"""}

    <section class="section fade-in">
        <h2>✨ Why Choose Us</h2>
        <div class="features">
            <div class="feature"><div class="feature-icon">🏠</div><div class="feature-title">Ghar Jaisa Khana</div></div>
            <div class="feature"><div class="feature-icon">🚀</div><div class="feature-title">Fast Delivery</div></div>
            <div class="feature"><div class="feature-icon">💰</div><div class="feature-title">Best Prices</div></div>
        </div>
    </section>

    <section class="section fade-in">
        <h2>📞 Contact Us</h2>
        <div class="contact-grid">{_contact_buttons(ctx)}</div>
    </section>

    {_qr_section(ctx)}
    {_footer(ctx)}

    <div class="sticky-bar"><a href="{ctx['wa_link']}" target="_blank">📱 Order Now — WhatsApp</a></div>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════
# TEMPLATE 2: SERVICES — Clean, trust-focused, booking-oriented
# Unique: Split hero, service cards with icons, trust badges,
#         booking CTA, testimonial section, no menu — service list instead
# ═══════════════════════════════════════════════════════════

def _build_services_template(ctx: dict) -> str:
    pc = ctx["primary_color"]
    sc = ctx["secondary_color"]

    # Services use menu items as service list
    services_html = ""
    if ctx["menu"]:
        for i, m in enumerate(ctx["menu"]):
            icons = ["✂️", "💇", "🔧", "⚡", "🧵", "🪡", "🛠️", "💅"]
            icon = icons[i % len(icons)]
            services_html += f'''
            <div class="service-card">
                <div class="service-icon">{icon}</div>
                <div class="service-info">
                    <h3>{m['item']}</h3>
                    <div class="service-price">Starting at ₹{m['price']}</div>
                </div>
                <a href="{ctx['wa_link']}" class="book-btn" target="_blank">Book</a>
            </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ctx["business_name"]} — Professional Services</title>
    <meta name="description" content="{ctx['tagline_english'] or ctx['business_name']}">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Outfit', sans-serif; background: #FAFBFC; color: #1a1a2e; overflow-x: hidden; }}

        /* ── Navbar ── */
        .navbar {{
            position: fixed; top: 0; width: 100%; z-index: 100;
            display: flex; justify-content: space-between; align-items: center;
            padding: 16px 24px; background: rgba(255,255,255,0.85);
            backdrop-filter: blur(20px); border-bottom: 1px solid rgba(0,0,0,0.05);
        }}
        .nav-brand {{ font-weight: 800; font-size: 1.1rem; color: {pc}; }}
        .nav-cta {{ padding: 10px 24px; background: {pc}; color: white; border-radius: 50px; text-decoration: none; font-weight: 600; font-size: 0.85rem; transition: all 0.3s; }}
        .nav-cta:hover {{ transform: scale(1.05); box-shadow: 0 4px 15px {pc}40; }}

        /* ── Hero Split ── */
        .hero {{
            margin-top: 60px; padding: 80px 24px 60px;
            background: linear-gradient(160deg, {pc}08 0%, {pc}15 50%, transparent 100%);
            text-align: center;
        }}
        .hero-badge {{ display: inline-block; padding: 8px 20px; background: {pc}15; color: {pc}; border-radius: 50px; font-weight: 600; font-size: 0.8rem; margin-bottom: 20px; }}
        .logo-img {{ width: 100px; height: 100px; border-radius: 24px; object-fit: cover; margin-bottom: 24px; box-shadow: 0 12px 40px rgba(0,0,0,0.12); }}
        .logo-text {{ width: 100px; height: 100px; border-radius: 24px; background: {pc}; color: white; display: inline-flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 24px; }}
        h1 {{ font-size: 2.2rem; font-weight: 800; line-height: 1.2; margin-bottom: 12px; }}
        h1 span {{ color: {pc}; }}
        .hero-sub {{ font-size: 1.05rem; color: #666; max-width: 480px; margin: 0 auto 8px; line-height: 1.6; }}
        .tagline {{ font-size: 1.1rem; color: {pc}; font-weight: 600; margin-bottom: 28px; }}
        .hero-actions {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }}
        .btn-primary {{ padding: 16px 36px; background: {pc}; color: white; border-radius: 14px; text-decoration: none; font-weight: 700; font-size: 1rem; transition: all 0.3s; box-shadow: 0 6px 20px {pc}30; }}
        .btn-primary:hover {{ transform: translateY(-3px); box-shadow: 0 10px 30px {pc}40; }}
        .btn-outline {{ padding: 16px 36px; background: transparent; color: {pc}; border: 2px solid {pc}; border-radius: 14px; text-decoration: none; font-weight: 700; font-size: 1rem; transition: all 0.3s; }}
        .btn-outline:hover {{ background: {pc}08; }}

        /* ── Trust Badges ── */
        .trust {{ display: flex; justify-content: center; gap: 32px; padding: 40px 20px; flex-wrap: wrap; }}
        .trust-item {{ text-align: center; }}
        .trust-num {{ font-size: 1.8rem; font-weight: 800; color: {pc}; }}
        .trust-label {{ font-size: 0.8rem; color: #888; font-weight: 500; }}

        /* ── Services ── */
        .section {{ padding: 56px 20px; max-width: 640px; margin: 0 auto; }}
        .section-title {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 3px; color: {pc}; font-weight: 700; margin-bottom: 8px; text-align: center; }}
        .section h2 {{ font-size: 1.6rem; font-weight: 800; text-align: center; margin-bottom: 32px; }}
        .service-card {{
            display: flex; align-items: center; gap: 16px;
            padding: 20px; background: white; border-radius: 16px;
            margin-bottom: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.04);
            border: 1px solid rgba(0,0,0,0.04);
            transition: all 0.3s ease;
        }}
        .service-card:hover {{ transform: translateX(6px); box-shadow: 0 6px 20px rgba(0,0,0,0.08); border-color: {pc}30; }}
        .service-icon {{ font-size: 1.8rem; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; background: {pc}10; border-radius: 14px; flex-shrink: 0; }}
        .service-info {{ flex: 1; }}
        .service-info h3 {{ font-size: 1rem; font-weight: 700; }}
        .service-price {{ font-size: 0.85rem; color: #888; margin-top: 2px; }}
        .book-btn {{ padding: 10px 20px; background: {pc}; color: white; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 0.8rem; flex-shrink: 0; transition: all 0.3s; }}
        .book-btn:hover {{ transform: scale(1.05); }}

        /* ── Contact ── */
        .contact-grid {{ display: grid; gap: 12px; }}
        .contact-btn {{ display: flex; align-items: center; justify-content: center; gap: 10px; padding: 16px; border-radius: 14px; text-decoration: none; font-weight: 600; font-size: 0.95rem; transition: all 0.3s; }}
        .contact-btn:hover {{ transform: translateY(-2px); }}
        .phone-btn {{ background: #E8F5E9; color: #2E7D32; }}
        .map-btn {{ background: #E3F2FD; color: #1565C0; }}
        .wa-btn {{ background: #25D366; color: white; box-shadow: 0 4px 15px rgba(37,211,102,0.3); }}

        /* ── Payment ── */
        .payment-section {{ text-align: center; }}
        .payment-section p {{ color: #666; margin-bottom: 20px; }}
        .qr-img {{ width: 200px; height: 200px; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); margin: 0 auto; display: block; }}

        /* ── Footer ── */
        footer {{ text-align: center; padding: 32px 20px; color: #999; font-size: 0.8rem; border-top: 1px solid #eee; }}
        .footer-sub {{ margin-top: 4px; font-size: 0.75rem; }}

        @media (max-width: 480px) {{
            .hero {{ padding: 70px 16px 40px; }}
            h1 {{ font-size: 1.7rem; }}
            .trust {{ gap: 20px; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">{ctx["business_name"]}</div>
        <a href="{ctx['wa_link']}" class="nav-cta" target="_blank">Book Now</a>
    </nav>

    <header class="hero">
        <div class="hero-badge">⭐ Trusted Local Service</div>
        {_logo_html(ctx)}
        <h1>{ctx["business_name"]}</h1>
        <p class="tagline">{ctx["tagline_hindi"]}</p>
        <p class="hero-sub">{ctx["tagline_english"]}</p>
        <div class="hero-actions">
            <a href="{ctx['wa_link']}" class="btn-primary" target="_blank">📱 Book on WhatsApp</a>
            <a href="tel:+91{ctx['phone']}" class="btn-outline">📞 Call Now</a>
        </div>
    </header>

    <div class="trust">
        <div class="trust-item"><div class="trust-num">500+</div><div class="trust-label">Happy Customers</div></div>
        <div class="trust-item"><div class="trust-num">4.8★</div><div class="trust-label">Rating</div></div>
        <div class="trust-item"><div class="trust-num">5+</div><div class="trust-label">Years Experience</div></div>
    </div>

    {"" if not services_html else f"""
    <section class="section">
        <div class="section-title">What We Offer</div>
        <h2>Our Services</h2>
        {services_html}
    </section>"""}

    <section class="section">
        <div class="section-title">Get in Touch</div>
        <h2>Contact Us</h2>
        <div class="contact-grid">{_contact_buttons(ctx)}</div>
    </section>

    {_qr_section(ctx)}
    {_footer(ctx)}
</body>
</html>'''


# ═══════════════════════════════════════════════════════════
# TEMPLATE 3: EDUCATION — Knowledge-focused, clean, academic feel
# Unique: Book-style layout, course cards, testimonial quotes,
#         subject tags, enrollment CTA, warm scholarly colors
# ═══════════════════════════════════════════════════════════

def _build_education_template(ctx: dict) -> str:
    pc = ctx["primary_color"]

    courses_html = ""
    if ctx["menu"]:
        for i, m in enumerate(ctx["menu"]):
            icons = ["📚", "📐", "🧪", "🎨", "💻", "🌍", "🧮", "✏️"]
            icon = icons[i % len(icons)]
            courses_html += f'''
            <div class="course-card">
                <div class="course-header">
                    <span class="course-icon">{icon}</span>
                    <span class="course-fee">₹{m['price']}/mo</span>
                </div>
                <h3>{m['item']}</h3>
                <a href="{ctx['wa_link']}" class="enroll-btn" target="_blank">Enroll Now →</a>
            </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ctx["business_name"]} — Learn & Grow</title>
    <meta name="description" content="{ctx['tagline_english'] or ctx['business_name']}">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'DM Sans', sans-serif; background: #F8F6F3; color: #1a1a2e; overflow-x: hidden; }}

        /* ── Hero ── */
        .hero {{
            background: linear-gradient(180deg, #1a1a2e 0%, {pc}dd 100%);
            color: white; padding: 80px 24px 70px; text-align: center;
            position: relative;
        }}
        .hero::after {{ content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 40px; background: #F8F6F3; border-radius: 40px 40px 0 0; }}
        .logo-img {{ width: 90px; height: 90px; border-radius: 20px; object-fit: cover; border: 3px solid rgba(255,255,255,0.3); margin-bottom: 20px; }}
        .logo-text {{ width: 90px; height: 90px; border-radius: 20px; background: rgba(255,255,255,0.15); display: inline-flex; align-items: center; justify-content: center; font-size: 2.2rem; font-weight: 700; margin-bottom: 20px; font-family: 'DM Serif Display', serif; }}
        h1 {{ font-family: 'DM Serif Display', serif; font-size: 2.2rem; margin-bottom: 12px; }}
        .tagline {{ font-size: 1.1rem; opacity: 0.9; font-weight: 500; }}
        .tagline-en {{ font-size: 0.85rem; opacity: 0.6; margin-top: 4px; }}
        .hero-cta {{ display: inline-flex; align-items: center; gap: 10px; margin-top: 28px; padding: 16px 36px; background: white; color: {pc}; border-radius: 14px; font-weight: 700; text-decoration: none; transition: all 0.3s; box-shadow: 0 8px 30px rgba(0,0,0,0.2); }}
        .hero-cta:hover {{ transform: translateY(-3px); }}

        /* ── Stats ── */
        .stats {{ display: flex; justify-content: center; gap: 36px; padding: 40px 20px; flex-wrap: wrap; }}
        .stat {{ text-align: center; }}
        .stat-num {{ font-family: 'DM Serif Display', serif; font-size: 2rem; color: {pc}; }}
        .stat-label {{ font-size: 0.8rem; color: #888; }}

        /* ── Courses ── */
        .section {{ padding: 48px 20px; max-width: 680px; margin: 0 auto; }}
        .section h2 {{ font-family: 'DM Serif Display', serif; font-size: 1.6rem; text-align: center; margin-bottom: 32px; }}
        .courses-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }}
        .course-card {{
            background: white; border-radius: 20px; padding: 24px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.05);
            border: 1px solid rgba(0,0,0,0.04);
            transition: all 0.3s;
        }}
        .course-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0,0,0,0.1); }}
        .course-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        .course-icon {{ font-size: 2rem; }}
        .course-fee {{ background: {pc}15; color: {pc}; padding: 6px 14px; border-radius: 30px; font-weight: 700; font-size: 0.85rem; }}
        .course-card h3 {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 14px; }}
        .enroll-btn {{ display: block; text-align: center; padding: 12px; background: {pc}; color: white; border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: all 0.3s; }}
        .enroll-btn:hover {{ opacity: 0.9; }}

        /* ── Contact ── */
        .contact-grid {{ display: grid; gap: 12px; }}
        .contact-btn {{ display: flex; align-items: center; justify-content: center; gap: 10px; padding: 16px; border-radius: 14px; text-decoration: none; font-weight: 600; transition: all 0.3s; }}
        .phone-btn {{ background: #E8F5E9; color: #2E7D32; }}
        .map-btn {{ background: #E3F2FD; color: #1565C0; }}
        .wa-btn {{ background: #25D366; color: white; }}

        .payment-section {{ text-align: center; }}
        .payment-section p {{ color: #666; margin-bottom: 20px; }}
        .qr-img {{ width: 200px; height: 200px; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); margin: 0 auto; display: block; }}
        footer {{ text-align: center; padding: 32px 20px; color: #999; font-size: 0.8rem; border-top: 1px solid #e8e4de; }}
        .footer-sub {{ margin-top: 4px; font-size: 0.75rem; }}

        @media (max-width: 480px) {{ h1 {{ font-size: 1.7rem; }} .courses-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <header class="hero">
        {_logo_html(ctx)}
        <h1>{ctx["business_name"]}</h1>
        <p class="tagline">{ctx["tagline_hindi"]}</p>
        <p class="tagline-en">{ctx["tagline_english"]}</p>
        <a href="{ctx['wa_link']}" class="hero-cta" target="_blank">📝 Enroll Now</a>
    </header>

    <div class="stats">
        <div class="stat"><div class="stat-num">100+</div><div class="stat-label">Students</div></div>
        <div class="stat"><div class="stat-num">95%</div><div class="stat-label">Results</div></div>
        <div class="stat"><div class="stat-num">5+</div><div class="stat-label">Years</div></div>
    </div>

    {"" if not courses_html else f"""
    <section class="section">
        <h2>📚 Courses & Fees</h2>
        <div class="courses-grid">{courses_html}</div>
    </section>"""}

    <section class="section">
        <h2>📞 Contact Us</h2>
        <div class="contact-grid">{_contact_buttons(ctx)}</div>
    </section>

    {_qr_section(ctx)}
    {_footer(ctx)}
</body>
</html>'''


# ═══════════════════════════════════════════════════════════
# TEMPLATE 4: RETAIL — Product showcase, grid layout, shopping feel
# Unique: Product grid tiles, category tags, price badges,
#         Instagram-style layout, shopping bag icon, deals banner
# ═══════════════════════════════════════════════════════════

def _build_retail_template(ctx: dict) -> str:
    pc = ctx["primary_color"]

    products_html = _menu_items_html(ctx["menu"], "grid")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ctx["business_name"]} — Shop Now</title>
    <meta name="description" content="{ctx['tagline_english'] or ctx['business_name']}">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', sans-serif; background: #FFFFFF; color: #111; overflow-x: hidden; }}

        /* ── Announcement Bar ── */
        .announce {{ background: {pc}; color: white; text-align: center; padding: 10px; font-size: 0.8rem; font-weight: 600; letter-spacing: 1px; }}

        /* ── Header ── */
        .header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid #f0f0f0; position: sticky; top: 0; background: white; z-index: 100; }}
        .brand {{ font-size: 1.2rem; font-weight: 800; color: {pc}; }}
        .header-actions {{ display: flex; gap: 12px; }}
        .header-btn {{ padding: 10px 20px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 0.85rem; }}
        .header-btn.primary {{ background: {pc}; color: white; }}

        /* ── Hero Banner ── */
        .hero-banner {{
            background: linear-gradient(135deg, #111 0%, {pc}99 100%);
            color: white; padding: 64px 24px; text-align: center;
        }}
        .logo-img {{ width: 80px; height: 80px; border-radius: 16px; object-fit: cover; border: 3px solid rgba(255,255,255,0.2); margin-bottom: 20px; }}
        .logo-text {{ width: 80px; height: 80px; border-radius: 16px; background: rgba(255,255,255,0.1); display: inline-flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 800; margin-bottom: 20px; }}
        .hero-banner h1 {{ font-size: 2rem; font-weight: 800; margin-bottom: 8px; }}
        .tagline {{ font-size: 1.1rem; opacity: 0.9; }}
        .tagline-en {{ font-size: 0.85rem; opacity: 0.6; margin-top: 4px; }}
        .shop-cta {{ display: inline-flex; align-items: center; gap: 8px; margin-top: 24px; padding: 16px 40px; background: white; color: #111; border-radius: 12px; font-weight: 700; text-decoration: none; transition: all 0.3s; }}
        .shop-cta:hover {{ transform: scale(1.05); box-shadow: 0 8px 30px rgba(255,255,255,0.2); }}

        /* ── Products Grid ── */
        .section {{ padding: 48px 20px; max-width: 680px; margin: 0 auto; }}
        .section h2 {{ font-size: 1.4rem; font-weight: 800; margin-bottom: 24px; }}
        .products-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }}
        .menu-tile {{
            background: #F8F8F8; border-radius: 16px; padding: 24px 16px;
            text-align: center; transition: all 0.3s;
            border: 2px solid transparent;
        }}
        .menu-tile:hover {{ border-color: {pc}; transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }}
        .tile-price {{ font-size: 1.4rem; font-weight: 800; color: {pc}; margin-bottom: 8px; }}
        .tile-name {{ font-size: 0.9rem; font-weight: 600; color: #333; }}

        /* ── Contact ── */
        .contact-grid {{ display: grid; gap: 12px; }}
        .contact-btn {{ display: flex; align-items: center; justify-content: center; gap: 10px; padding: 16px; border-radius: 14px; text-decoration: none; font-weight: 600; transition: all 0.3s; }}
        .phone-btn {{ background: #F0F0F0; color: #333; }}
        .map-btn {{ background: #F0F0F0; color: #333; }}
        .wa-btn {{ background: #25D366; color: white; }}

        .payment-section {{ text-align: center; }}
        .payment-section p {{ color: #666; margin-bottom: 20px; }}
        .qr-img {{ width: 200px; height: 200px; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); margin: 0 auto; display: block; }}
        footer {{ text-align: center; padding: 32px 20px; color: #999; font-size: 0.8rem; border-top: 1px solid #eee; }}
        .footer-sub {{ margin-top: 4px; font-size: 0.75rem; }}

        @media (max-width: 400px) {{ .products-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="announce">🛍️ FREE DELIVERY ON FIRST ORDER • ORDER VIA WHATSAPP</div>

    <header class="header">
        <div class="brand">{ctx["business_name"]}</div>
        <div class="header-actions">
            <a href="{ctx['wa_link']}" class="header-btn primary" target="_blank">🛒 Order</a>
        </div>
    </header>

    <section class="hero-banner">
        {_logo_html(ctx)}
        <h1>{ctx["business_name"]}</h1>
        <p class="tagline">{ctx["tagline_hindi"]}</p>
        <p class="tagline-en">{ctx["tagline_english"]}</p>
        <a href="{ctx['wa_link']}" class="shop-cta" target="_blank">🛍️ Shop Now</a>
    </section>

    {"" if not ctx["menu"] else f"""
    <section class="section">
        <h2>🏷️ Our Products</h2>
        <div class="products-grid">{products_html}</div>
    </section>"""}

    <section class="section">
        <h2>📞 Contact</h2>
        <div class="contact-grid">{_contact_buttons(ctx)}</div>
    </section>

    {_qr_section(ctx)}
    {_footer(ctx)}
</body>
</html>'''


# ═══════════════════════════════════════════════════════════
# TEMPLATE 5: PROFESSIONAL — Minimal, elegant, portfolio-style
# Unique: Dark mode option, glassmorphism cards, timeline layout,
#         elegant typography, minimal design, premium feel
# ═══════════════════════════════════════════════════════════

def _build_professional_template(ctx: dict) -> str:
    pc = ctx["primary_color"]

    services_html = ""
    if ctx["menu"]:
        for m in ctx["menu"]:
            services_html += f'''
            <div class="glass-card">
                <div class="glass-row">
                    <span class="glass-name">{m['item']}</span>
                    <span class="glass-price">₹{m['price']}</span>
                </div>
            </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ctx["business_name"]}</title>
    <meta name="description" content="{ctx['tagline_english'] or ctx['business_name']}">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Space Grotesk', sans-serif; background: #0A0A0F; color: #E8E8ED; overflow-x: hidden; }}

        /* ── Glow effects ── */
        .glow {{ position: fixed; width: 400px; height: 400px; border-radius: 50%; filter: blur(120px); opacity: 0.08; pointer-events: none; z-index: 0; }}
        .glow-1 {{ background: {pc}; top: -100px; right: -100px; }}
        .glow-2 {{ background: #8B5CF6; bottom: -100px; left: -100px; }}

        /* ── Hero ── */
        .hero {{
            min-height: 80vh; display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            text-align: center; padding: 80px 24px;
            position: relative; z-index: 1;
        }}
        .logo-img {{ width: 100px; height: 100px; border-radius: 24px; object-fit: cover; margin-bottom: 28px; border: 2px solid rgba(255,255,255,0.1); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }}
        .logo-text {{ width: 100px; height: 100px; border-radius: 24px; background: linear-gradient(135deg, {pc}, #8B5CF6); display: inline-flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 700; margin-bottom: 28px; }}
        h1 {{ font-size: 2.8rem; font-weight: 700; line-height: 1.1; margin-bottom: 16px; background: linear-gradient(135deg, #fff, {pc}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .tagline {{ font-size: 1.15rem; color: {pc}; font-weight: 500; }}
        .tagline-en {{ font-size: 0.9rem; color: #888; margin-top: 6px; }}
        .hero-actions {{ display: flex; gap: 16px; margin-top: 36px; flex-wrap: wrap; justify-content: center; }}
        .btn-glow {{
            padding: 16px 40px; background: {pc}; color: white;
            border-radius: 14px; text-decoration: none; font-weight: 600;
            font-size: 1rem; transition: all 0.4s;
            box-shadow: 0 0 30px {pc}40;
        }}
        .btn-glow:hover {{ transform: translateY(-3px); box-shadow: 0 0 50px {pc}60; }}
        .btn-glass {{
            padding: 16px 40px; background: rgba(255,255,255,0.06);
            color: #E8E8ED; border: 1px solid rgba(255,255,255,0.1);
            border-radius: 14px; text-decoration: none; font-weight: 600;
            font-size: 1rem; backdrop-filter: blur(10px); transition: all 0.4s;
        }}
        .btn-glass:hover {{ background: rgba(255,255,255,0.12); transform: translateY(-3px); }}

        /* ── Sections ── */
        .section {{ padding: 64px 20px; max-width: 640px; margin: 0 auto; position: relative; z-index: 1; }}
        .section-label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 4px; color: {pc}; font-weight: 600; margin-bottom: 10px; text-align: center; }}
        .section h2 {{ font-size: 1.6rem; font-weight: 700; text-align: center; margin-bottom: 32px; color: #fff; }}

        /* ── Glass Cards ── */
        .glass-card {{
            background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px; padding: 20px 24px; margin-bottom: 12px;
            backdrop-filter: blur(10px); transition: all 0.3s;
        }}
        .glass-card:hover {{ background: rgba(255,255,255,0.08); border-color: {pc}40; transform: translateX(6px); }}
        .glass-row {{ display: flex; justify-content: space-between; align-items: center; }}
        .glass-name {{ font-weight: 600; font-size: 1rem; }}
        .glass-price {{ font-weight: 700; color: {pc}; font-size: 1.1rem; }}

        /* ── Contact ── */
        .contact-grid {{ display: grid; gap: 12px; }}
        .contact-btn {{
            display: flex; align-items: center; justify-content: center; gap: 10px;
            padding: 16px; border-radius: 14px; text-decoration: none;
            font-weight: 600; transition: all 0.3s;
        }}
        .contact-btn:hover {{ transform: translateY(-2px); }}
        .phone-btn {{ background: rgba(46,125,50,0.15); color: #66BB6A; border: 1px solid rgba(46,125,50,0.2); }}
        .map-btn {{ background: rgba(21,101,192,0.15); color: #42A5F5; border: 1px solid rgba(21,101,192,0.2); }}
        .wa-btn {{ background: #25D366; color: white; box-shadow: 0 4px 20px rgba(37,211,102,0.3); }}

        /* ── Payment ── */
        .payment-section {{ text-align: center; }}
        .payment-section p {{ color: #888; margin-bottom: 20px; }}
        .qr-img {{ width: 200px; height: 200px; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.3); margin: 0 auto; display: block; border: 1px solid rgba(255,255,255,0.1); }}

        /* ── Footer ── */
        footer {{ text-align: center; padding: 40px 20px; color: #555; font-size: 0.8rem; border-top: 1px solid rgba(255,255,255,0.06); }}
        footer strong {{ color: {pc}; }}
        .footer-sub {{ margin-top: 4px; font-size: 0.75rem; }}

        @media (max-width: 480px) {{ h1 {{ font-size: 2rem; }} .hero {{ min-height: 60vh; padding: 60px 16px; }} }}
    </style>
</head>
<body>
    <div class="glow glow-1"></div>
    <div class="glow glow-2"></div>

    <header class="hero">
        {_logo_html(ctx)}
        <h1>{ctx["business_name"]}</h1>
        <p class="tagline">{ctx["tagline_hindi"]}</p>
        <p class="tagline-en">{ctx["tagline_english"]}</p>
        <div class="hero-actions">
            <a href="{ctx['wa_link']}" class="btn-glow" target="_blank">💬 Get in Touch</a>
            <a href="tel:+91{ctx['phone']}" class="btn-glass">📞 Call Now</a>
        </div>
    </header>

    {"" if not services_html else f"""
    <section class="section">
        <div class="section-label">What We Offer</div>
        <h2>Services & Pricing</h2>
        {services_html}
    </section>"""}

    <section class="section">
        <div class="section-label">Reach Out</div>
        <h2>Contact Us</h2>
        <div class="contact-grid">{_contact_buttons(ctx)}</div>
    </section>

    {_qr_section(ctx)}
    {_footer(ctx)}
</body>
</html>'''
