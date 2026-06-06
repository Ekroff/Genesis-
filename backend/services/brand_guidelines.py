"""Brand Guidelines PDF Generator — Creates a professional brand kit document.

Generates a single-page brand guidelines PDF that looks like a ₹20,000 agency deliverable:
- Logo display (white + dark backgrounds)
- Color palette with HEX codes
- Font recommendation
- Taglines (Hindi + English)
- Do's and Don'ts
- Social media usage notes

Uses ReportLab. Uploaded to Supabase Storage.
"""

import io
from services.supabase_client import upload_to_storage

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage,
    )
    from reportlab.lib.units import inch, cm, mm
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


async def generate_brand_guidelines_pdf(
    session_id: str,
    business_name: str,
    tagline_hindi: str,
    tagline_english: str,
    primary_color: str,
    secondary_color: str,
    font_name: str = "Poppins",
    brand_mood: str = "",
    logo_url: str = "",
) -> str | None:
    """Generate and upload a brand guidelines PDF.
    
    Returns the public URL of the uploaded PDF.
    """
    if not HAS_REPORTLAB:
        print("[BrandGuidelines] reportlab not available")
        return None

    try:
        pdf_bytes = _build_brand_pdf(
            business_name=business_name,
            tagline_hindi=tagline_hindi,
            tagline_english=tagline_english,
            primary_color=primary_color,
            secondary_color=secondary_color,
            font_name=font_name,
            brand_mood=brand_mood,
        )

        path = f"brand/{session_id}/brand_guidelines.pdf"
        url = await upload_to_storage(
            "genesis-assets", path, pdf_bytes, content_type="application/pdf",
        )
        return url

    except Exception as e:
        print(f"[BrandGuidelines] Failed: {e}")
        return None


def _build_brand_pdf(
    business_name: str,
    tagline_hindi: str,
    tagline_english: str,
    primary_color: str,
    secondary_color: str,
    font_name: str,
    brand_mood: str,
) -> bytes:
    """Build the brand guidelines PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ──
    title = ParagraphStyle(
        "BrandTitle", parent=styles["Title"],
        fontSize=28, textColor=colors.HexColor(primary_color),
        spaceAfter=8, leading=32,
    )
    section = ParagraphStyle(
        "BrandSection", parent=styles["Heading2"],
        fontSize=14, textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=20, spaceAfter=10,
        borderWidth=0, borderPadding=0,
    )
    body = ParagraphStyle(
        "BrandBody", parent=styles["Normal"],
        fontSize=10, spaceAfter=6, leading=14,
    )
    small = ParagraphStyle(
        "BrandSmall", parent=styles["Normal"],
        fontSize=8, textColor=colors.gray, spaceAfter=4,
    )

    elements = []

    # ═══════ HEADER ═══════
    elements.append(Paragraph(f"{business_name}", title))
    elements.append(Paragraph("Brand Guidelines", ParagraphStyle(
        "Subtitle", parent=styles["Heading3"],
        fontSize=12, textColor=colors.HexColor("#666666"),
        spaceAfter=24,
    )))
    elements.append(Spacer(1, 10))

    # ═══════ TAGLINES ═══════
    elements.append(Paragraph("Tagline", section))
    elements.append(Paragraph(f'<font size="16"><b>{tagline_hindi}</b></font>', body))
    elements.append(Paragraph(f'<font size="11" color="#666666"><i>{tagline_english}</i></font>', body))
    elements.append(Spacer(1, 5))

    # ═══════ BRAND MOOD ═══════
    if brand_mood:
        elements.append(Paragraph("Brand Personality", section))
        elements.append(Paragraph(f"<b>{brand_mood}</b>", body))
        elements.append(Spacer(1, 5))

    # ═══════ COLOR PALETTE ═══════
    elements.append(Paragraph("Color Palette", section))

    try:
        p_color = colors.HexColor(primary_color)
        s_color = colors.HexColor(secondary_color)
    except Exception:
        p_color = colors.HexColor("#FF6B35")
        s_color = colors.HexColor("#FFF8F0")
        primary_color = "#FF6B35"
        secondary_color = "#FFF8F0"

    color_data = [
        ["", "Primary Color", "Secondary Color"],
        ["", primary_color.upper(), secondary_color.upper()],
    ]

    ct = Table(color_data, colWidths=[0.8 * inch, 2.5 * inch, 2.5 * inch], rowHeights=[50, 20])
    ct.setStyle(TableStyle([
        # Color swatches in row 0
        ("BACKGROUND", (1, 0), (1, 0), p_color),
        ("BACKGROUND", (2, 0), (2, 0), s_color),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.white),
        ("TEXTCOLOR", (2, 0), (2, 0), colors.HexColor("#333333")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("GRID", (1, 0), (-1, -1), 1, colors.HexColor("#eeeeee")),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
    ]))
    elements.append(ct)
    elements.append(Spacer(1, 10))

    # ═══════ TYPOGRAPHY ═══════
    elements.append(Paragraph("Typography", section))
    elements.append(Paragraph(f'<b>Primary Font:</b> {font_name}', body))
    elements.append(Paragraph(
        f'Use <b>{font_name}</b> for all headings, body text, and marketing materials. '
        f'Available free on Google Fonts: <font color="{primary_color}">fonts.google.com</font>',
        body,
    ))
    elements.append(Spacer(1, 5))

    # ═══════ DO'S AND DON'TS ═══════
    elements.append(Paragraph("Usage Guidelines", section))

    dos_donts = [
        ["✅ DO", "❌ DON'T"],
        [
            f"Use {primary_color.upper()} as the primary brand color on all materials",
            "Change the brand colors without approval",
        ],
        [
            "Keep the logo clear and visible with adequate spacing",
            "Stretch, rotate, or distort the logo",
        ],
        [
            f"Use {font_name} font consistently across all platforms",
            "Use decorative or hard-to-read fonts",
        ],
        [
            "Maintain the Hindi tagline on all Indian-market materials",
            "Translate the tagline literally — use the approved versions",
        ],
    ]

    dd_table = Table(dos_donts, colWidths=[3 * inch, 3 * inch])
    dd_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#E8F5E9")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FFEBEE")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(dd_table)

    # ═══════ FOOTER ═══════
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "<i>Generated by GENESIS AI — Your complete brand identity, created in minutes.</i>",
        ParagraphStyle("BrandFooter", parent=small, fontSize=8, textColor=colors.gray),
    ))

    doc.build(elements)
    return buf.getvalue()
