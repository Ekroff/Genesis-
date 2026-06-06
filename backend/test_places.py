"""Test Google Places API directly."""
import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, ".")

from services.places_client import find_nearby_businesses
from config import GOOGLE_PLACES_KEY


async def main():
    print(f"[CONFIG] Places API key: {'SET (' + GOOGLE_PLACES_KEY[:10] + '...)' if GOOGLE_PLACES_KEY else 'NOT SET'}")

    if not GOOGLE_PLACES_KEY:
        print("[SKIP] No API key")
        return

    results = await find_nearby_businesses(
        address="Sector 15, Noida, UP",
        business_type="tiffin_delivery",
        max_results=5,
    )
    print(f"\n[RESULT] Found {len(results)} businesses:")
    for r in results:
        print(f"  - {r['name']} | {r.get('phone', 'no phone')} | {r.get('rating', '?')} stars")
        print(f"    {r['address'][:60]}")


if __name__ == "__main__":
    asyncio.run(main())
