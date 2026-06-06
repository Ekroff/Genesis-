"""Payment Agent — UPI QR generation + Smart Invoice tool setup.

What it produces:
- General UPI QR code (for walk-in customers)
- Smart Invoice page URL (genesis.vercel.app/pay/{session_id})
- Menu stored for invoice parsing

Dependencies: None (runs in parallel with Brand, Outreach, Legal)
Writes to state: upi_qr_url, invoice_page_url
"""

from agents.state import GenesisState
from services.supabase_client import push_update
import urllib.parse
import traceback


async def payment_agent(state: GenesisState) -> dict:
    """Run the Payment Agent. Returns updates to merge into GenesisState."""
    sid = state["session_id"]

    try:
        # ══════════════════════════════════════
        # PHASE 1: Generate UPI QR (0% → 40%)
        # ══════════════════════════════════════
        await push_update(sid, "payment", 10, "Generating your UPI QR code... 💳")

        # Build UPI ID from phone if not provided
        upi_id = state.get("upi_id", "")
        if not upi_id:
            phone = state.get("phone", "")
            if phone:
                upi_id = f"{phone}@paytm"
            else:
                upi_id = "merchant@paytm"

        business_name = state["business_name"]

        # Generate general-purpose UPI QR (no amount — for walk-in payments)
        upi_string = (
            f"upi://pay?"
            f"pa={upi_id}&"
            f"pn={urllib.parse.quote(business_name)}&"
            f"cu=INR"
        )
        qr_url = (
            f"https://api.qrserver.com/v1/create-qr-code/"
            f"?size=400x400"
            f"&data={urllib.parse.quote(upi_string)}"
            f"&bgcolor=ffffff"
            f"&color=000000"
            f"&format=png"
        )

        await push_update(sid, "payment", 40, "UPI QR code created! ✅")

        # ══════════════════════════════════════
        # PHASE 2: Smart Invoice Tool (40% → 80%)
        # ══════════════════════════════════════
        await push_update(sid, "payment", 50, "Setting up Smart Invoice tool... 🧾")

        # The invoice page is a dynamic route in the Next.js frontend
        # It reads session data (menu, business name) from Supabase
        # and uses Gemini to parse natural language orders
        invoice_page_url = f"/pay/{sid}"

        await push_update(sid, "payment", 75, "Smart Invoice ready! 🧾")

        # ══════════════════════════════════════
        # PHASE 3: Complete (80% → 100%)
        # ══════════════════════════════════════
        result_data = {
            "upi_qr_url": qr_url,
            "upi_id": upi_id,
            "invoice_page_url": invoice_page_url,
            "menu_items": state.get("menu", []),
        }

        await push_update(
            sid, "payment", 100,
            "Payment setup complete! ✅",
            status="completed",
            result_data=result_data,
        )

        completed = list(state.get("completed_agents", []))
        completed.append("payment")

        return {
            "upi_qr_url": qr_url,
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
            "invoice_page_url": None,
            "completed_agents": completed,
        }
