"""Legal Agent — Compliance checklist + GST Revenue Calculator + Menu Pricing Intelligence.

What it produces:
- Business-specific legal checklist (FSSAI, GST, Udyam, Shop Act)
- PDF legal guide with step-by-step Hindi instructions
- GST Revenue Calculator (estimates annual revenue, months to threshold)
- Menu Pricing Intelligence (market comparison + suggestions)

Dependencies: None (runs in parallel with Brand, Payment, Outreach)
Writes to state: legal_checklist, legal_pdf_url, gst_analysis, pricing_analysis
"""

from agents.state import GenesisState
from services.supabase_client import push_update, upload_to_storage
from services.gemini_client import generate_json
import traceback
import io

# ReportLab for PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch, cm
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("[LegalAgent] WARNING: reportlab not installed, PDF generation disabled")


async def legal_agent(state: GenesisState) -> dict:
    """Run the Legal Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Analyze Compliance Needs (0% → 25%)
        # ══════════════════════════════════════
        await push_update(sid, "legal", 10, "Analyzing your compliance needs... ⚖️")

        business_name = state["business_name"]
        business_type = state.get("business_type", "")
        address = state.get("address", "")
        phone = state.get("phone", "")
        menu = state.get("menu", [])

        legal_data = await generate_json(f"""
You are an Indian MSME legal compliance expert.

Business Name: {business_name}
Business Type: {business_type}
Address: {address}

Analyze what legal registrations this business needs.
Return JSON:
{{
    "registrations": [
        {{
            "name": "Registration name (e.g., FSSAI, GST, Udyam)",
            "status": "required" or "recommended" or "optional",
            "reason": "Why this is needed (1 sentence in Hindi)",
            "cost": "Registration cost (e.g., Free, ₹100, ₹2000)",
            "time": "Processing time (e.g., 7 days, 30 days)",
            "website": "Official registration website URL",
            "documents_needed": ["list", "of", "documents"]
        }}
    ],
    "summary_hindi": "2-3 sentence summary in Hindi about what the business owner should do first",
    "estimated_total_cost": "Total estimated cost for all registrations"
}}

Include ALL relevant registrations for a {business_type} business in India:
- FSSAI (if food), GST (if turnover applicable), Udyam MSME, Shop & Establishment Act
- Any state-specific requirements based on the address
""")

        registrations = legal_data.get("registrations", [])
        await push_update(sid, "legal", 25, f"Found {len(registrations)} registrations needed 📋")

        # Build checklist
        checklist = []
        for reg in registrations:
            checklist.append({
                "item": reg.get("name", "Unknown"),
                "status": reg.get("status", "recommended"),
                "reason": reg.get("reason", ""),
                "cost": reg.get("cost", ""),
                "time": reg.get("time", ""),
                "website": reg.get("website", ""),
                "documents": reg.get("documents_needed", []),
            })

        # ══════════════════════════════════════
        # PHASE 2: GST Revenue Calculator (25% → 50%)
        # ══════════════════════════════════════
        await push_update(sid, "legal", 30, "Calculating GST projections... 📊")

        gst_analysis = await _calculate_gst_projections(menu, business_type, address)

        await push_update(sid, "legal", 48, f"GST analysis done! {gst_analysis.get('verdict', '')} 📊")

        # ══════════════════════════════════════
        # PHASE 3: Menu Pricing Intelligence (50% → 70%)
        # ══════════════════════════════════════
        pricing_analysis = {}
        if menu:
            await push_update(sid, "legal", 52, "Analyzing menu pricing vs market... 💰")
            pricing_analysis = await _analyze_menu_pricing(menu, business_type, address)
            await push_update(sid, "legal", 68, "Pricing intelligence ready! 💡")

        # ══════════════════════════════════════
        # PHASE 4: Generate PDF Guide (70% → 90%)
        # ══════════════════════════════════════
        pdf_url = None

        if HAS_REPORTLAB:
            try:
                await push_update(sid, "legal", 72, "Creating PDF legal guide... 📄")

                pdf_bytes = _generate_legal_pdf(
                    business_name=business_name,
                    business_type=business_type,
                    address=address,
                    phone=phone,
                    registrations=registrations,
                    summary=legal_data.get("summary_hindi", ""),
                    total_cost=legal_data.get("estimated_total_cost", ""),
                    gst_analysis=gst_analysis,
                    pricing_analysis=pricing_analysis,
                )

                pdf_path = f"legal/{sid}/legal_guide.pdf"
                pdf_url = await upload_to_storage(
                    "genesis-assets", pdf_path, pdf_bytes, content_type="application/pdf",
                )
                await push_update(sid, "legal", 88, "PDF uploaded! ✅")

            except Exception as pdf_err:
                print(f"[LegalAgent] PDF generation failed: {pdf_err}")
                await push_update(sid, "legal", 88, "PDF skipped, checklist ready ⚠️")
        else:
            await push_update(sid, "legal", 88, "PDF unavailable, checklist ready ⚠️")

        # ══════════════════════════════════════
        # PHASE 5: Complete (90% → 100%)
        # ══════════════════════════════════════
        result_data = {
            "legal_checklist": checklist,
            "legal_pdf_url": pdf_url,
            "summary_hindi": legal_data.get("summary_hindi", ""),
            "total_cost": legal_data.get("estimated_total_cost", ""),
            "registration_count": len(checklist),
            "required_count": sum(1 for c in checklist if c["status"] == "required"),
            "gst_analysis": gst_analysis,
            "pricing_analysis": pricing_analysis,
        }

        await push_update(
            sid, "legal", 100,
            f"Legal + GST + Pricing ready! {len(checklist)} registrations ✅",
            status="completed",
            result_data=result_data,
        )

        return {
            "legal_checklist": checklist,
            "legal_pdf_url": pdf_url,
            "completed_agents": ["legal"],
        }

    except Exception as e:
        error_msg = f"Legal Agent error: {str(e)}"
        print(f"[LegalAgent] ERROR: {traceback.format_exc()}")
        await push_update(sid, "legal", 0, error_msg, status="error")

        return {
            "legal_checklist": [],
            "legal_pdf_url": None,
            "completed_agents": ["legal"],
        }


# ═══════════════════════════════════════════════════
# GST REVENUE CALCULATOR
# ═══════════════════════════════════════════════════

async def _calculate_gst_projections(
    menu: list, business_type: str, address: str
) -> dict:
    """Calculate GST projections based on menu prices and estimated orders."""

    if not menu:
        return {
            "daily_revenue": 0,
            "monthly_revenue": 0,
            "annual_revenue": 0,
            "gst_needed": False,
            "months_to_threshold": None,
            "verdict": "No menu data — cannot estimate",
        }

    avg_price = sum(m.get("price", 0) for m in menu) / max(len(menu), 1)

    result = await generate_json(f"""
You are an Indian small business financial advisor.

Business type: {business_type}
Location: {address}
Menu items: {len(menu)}
Average item price: ₹{avg_price:.0f}
Menu: {[f"{m.get('item','')} ₹{m.get('price',0)}" for m in menu[:10]]}

Estimate realistic daily orders for this type of business in this location.
Consider:
- Type of business (tiffin, restaurant, chai, etc.)
- Location density (metro vs tier-2 vs rural)
- Typical customer count for a new small business

Return JSON:
{{
    "estimated_daily_orders": 25,
    "avg_order_value": 120,
    "daily_revenue": 3000,
    "monthly_revenue": 90000,
    "annual_revenue": 1080000,
    "gst_threshold": 2000000,
    "gst_needed_now": false,
    "months_to_threshold": 22,
    "growth_rate_monthly_percent": 5,
    "verdict_hindi": "Your current revenue is below ₹20L GST threshold. At 5% monthly growth, you'll reach it in ~22 months. We recommend starting GST registration at ₹15L to avoid penalties.",
    "recommendation": "Start GST registration when monthly revenue crosses ₹1.25 lakh consistently"
}}

Be realistic for an Indian small business. Not too optimistic, not pessimistic.
""")

    return {
        "estimated_daily_orders": result.get("estimated_daily_orders", 20),
        "avg_order_value": result.get("avg_order_value", avg_price),
        "daily_revenue": result.get("daily_revenue", 0),
        "monthly_revenue": result.get("monthly_revenue", 0),
        "annual_revenue": result.get("annual_revenue", 0),
        "gst_threshold": 2000000,
        "gst_needed": result.get("gst_needed_now", False),
        "months_to_threshold": result.get("months_to_threshold"),
        "growth_rate": result.get("growth_rate_monthly_percent", 5),
        "verdict": result.get("verdict_hindi", ""),
        "recommendation": result.get("recommendation", ""),
    }


# ═══════════════════════════════════════════════════
# MENU PRICING INTELLIGENCE
# ═══════════════════════════════════════════════════

async def _analyze_menu_pricing(menu: list, business_type: str, address: str) -> dict:
    """Analyze menu prices against typical market rates."""

    menu_str = "\n".join([f"- {m.get('item', '')}: ₹{m.get('price', 0)}" for m in menu])

    result = await generate_json(f"""
You are an Indian small business pricing consultant.

Business type: {business_type}
Location: {address}

Current menu:
{menu_str}

Analyze each item's pricing compared to typical market rates in this location.
Consider:
- Local market rates for similar items
- Cost of ingredients
- Competitive pricing in the area
- Profit margin suggestions

Return JSON:
{{
    "items": [
        {{
            "item": "Dal Chawal",
            "current_price": 80,
            "market_low": 70,
            "market_avg": 90,
            "market_high": 110,
            "verdict": "underpriced",
            "suggested_price": 90,
            "advice_hindi": "आपकी price market average से कम है। ₹90 करने पर भी customers आएंगे।"
        }}
    ],
    "overall_verdict_hindi": "2-3 sentence overall pricing assessment in Hindi",
    "potential_monthly_increase": 5000
}}

Be specific and practical. These are real small business owners.
""")

    return result


# ═══════════════════════════════════════════════════
# BRAND GUIDELINES PDF
# ═══════════════════════════════════════════════════

def _generate_legal_pdf(
    business_name: str,
    business_type: str,
    address: str,
    phone: str,
    registrations: list,
    summary: str,
    total_cost: str,
    gst_analysis: dict = None,
    pricing_analysis: dict = None,
) -> bytes:
    """Generate a comprehensive PDF legal guide with GST + pricing sections."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=20, textColor=colors.HexColor("#FF6B35"), spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "CustomHeading", parent=styles["Heading2"],
        fontSize=14, textColor=colors.HexColor("#1a1a2e"), spaceBefore=15, spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "CustomBody", parent=styles["Normal"],
        fontSize=10, spaceAfter=6, leading=14,
    )
    highlight_style = ParagraphStyle(
        "Highlight", parent=body_style,
        backColor=colors.HexColor("#FFF8F0"), borderPadding=8,
    )

    elements = []

    # ── Title ──
    elements.append(Paragraph("GENESIS - Legal & Financial Guide", title_style))
    elements.append(Paragraph(f"<b>Business:</b> {business_name}", body_style))
    elements.append(Paragraph(f"<b>Type:</b> {business_type}", body_style))
    if address:
        elements.append(Paragraph(f"<b>Address:</b> {address}", body_style))
    if phone:
        elements.append(Paragraph(f"<b>Phone:</b> {phone}", body_style))
    elements.append(Spacer(1, 15))

    # ── Summary ──
    if summary:
        elements.append(Paragraph("Summary", heading_style))
        elements.append(Paragraph(summary, body_style))
        elements.append(Spacer(1, 10))

    # ── Total cost ──
    if total_cost:
        elements.append(Paragraph(f"<b>Estimated Total Cost:</b> {total_cost}", body_style))
        elements.append(Spacer(1, 10))

    # ── Registrations ──
    elements.append(Paragraph("Required Registrations", heading_style))

    for i, reg in enumerate(registrations, 1):
        name = reg.get("name", "Unknown")
        status = reg.get("status", "").upper()
        cost = reg.get("cost", "N/A")
        time_est = reg.get("time", "N/A")
        reason = reg.get("reason", "")
        website = reg.get("website", "")

        status_color = {"REQUIRED": "red", "RECOMMENDED": "orange", "OPTIONAL": "green"}.get(status, "black")

        elements.append(Paragraph(
            f"<b>{i}. {name}</b> — <font color='{status_color}'>[{status}]</font>",
            body_style,
        ))
        if reason:
            elements.append(Paragraph(f"   Reason: {reason}", body_style))
        elements.append(Paragraph(f"   Cost: {cost} | Time: {time_est}", body_style))

        docs = reg.get("documents_needed", [])
        if docs:
            elements.append(Paragraph(f"   Documents: {', '.join(docs[:5])}", body_style))
        if website:
            elements.append(Paragraph(f"   Website: {website}", body_style))
        elements.append(Spacer(1, 8))

    # ── GST Revenue Calculator ──
    if gst_analysis and gst_analysis.get("daily_revenue"):
        elements.append(Paragraph("GST Revenue Analysis", heading_style))

        gst_data = [
            ["Metric", "Value"],
            ["Estimated Daily Orders", str(gst_analysis.get("estimated_daily_orders", "—"))],
            ["Average Order Value", f"₹{gst_analysis.get('avg_order_value', 0):.0f}"],
            ["Daily Revenue", f"₹{gst_analysis.get('daily_revenue', 0):,.0f}"],
            ["Monthly Revenue", f"₹{gst_analysis.get('monthly_revenue', 0):,.0f}"],
            ["Annual Revenue", f"₹{gst_analysis.get('annual_revenue', 0):,.0f}"],
            ["GST Threshold", "₹20,00,000"],
            ["GST Needed Now?", "Yes" if gst_analysis.get("gst_needed") else "No"],
        ]

        if gst_analysis.get("months_to_threshold"):
            gst_data.append(["Months to Threshold", f"~{gst_analysis['months_to_threshold']} months"])

        t = Table(gst_data, colWidths=[3.5*inch, 3*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF6B35")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FAFAFA")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF8F0")]),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 8))

        verdict = gst_analysis.get("verdict", "")
        if verdict:
            elements.append(Paragraph(f"<b>Analysis:</b> {verdict}", body_style))

        recommendation = gst_analysis.get("recommendation", "")
        if recommendation:
            elements.append(Paragraph(f"<b>Recommendation:</b> {recommendation}", body_style))
        elements.append(Spacer(1, 10))

    # ── Menu Pricing Intelligence ──
    if pricing_analysis and pricing_analysis.get("items"):
        elements.append(Paragraph("Menu Pricing Intelligence", heading_style))

        pricing_data = [["Item", "Your Price", "Market Avg", "Suggested", "Verdict"]]
        for item in pricing_analysis.get("items", []):
            verdict = item.get("verdict", "")
            verdict_color = "red" if verdict == "underpriced" else "green" if verdict == "overpriced" else "black"
            pricing_data.append([
                item.get("item", ""),
                f"₹{item.get('current_price', 0)}",
                f"₹{item.get('market_avg', 0)}",
                f"₹{item.get('suggested_price', 0)}",
                verdict.upper(),
            ])

        t2 = Table(pricing_data, colWidths=[2*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.3*inch])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3B82F6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F7FF")]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 8))

        overall = pricing_analysis.get("overall_verdict_hindi", "")
        if overall:
            elements.append(Paragraph(f"<b>Overall:</b> {overall}", body_style))

        potential = pricing_analysis.get("potential_monthly_increase", 0)
        if potential:
            elements.append(Paragraph(
                f"<b>Potential Monthly Revenue Increase:</b> ₹{potential:,.0f}",
                body_style,
            ))

    # ── Footer ──
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "<i>Generated by GENESIS AI Business Launcher. This is a guide only — "
        "please verify requirements with local authorities.</i>",
        ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=colors.gray),
    ))

    doc.build(elements)
    return buffer.getvalue()
