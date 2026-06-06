"""Legal Agent — Generates compliance checklist + pre-filled registration guides.

What it produces:
- Business-specific legal checklist (FSSAI, GST, Udyam, Shop Act)
- PDF legal guide with step-by-step Hindi instructions
- Pre-filled form data ready for submission
- Upload PDF to Supabase Storage

Dependencies: None (runs in parallel with Brand, Payment, Outreach)
Writes to state: legal_checklist, legal_pdf_url
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
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("[LegalAgent] WARNING: reportlab not installed, PDF generation disabled")


async def legal_agent(state: GenesisState) -> dict:
    """Run the Legal Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Analyze Compliance Needs (0% → 30%)
        # ══════════════════════════════════════
        await push_update(sid, "legal", 10, "Analyzing your compliance needs... ⚖️")

        business_name = state["business_name"]
        business_type = state.get("business_type", "")
        address = state.get("address", "")
        phone = state.get("phone", "")

        # Get legal requirements from Gemini
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
        await push_update(sid, "legal", 35, f"Found {len(registrations)} registrations needed 📋")

        # ══════════════════════════════════════
        # PHASE 2: Generate Checklist (30% → 60%)
        # ══════════════════════════════════════
        await push_update(sid, "legal", 45, "Creating your legal checklist... 📝")

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

        await push_update(sid, "legal", 55, "Checklist ready! Generating guide PDF... 📄")

        # ══════════════════════════════════════
        # PHASE 3: Generate PDF Guide (60% → 90%)
        # ══════════════════════════════════════
        pdf_url = None

        if HAS_REPORTLAB:
            try:
                await push_update(sid, "legal", 65, "Creating PDF legal guide... 📄")
                
                pdf_bytes = _generate_legal_pdf(
                    business_name=business_name,
                    business_type=business_type,
                    address=address,
                    phone=phone,
                    registrations=registrations,
                    summary=legal_data.get("summary_hindi", ""),
                    total_cost=legal_data.get("estimated_total_cost", ""),
                )

                # Upload to Supabase Storage
                pdf_path = f"legal/{sid}/legal_guide.pdf"
                pdf_url = await upload_to_storage(
                    "genesis-assets",
                    pdf_path,
                    pdf_bytes,
                    content_type="application/pdf",
                )

                await push_update(sid, "legal", 85, "PDF uploaded! ✅")

            except Exception as pdf_err:
                print(f"[LegalAgent] PDF generation failed: {pdf_err}")
                await push_update(sid, "legal", 85, "PDF skipped, checklist ready ⚠️")
        else:
            await push_update(sid, "legal", 85, "PDF generation unavailable, checklist ready ⚠️")

        # ══════════════════════════════════════
        # PHASE 4: Complete (90% → 100%)
        # ══════════════════════════════════════
        result_data = {
            "legal_checklist": checklist,
            "legal_pdf_url": pdf_url,
            "summary_hindi": legal_data.get("summary_hindi", ""),
            "total_cost": legal_data.get("estimated_total_cost", ""),
            "registration_count": len(checklist),
            "required_count": sum(1 for c in checklist if c["status"] == "required"),
        }

        await push_update(
            sid, "legal", 100,
            f"Legal guide ready! {len(checklist)} registrations identified ✅",
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


def _generate_legal_pdf(
    business_name: str,
    business_type: str,
    address: str,
    phone: str,
    registrations: list,
    summary: str,
    total_cost: str,
) -> bytes:
    """Generate a PDF legal guide using ReportLab. Returns bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#FF6B35"),
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=15,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
        leading=14,
    )

    elements = []

    # Title
    elements.append(Paragraph("GENESIS - Legal Compliance Guide", title_style))
    elements.append(Paragraph(f"<b>Business:</b> {business_name}", body_style))
    elements.append(Paragraph(f"<b>Type:</b> {business_type}", body_style))
    if address:
        elements.append(Paragraph(f"<b>Address:</b> {address}", body_style))
    if phone:
        elements.append(Paragraph(f"<b>Phone:</b> {phone}", body_style))
    elements.append(Spacer(1, 15))

    # Summary
    if summary:
        elements.append(Paragraph("Summary", heading_style))
        elements.append(Paragraph(summary, body_style))
        elements.append(Spacer(1, 10))

    # Total cost
    if total_cost:
        elements.append(Paragraph(f"<b>Estimated Total Cost:</b> {total_cost}", body_style))
        elements.append(Spacer(1, 10))

    # Registrations table
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
            doc_str = ", ".join(docs[:5])
            elements.append(Paragraph(f"   Documents: {doc_str}", body_style))
        
        if website:
            elements.append(Paragraph(f"   Website: {website}", body_style))
        
        elements.append(Spacer(1, 8))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "<i>Generated by GENESIS AI Business Launcher. This is a guide only — "
        "please verify requirements with local authorities.</i>",
        ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=colors.gray),
    ))

    doc.build(elements)
    return buffer.getvalue()
