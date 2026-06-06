"""Image generation service — Logo and product photo generation.

Tested & working pipeline (June 2026):
1. Kie.ai (FLUX Pro — user's API key, high quality)
2. Gemini native image gen (if billing enabled)  
3. Stable Horde (free community GPUs, ~30-60s)
4. SVG gradient logo (instant, always works)
"""

import httpx
import os
import uuid
import base64
import urllib.parse
import asyncio
import json
import time
from config import GEMINI_API_KEY, KIE_API_KEY

# Business-type-specific logo style prompts
LOGO_STYLE_MAP = {
    "tiffin_delivery": "warm tiffin box or thali plate icon, orange and cream colors, Indian food service",
    "home_baker": "cupcake or whisk icon, pastel pink and cream, bakery warmth",
    "tutor": "open book or graduation cap icon, deep blue and white, academic trust",
    "tailor": "needle and thread or scissors icon, royal purple and gold, craftsmanship",
    "salon": "scissors or comb icon, rose gold and white, beauty elegance",
    "kirana": "shopping bag or grocery basket icon, green and cream, freshness",
    "plumber": "wrench or water drop icon, blue and silver, reliability",
    "electrician": "lightning bolt or bulb icon, yellow and dark blue, energy",
    "photographer": "camera or lens icon, black and gold, creativity",
    "gym_trainer": "dumbbell or flex icon, red and black, strength",
    "doctor": "stethoscope or health plus icon, teal and white, trust",
    "lawyer": "scales of justice icon, navy and gold, authority",
    "cloud_kitchen": "steaming pot or chef hat, red and white, delicious food",
    "car_wash": "car sparkle icon, blue and silver, shine",
    "pet_care": "paw print icon, warm brown and cream, love",
}

# Color palettes for SVG fallback and brand identity
BUSINESS_COLORS = {
    "tiffin_delivery": ("#FF6B35", "#FFF0E6"),
    "home_baker": ("#E91E63", "#FCE4EC"),
    "tutor": ("#1565C0", "#E3F2FD"),
    "tailor": ("#7B1FA2", "#F3E5F5"),
    "salon": ("#C2185B", "#FCE4EC"),
    "kirana": ("#2E7D32", "#E8F5E9"),
    "plumber": ("#1976D2", "#E3F2FD"),
    "electrician": ("#F9A825", "#FFF8E1"),
    "photographer": ("#212121", "#F5F5F5"),
    "gym_trainer": ("#C62828", "#FFEBEE"),
    "doctor": ("#00897B", "#E0F2F1"),
    "lawyer": ("#283593", "#E8EAF6"),
    "cloud_kitchen": ("#D32F2F", "#FFEBEE"),
    "car_wash": ("#0288D1", "#E1F5FE"),
    "pet_care": ("#795548", "#EFEBE9"),
}


async def generate_logo(business_name: str, business_type: str) -> str:
    """Generate a professional logo. Returns URL or data URI.
    
    Cascade: Kie.ai FLUX → Gemini → Stable Horde → SVG fallback
    """
    style = LOGO_STYLE_MAP.get(
        business_type,
        "relevant professional icon, trustworthy modern colors"
    )
    prompt = (
        f"Professional minimal flat logo icon design for '{business_name}', "
        f"an Indian small business. {style}. "
        f"Vector art style, simple clean geometric shapes, "
        f"solid white background, absolutely no text or letters, "
        f"centered composition, high quality, crisp edges"
    )

    # Method 1: Kie.ai with FLUX Pro (user's key, best quality)
    if KIE_API_KEY:
        try:
            url = await _generate_with_kie(prompt)
            if url:
                print(f"[ImageGen] Kie.ai FLUX succeeded")
                return url
        except Exception as e:
            print(f"[ImageGen] Kie.ai failed: {e}")

    # Method 2: Gemini native image generation
    if GEMINI_API_KEY:
        try:
            url = await _generate_with_gemini(prompt)
            if url:
                print(f"[ImageGen] Gemini succeeded")
                return url
        except Exception as e:
            print(f"[ImageGen] Gemini failed: {e}")

    # Method 3: Stable Horde (free, community powered)
    try:
        url = await _generate_with_stable_horde(prompt)
        if url:
            print(f"[ImageGen] Stable Horde succeeded")
            return url
    except Exception as e:
        print(f"[ImageGen] Stable Horde failed: {e}")

    # Method 4: SVG fallback (instant, always works)
    print(f"[ImageGen] Using SVG fallback for '{business_name}'")
    return _generate_svg_logo(business_name, business_type)


# ═══════════════════════════════════════════════
# Kie.ai — FLUX Pro (primary, user's paid key)
# ═══════════════════════════════════════════════

async def _generate_with_kie(prompt: str) -> str:
    """Generate image using Kie.ai's FLUX Pro model.
    
    Kie.ai is an API aggregator — one key for FLUX, Stable Diffusion, etc.
    Tested & confirmed working (June 2026):
      - POST /jobs/createTask → get taskId
      - GET /jobs/recordInfo?taskId=... → poll until state="success"
      - Parse resultJson → resultUrls[0] for image URL
    """
    KIE_BASE = "https://api.kie.ai/api/v1"
    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        # Step 1: Create task
        create_resp = await client.post(
            f"{KIE_BASE}/jobs/createTask",
            headers=headers,
            json={
                "model": "flux-2/pro-text-to-image",
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": "1:1",
                    "resolution": "1K",
                    "nsfw_checker": False,
                },
            },
        )

        if create_resp.status_code != 200:
            print(f"[Kie] Create failed: {create_resp.status_code} {create_resp.text[:200]}")
            return None

        data = create_resp.json()
        task_id = data.get("data", {}).get("taskId")
        if not task_id:
            print(f"[Kie] No taskId in response: {data}")
            return None

        print(f"[Kie] Task created: {task_id}")

        # Step 2: Poll with GET /jobs/recordInfo (max 120 seconds)
        for attempt in range(40):
            await asyncio.sleep(3)

            status_resp = await client.get(
                f"{KIE_BASE}/jobs/recordInfo",
                params={"taskId": task_id},
                headers=headers,
            )

            if status_resp.status_code != 200:
                continue

            status_data = status_resp.json()
            task_state = status_data.get("data", {}).get("state", "")

            if task_state == "success":
                # Extract image URL from resultJson
                result_json_str = status_data.get("data", {}).get("resultJson", "")
                if result_json_str:
                    try:
                        result_obj = json.loads(result_json_str)
                        urls = result_obj.get("resultUrls", [])
                        if urls and isinstance(urls[0], str):
                            print(f"[Kie] Image generated: {urls[0][:80]}...")
                            return urls[0]
                    except json.JSONDecodeError:
                        pass
                
                print(f"[Kie] Success but can't parse resultJson")
                return None

            elif task_state == "fail":
                fail_msg = status_data.get("data", {}).get("failMsg", "Unknown")
                print(f"[Kie] Task failed: {fail_msg}")
                return None

            # Still processing (waiting/queuing/generating)
            if attempt % 5 == 0:
                print(f"[Kie] State: {task_state or 'pending'}... ({attempt * 3}s)")

    print(f"[Kie] Timed out after 120 seconds")
    return None


# ═══════════════════════════════════════════════
# Gemini — Nano Banana 2 (if billing enabled)
# ═══════════════════════════════════════════════

async def _generate_with_gemini(prompt: str) -> str:
    """Gemini native image generation."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    models = ["gemini-2.5-flash-image", "gemini-3.1-flash-image"]

    for model in models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    try:
                        from services.supabase_client import upload_to_storage
                        filename = f"logos/{uuid.uuid4().hex}.png"
                        url = await upload_to_storage(
                            "genesis-assets", filename, image_bytes, "image/png"
                        )
                        if url:
                            return url
                    except Exception:
                        pass
                    b64 = base64.b64encode(image_bytes).decode()
                    return f"data:image/png;base64,{b64}"
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                continue
            raise
    return None


# ═══════════════════════════════════════════════
# Stable Horde — Free community GPUs
# ═══════════════════════════════════════════════

async def _generate_with_stable_horde(prompt: str) -> str:
    """Generate image using Stable Horde — free, community-powered."""
    HORDE_URL = "https://stablehorde.net/api/v2"
    ANON_KEY = "0000000000"

    headers = {
        "Content-Type": "application/json",
        "apikey": ANON_KEY,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        submit_resp = await client.post(
            f"{HORDE_URL}/generate/async",
            headers=headers,
            json={
                "prompt": prompt,
                "params": {
                    "width": 512, "height": 512,
                    "steps": 25, "cfg_scale": 7,
                    "sampler_name": "k_euler_a",
                },
                "nsfw": False,
                "censor_nsfw": True,
            },
        )

        if submit_resp.status_code not in (200, 202):
            return None

        job_id = submit_resp.json().get("id")
        if not job_id:
            return None

        for attempt in range(30):
            await asyncio.sleep(3)
            status_resp = await client.get(
                f"{HORDE_URL}/generate/check/{job_id}", headers=headers,
            )
            if status_resp.status_code != 200:
                continue
            status = status_resp.json()
            if status.get("done"):
                result_resp = await client.get(
                    f"{HORDE_URL}/generate/status/{job_id}", headers=headers,
                )
                if result_resp.status_code == 200:
                    gens = result_resp.json().get("generations", [])
                    if gens:
                        return gens[0].get("img", "")
                break
            if status.get("faulted"):
                break
    return None


# ═══════════════════════════════════════════════
# SVG Fallback — Instant, always works
# ═══════════════════════════════════════════════

def _generate_svg_logo(business_name: str, business_type: str) -> str:
    """Generate a premium SVG logo as data URI. Always works, instant."""
    primary, secondary = BUSINESS_COLORS.get(
        business_type, ("#FF6B35", "#FFF0E6")
    )
    initial = business_name[0].upper() if business_name else "G"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{primary}" />
      <stop offset="100%" style="stop-color:{primary}BB" />
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.15"/>
    </filter>
  </defs>
  <rect width="400" height="400" fill="white"/>
  <rect x="40" y="40" width="320" height="320" rx="64" fill="url(#grad)" filter="url(#shadow)"/>
  <rect x="60" y="60" width="280" height="280" rx="48" fill="{primary}" opacity="0.3"/>
  <text x="200" y="250" text-anchor="middle"
        font-family="system-ui,-apple-system,Arial"
        font-size="200" font-weight="800" fill="white"
        opacity="0.95">{initial}</text>
</svg>'''

    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def get_brand_colors(business_type: str) -> tuple:
    """Get recommended brand colors for a business type."""
    return BUSINESS_COLORS.get(business_type, ("#FF6B35", "#FFF0E6"))


async def generate_product_photo(item_name: str, business_type: str) -> str:
    """Generate a product/food photo for menu items."""
    if business_type in ("tiffin_delivery", "home_baker", "cloud_kitchen"):
        prompt = (
            f"Appetizing photo of {item_name}, Indian home-cooked style, "
            f"served in traditional steel thali or bowl, warm lighting, "
            f"top-down view, food photography"
        )
    else:
        prompt = f"Professional photo of {item_name} service, clean modern style"

    # Use Kie.ai for product photos too
    if KIE_API_KEY:
        try:
            url = await _generate_with_kie(prompt)
            if url:
                return url
        except Exception:
            pass

    encoded_name = urllib.parse.quote(item_name[:20])
    return f"https://placehold.co/400x300/FF6B35/white?text={encoded_name}"
