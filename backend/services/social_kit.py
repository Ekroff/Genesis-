"""Social Media Kit Generator — Creates platform-specific branded images.

Generates SVG-based social media banners at correct sizes:
- Instagram Post:  1080 x 1080 px
- Instagram Story: 1080 x 1920 px
- Facebook Cover:  1200 x 630 px
- WhatsApp DP:     500 x 500 px

Each image includes the logo, business name, tagline, and brand colors.
SVGs are uploaded to Supabase Storage for download.
"""

import asyncio
from services.supabase_client import upload_to_storage


# ═══════════════════════════════════════════════════════════
# Platform size definitions
# ═══════════════════════════════════════════════════════════

SOCIAL_SIZES = {
    "instagram_post": {"w": 1080, "h": 1080, "label": "Instagram Post"},
    "instagram_story": {"w": 1080, "h": 1920, "label": "Instagram Story"},
    "facebook_cover": {"w": 1200, "h": 630, "label": "Facebook Cover"},
    "whatsapp_dp": {"w": 500, "h": 500, "label": "WhatsApp DP"},
}


async def generate_social_media_kit(
    session_id: str,
    business_name: str,
    tagline_hindi: str,
    tagline_english: str,
    primary_color: str,
    secondary_color: str,
    logo_url: str,
    phone: str = "",
    address: str = "",
) -> dict:
    """Generate all social media images and upload to Supabase Storage.
    
    Returns dict mapping platform name → public URL.
    """
    results = {}

    for platform, size in SOCIAL_SIZES.items():
        svg = _build_social_svg(
            width=size["w"],
            height=size["h"],
            platform=platform,
            business_name=business_name,
            tagline_hindi=tagline_hindi,
            tagline_english=tagline_english,
            primary_color=primary_color,
            secondary_color=secondary_color,
            logo_url=logo_url,
            phone=phone,
            address=address,
        )

        # Upload to Supabase Storage
        path = f"social-kit/{session_id}/{platform}.svg"
        try:
            url = await upload_to_storage(
                "genesis-assets",
                path,
                svg.encode("utf-8"),
                content_type="image/svg+xml",
            )
            results[platform] = url
        except Exception as e:
            print(f"[SocialKit] Failed to upload {platform}: {e}")
            results[platform] = None

    return results


def _build_social_svg(
    width: int,
    height: int,
    platform: str,
    business_name: str,
    tagline_hindi: str,
    tagline_english: str,
    primary_color: str,
    secondary_color: str,
    logo_url: str,
    phone: str,
    address: str,
) -> str:
    """Generate an SVG image for a specific social media platform."""

    # Responsive font sizes based on canvas size
    min_dim = min(width, height)
    name_size = int(min_dim * 0.08)
    tagline_size = int(min_dim * 0.045)
    sub_size = int(min_dim * 0.03)
    logo_size = int(min_dim * 0.18)

    cx = width // 2
    cy = height // 2

    # Logo: embed if URL exists, otherwise use initial letter
    if logo_url and logo_url.startswith("http"):
        logo_el = f'''<image href="{logo_url}" x="{cx - logo_size//2}" y="{cy - int(height*0.28)}" 
            width="{logo_size}" height="{logo_size}" 
            clip-path="inset(0 round 20%)" preserveAspectRatio="xMidYMid slice"/>'''
    else:
        logo_el = f'''<rect x="{cx - logo_size//2}" y="{cy - int(height*0.28)}" 
            width="{logo_size}" height="{logo_size}" rx="{logo_size//5}" 
            fill="rgba(255,255,255,0.15)"/>
        <text x="{cx}" y="{cy - int(height*0.28) + logo_size*0.7}" 
            font-size="{logo_size//2}" fill="white" text-anchor="middle" 
            font-family="Arial,sans-serif" font-weight="700">{business_name[0]}</text>'''

    # Platform-specific decorations
    decorations = _get_decorations(platform, width, height, primary_color)

    # Contact info for story/cover formats
    contact_text = ""
    if platform in ("instagram_story", "facebook_cover") and phone:
        contact_y = cy + int(height * 0.25)
        contact_text = f'''<text x="{cx}" y="{contact_y}" font-size="{sub_size}" 
            fill="rgba(255,255,255,0.7)" text-anchor="middle" font-family="Arial,sans-serif">
            📞 {phone}  •  📍 {address[:30]}
        </text>'''

    # GENESIS watermark
    watermark_y = height - int(height * 0.04)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
    width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="{primary_color}"/>
            <stop offset="50%" stop-color="{primary_color}dd"/>
            <stop offset="100%" stop-color="{_darken_color(primary_color, 30)}"/>
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.2"/>
        </filter>
    </defs>

    <!-- Background -->
    <rect width="{width}" height="{height}" fill="url(#bg)"/>

    <!-- Decorative elements -->
    {decorations}

    <!-- Logo -->
    {logo_el}

    <!-- Business Name -->
    <text x="{cx}" y="{cy + int(height*0.05)}" font-size="{name_size}" 
        fill="white" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" 
        font-weight="800" filter="url(#shadow)">
        {business_name}
    </text>

    <!-- Hindi Tagline -->
    <text x="{cx}" y="{cy + int(height*0.12)}" font-size="{tagline_size}" 
        fill="rgba(255,255,255,0.9)" text-anchor="middle" font-family="Arial,sans-serif" 
        font-weight="600">
        {tagline_hindi}
    </text>

    <!-- English Tagline -->
    <text x="{cx}" y="{cy + int(height*0.17)}" font-size="{int(tagline_size*0.7)}" 
        fill="rgba(255,255,255,0.6)" text-anchor="middle" font-family="Arial,sans-serif">
        {tagline_english}
    </text>

    <!-- Contact info (story/cover only) -->
    {contact_text}

    <!-- GENESIS watermark -->
    <text x="{cx}" y="{watermark_y}" font-size="{int(sub_size*0.8)}" 
        fill="rgba(255,255,255,0.3)" text-anchor="middle" font-family="Arial,sans-serif">
        Powered by GENESIS AI
    </text>
</svg>'''


def _get_decorations(platform: str, w: int, h: int, color: str) -> str:
    """Generate unique decorative SVG elements per platform."""

    if platform == "instagram_post":
        # Geometric circles
        return f'''
        <circle cx="{w*0.85}" cy="{h*0.15}" r="{w*0.12}" fill="rgba(255,255,255,0.06)"/>
        <circle cx="{w*0.1}" cy="{h*0.9}" r="{w*0.18}" fill="rgba(255,255,255,0.04)"/>
        <circle cx="{w*0.92}" cy="{h*0.88}" r="{w*0.08}" fill="rgba(255,255,255,0.05)"/>
        <rect x="0" y="{h-6}" width="{w}" height="6" fill="rgba(255,255,255,0.3)" rx="3"/>'''

    elif platform == "instagram_story":
        # Vertical wave pattern
        return f'''
        <ellipse cx="{w*0.5}" cy="{h*0.05}" rx="{w*0.7}" ry="{h*0.06}" fill="rgba(255,255,255,0.05)"/>
        <ellipse cx="{w*0.5}" cy="{h*0.95}" rx="{w*0.7}" ry="{h*0.06}" fill="rgba(255,255,255,0.05)"/>
        <circle cx="{w*0.9}" cy="{h*0.3}" r="{w*0.15}" fill="rgba(255,255,255,0.03)"/>
        <circle cx="{w*0.1}" cy="{h*0.7}" r="{w*0.2}" fill="rgba(255,255,255,0.03)"/>
        <rect x="{w*0.1}" y="{h*0.02}" width="{w*0.8}" height="3" fill="rgba(255,255,255,0.2)" rx="2"/>'''

    elif platform == "facebook_cover":
        # Wide horizontal stripes
        return f'''
        <rect x="0" y="0" width="{w}" height="4" fill="rgba(255,255,255,0.2)"/>
        <rect x="0" y="{h-4}" width="{w}" height="4" fill="rgba(255,255,255,0.2)"/>
        <circle cx="{w*0.05}" cy="{h*0.5}" r="{h*0.4}" fill="rgba(255,255,255,0.04)"/>
        <circle cx="{w*0.95}" cy="{h*0.5}" r="{h*0.35}" fill="rgba(255,255,255,0.03)"/>'''

    elif platform == "whatsapp_dp":
        # Rounded corner highlight
        return f'''
        <circle cx="{w*0.85}" cy="{h*0.15}" r="{w*0.1}" fill="rgba(255,255,255,0.08)"/>
        <circle cx="{w*0.15}" cy="{h*0.85}" r="{w*0.12}" fill="rgba(255,255,255,0.06)"/>'''

    return ""


def _darken_color(hex_color: str, amount: int = 30) -> str:
    """Darken a hex color by reducing RGB values."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#1a1a2e"
    try:
        r = max(0, int(hex_color[0:2], 16) - amount)
        g = max(0, int(hex_color[2:4], 16) - amount)
        b = max(0, int(hex_color[4:6], 16) - amount)
        return f"#{r:02x}{g:02x}{b:02x}"
    except ValueError:
        return "#1a1a2e"
