"""Test all free image generation options"""
import httpx
import time

# Option 1: Stability AI DreamStudio free trial
# Option 2: Craiyon (DALL-E mini) - free
# Option 3: HuggingFace Inference API - free tier
# Option 4: Together.ai - free credits

print("=== Testing Free Image APIs ===\n")

# Test 1: HuggingFace Inference API (free, no key for some models)
print("1. HuggingFace Inference API...")
try:
    r = httpx.post(
        "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
        json={"inputs": "professional logo icon for tiffin service, minimal, orange"},
        timeout=60,
    )
    print(f"   Status: {r.status_code}")
    if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
        with open("test_hf_logo.png", "wb") as f:
            f.write(r.content)
        print(f"   SUCCESS! Saved test_hf_logo.png ({len(r.content)} bytes)")
    elif r.status_code == 401:
        print("   Needs API key (free to get)")
    else:
        print(f"   Response: {r.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Together.ai free inference
print("\n2. Together.ai...")
try:
    r = httpx.post(
        "https://api.together.xyz/v1/images/generations",
        headers={"Content-Type": "application/json"},
        json={
            "model": "black-forest-labs/FLUX.1-schnell-Free",
            "prompt": "professional logo icon for tiffin service, minimal, orange, white background",
            "width": 512,
            "height": 512,
            "n": 1,
        },
        timeout=30,
    )
    print(f"   Status: {r.status_code}")
    if r.status_code == 401:
        print("   Needs API key (free tier available)")
    else:
        print(f"   Response: {r.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Stable Horde (completely free, community-powered)
print("\n3. Stable Horde (free, community GPU)...")
try:
    r = httpx.post(
        "https://stablehorde.net/api/v2/generate/async",
        headers={"Content-Type": "application/json", "apikey": "0000000000"},
        json={
            "prompt": "professional minimal flat logo icon for tiffin service, orange, white bg, no text",
            "params": {"width": 512, "height": 512, "steps": 20},
        },
        timeout=30,
    )
    print(f"   Status: {r.status_code}")
    if r.status_code in (200, 202):
        data = r.json()
        print(f"   Job submitted! ID: {data.get('id', 'N/A')}")
        print("   SUCCESS - Stable Horde works (free, just slower)")
    else:
        print(f"   Response: {r.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 4: SVG fallback (always works)
print("\n4. SVG Fallback (instant, always works)...")
import base64
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <rect width="400" height="400" fill="white"/>
  <rect x="50" y="50" width="300" height="300" rx="60" fill="#FF6B35"/>
  <text x="200" y="235" text-anchor="middle" font-family="Arial" font-size="180" font-weight="bold" fill="white">R</text>
</svg>'''
b64 = base64.b64encode(svg.encode()).decode()
data_uri = f"data:image/svg+xml;base64,{b64}"
print(f"   SVG data URI: {len(data_uri)} chars")
print("   SUCCESS - Always works")

print("\n=== Summary ===")
print("Recommended: HuggingFace (free key) > Stable Horde (free) > SVG fallback")
