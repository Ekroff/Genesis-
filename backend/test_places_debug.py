"""Debug: Test both Places API endpoints to find which one works."""
import httpx
import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from config import GOOGLE_PLACES_KEY
API_KEY = GOOGLE_PLACES_KEY


async def main():
    async with httpx.AsyncClient(timeout=15.0) as client:

        # Test 1: Places API (New) - Text Search
        print("=== TEST 1: Places API (New) ===")
        try:
            resp = await client.post(
                "https://places.googleapis.com/v1/places:searchText",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": API_KEY,
                    "X-Goog-FieldMask": "places.displayName,places.formattedAddress",
                },
                json={"textQuery": "offices near Sector 15 Noida", "maxResultCount": 3},
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
        except Exception as e:
            print(f"Error: {e}")

        print()

        # Test 2: Legacy Places API - Nearby Search
        print("=== TEST 2: Legacy Places API (Nearby Search) ===")
        try:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={
                    "query": "offices near Sector 15 Noida",
                    "key": API_KEY,
                },
            )
            print(f"Status: {resp.status_code}")
            data = resp.json()
            print(f"API Status: {data.get('status')}")
            if data.get("results"):
                for r in data["results"][:3]:
                    print(f"  - {r['name']} | {r.get('formatted_address', '')[:50]}")
            elif data.get("error_message"):
                print(f"Error: {data['error_message']}")
        except Exception as e:
            print(f"Error: {e}")

        print()

        # Test 3: Simple Geocoding test (to verify key works at all)
        print("=== TEST 3: Geocoding API (key validity check) ===")
        try:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": "Sector 15 Noida", "key": API_KEY},
            )
            print(f"Status: {resp.status_code}")
            data = resp.json()
            print(f"API Status: {data.get('status')}")
            if data.get("error_message"):
                print(f"Error: {data['error_message']}")
            elif data.get("results"):
                print(f"Location: {data['results'][0].get('formatted_address', 'found')}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
