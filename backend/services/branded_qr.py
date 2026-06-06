"""Branded QR Code Generator — Creates logo-embedded QR codes.

Generates two types of branded QR codes:
1. UPI Payment QR — scan to pay via GPay/PhonePe/Paytm
2. WhatsApp Business QR — scan to open WhatsApp chat with pre-filled message

Each QR has the business logo embedded in the center with rounded modules.
Uploaded to Supabase Storage for download.
"""

import io
import urllib.parse
import httpx
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from PIL import Image

from services.supabase_client import upload_to_storage


async def generate_branded_upi_qr(
    session_id: str,
    upi_id: str,
    business_name: str,
    logo_url: str | None = None,
) -> str | None:
    """Generate a branded UPI payment QR with logo in center.
    
    Returns public URL of the uploaded PNG.
    """
    upi_string = (
        f"upi://pay?"
        f"pa={upi_id}&"
        f"pn={urllib.parse.quote(business_name)}&"
        f"cu=INR"
    )

    img = _make_branded_qr(upi_string)
    img = await _embed_logo(img, logo_url)

    # Upload
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    path = f"qr/{session_id}/upi_branded.png"
    url = await upload_to_storage(
        "genesis-assets", path, buf.getvalue(), content_type="image/png"
    )
    return url


async def generate_whatsapp_qr(
    session_id: str,
    phone: str,
    business_name: str,
    logo_url: str | None = None,
) -> str | None:
    """Generate a branded WhatsApp Business QR.
    
    When scanned, opens WhatsApp chat with pre-filled message.
    Returns public URL of the uploaded PNG.
    """
    # Clean phone number
    clean_phone = phone.replace(" ", "").replace("-", "").replace("+91", "")
    if clean_phone.startswith("0"):
        clean_phone = clean_phone[1:]

    message = f"Hi! I found {business_name} online. I'm interested in your services."
    wa_url = f"https://wa.me/91{clean_phone}?text={urllib.parse.quote(message)}"

    img = _make_branded_qr(wa_url)
    img = await _embed_logo(img, logo_url)

    # Upload
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    path = f"qr/{session_id}/whatsapp_branded.png"
    url = await upload_to_storage(
        "genesis-assets", path, buf.getvalue(), content_type="image/png"
    )
    return url


def _make_branded_qr(data: str) -> Image.Image:
    """Create a styled QR code with rounded modules."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High correction for logo overlay
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
    )

    # Convert to RGBA for logo compositing
    return img.convert("RGBA")


async def _embed_logo(qr_img: Image.Image, logo_url: str | None) -> Image.Image:
    """Download logo and paste it in the center of the QR code."""
    if not logo_url or not logo_url.startswith("http"):
        return qr_img.convert("RGB")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(logo_url)
            resp.raise_for_status()

        logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")

        # Resize logo to ~20% of QR size
        qr_w, qr_h = qr_img.size
        logo_size = int(qr_w * 0.2)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

        # White background circle behind logo for visibility
        bg = Image.new("RGBA", (logo_size + 16, logo_size + 16), (255, 255, 255, 255))
        paste_x = (qr_w - bg.width) // 2
        paste_y = (qr_h - bg.height) // 2
        qr_img.paste(bg, (paste_x, paste_y))

        # Paste logo centered
        logo_x = (qr_w - logo_size) // 2
        logo_y = (qr_h - logo_size) // 2
        qr_img.paste(logo, (logo_x, logo_y), logo)

        return qr_img.convert("RGB")

    except Exception as e:
        print(f"[QR] Logo embed failed: {e}, returning plain QR")
        return qr_img.convert("RGB")
