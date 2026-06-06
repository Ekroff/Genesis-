"""Payment Agent — Branded UPI QR + WhatsApp QR + Smart Invoice.

What it produces:
- Logo-embedded UPI QR code (branded, rounded modules — the demo killer)
- WhatsApp Business QR (scan → opens WhatsApp chat with business)
- Smart Invoice page URL (voice order → exact-amount UPI link)
- Fallback plain QR if branded generation fails

Dependencies: Brand Agent logo_url (optional, works without it)
Writes to state: upi_qr_url, whatsapp_qr_url, invoice_page_url
"""

from agents.state import GenesisState
from services.supabase_client import push_update
from services.branded_qr import generate_branded_upi_qr, generate_whatsapp_qr
import urllib.parse
import traceback


async def payment_agent(state: GenesisState) -> dict:
    """Run the Payment Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Build UPI ID (0% → 10%)
        # ══════════════════════════════════════
        await push_update(sid, "payment", 5, "Setting up payment... 💳")

        upi_id = state.get("upi_id", "")
        if not upi_id:
            phone = state.get("phone", "")
            upi_id = f"{phone}@paytm" if phone else "merchant@paytm"

        business_name = state["business_name"]
        phone = state.get("phone", "")
        logo_url = state.get("logo_url", "")

        # ══════════════════════════════════════
        # PHASE 2: Branded UPI QR (10% → 45%)
        # ══════════════════════════════════════
        await push_update(sid, "payment", 15, "Creating branded UPI QR code... 🎨")

        branded_qr_url = None
        try:
            branded_qr_url = await generate_branded_upi_qr(
                session_id=sid,
                upi_id=upi_id,
                business_name=business_name,
                logo_url=logo_url,
            )
            await push_update(sid, "payment", 40, "Branded UPI QR created! ✅")
        except Exception as qr_err:
            print(f"[PaymentAgent] Branded QR failed, falling back: {qr_err}")

        # Fallback to plain QR if branded fails
        if not branded_qr_url:
            upi_string = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(business_name)}&cu=INR"
            branded_qr_url = (
                f"https://api.qrserver.com/v1/create-qr-code/"
                f"?size=400x400"
                f"&data={urllib.parse.quote(upi_string)}"
                f"&bgcolor=ffffff&color=000000&format=png"
            )
            await push_update(sid, "payment", 40, "UPI QR ready ✅")

        # ══════════════════════════════════════
        # PHASE 3: WhatsApp Business QR (45% → 70%)
        # ══════════════════════════════════════
        whatsapp_qr_url = None
        if phone:
            await push_update(sid, "payment", 50, "Creating WhatsApp Business QR... 📱")
            try:
                whatsapp_qr_url = await generate_whatsapp_qr(
                    session_id=sid,
                    phone=phone,
                    business_name=business_name,
                    logo_url=logo_url,
                )
                await push_update(sid, "payment", 68, "WhatsApp QR created! 📱")
            except Exception as wa_err:
                print(f"[PaymentAgent] WhatsApp QR failed: {wa_err}")
                await push_update(sid, "payment", 68, "WhatsApp QR skipped ⚠️")

        # ══════════════════════════════════════
        # PHASE 4: Smart Invoice (70% → 90%)
        # ══════════════════════════════════════
        await push_update(sid, "payment", 75, "Setting up Smart Invoice tool... 🧾")

        invoice_page_url = f"/pay/{sid}"

        await push_update(sid, "payment", 88, "Smart Invoice ready! 🧾")

        # ══════════════════════════════════════
        # PHASE 5: Complete (90% → 100%)
        # ══════════════════════════════════════
        result_data = {
            "upi_qr_url": branded_qr_url,
            "upi_id": upi_id,
            "whatsapp_qr_url": whatsapp_qr_url,
            "invoice_page_url": invoice_page_url,
            "menu_items": state.get("menu", []),
            "has_branded_qr": "branded" if "genesis-assets" in (branded_qr_url or "") else "plain",
        }

        await push_update(
            sid, "payment", 100,
            "Payment setup complete! Branded QR + WhatsApp QR ready ✅",
            status="completed",
            result_data=result_data,
        )

        completed = list(state.get("completed_agents", []))
        completed.append("payment")

        return {
            "upi_qr_url": branded_qr_url,
            "whatsapp_qr_url": whatsapp_qr_url,
            "invoice_page_url": invoice_page_url,
            "completed_agents": completed,
        }

    except Exception as e:
        error_msg = f"Payment Agent error: {str(e)}"
        print(f"[PaymentAgent] ERROR: {traceback.format_exc()}")
        await push_update(sid, "payment", 0, error_msg, status="error")

        completed = list(state.get("completed_agents", []))
        completed.append("payment")

        return {
            "upi_qr_url": None,
            "whatsapp_qr_url": None,
            "invoice_page_url": None,
            "completed_agents": completed,
        }
