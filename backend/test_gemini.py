"""Test Gemini text + confirm API works"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from google import genai
from config import GEMINI_API_KEY
c = genai.Client(api_key=GEMINI_API_KEY)

# Test 1: Hindi tagline
print("Test 1: Hindi tagline generation")
r = c.models.generate_content(
    model="gemini-2.5-flash",
    contents="Generate a catchy Hindi tagline for Ramesh Tiffin Service. Return ONLY the tagline."
)
print(f"  Result: {r.text.strip()}")

# Test 2: JSON generation (for brand identity)
print("\nTest 2: JSON brand identity")
r2 = c.models.generate_content(
    model="gemini-2.5-flash",
    contents="""Generate brand identity for "Ramesh Tiffin Service" (tiffin delivery).
Return ONLY valid JSON with these keys:
{
  "tagline_hindi": "...",
  "tagline_english": "...",
  "primary_color": "#hex",
  "secondary_color": "#hex",
  "font_recommendation": "Google Font name",
  "instagram_bio": "..."
}"""
)
print(f"  Result: {r2.text.strip()[:300]}")

print("\nAll tests passed! Gemini API is working.")
