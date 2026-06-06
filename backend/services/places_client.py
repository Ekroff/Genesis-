"""Google Places API service — finds nearby businesses for outreach.

Uses the Places API (New) with Text Search to find offices, companies,
and potential customers near the user's business location.
"""

import httpx
from config import GOOGLE_PLACES_KEY

PLACES_BASE = "https://places.googleapis.com/v1/places:searchText"


async def find_nearby_businesses(
    address: str,
    business_type: str,
    max_results: int = 15,
) -> list[dict]:
    """Find nearby offices and businesses that could be potential customers.
    
    For a tiffin service → find offices, IT parks, co-working spaces
    For a salon → find residential complexes, offices
    For a tutor → find schools, coaching centers, residential areas
    
    Returns list of: {name, address, phone, type, rating}
    """
    if not GOOGLE_PLACES_KEY:
        print("[Places] No API key configured")
        return []

    # Build search query based on business type
    search_queries = _get_search_queries(business_type)
    
    all_results = []
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for query in search_queries[:2]:  # Max 2 queries to save API calls
            full_query = f"{query} near {address}"
            
            try:
                resp = await client.post(
                    PLACES_BASE,
                    headers={
                        "Content-Type": "application/json",
                        "X-Goog-Api-Key": GOOGLE_PLACES_KEY,
                        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.types,places.rating,places.googleMapsUri",
                    },
                    json={
                        "textQuery": full_query,
                        "maxResultCount": max_results,
                        "languageCode": "en",
                    },
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    places = data.get("places", [])
                    
                    for place in places:
                        all_results.append({
                            "name": place.get("displayName", {}).get("text", "Unknown"),
                            "address": place.get("formattedAddress", ""),
                            "phone": place.get("nationalPhoneNumber", ""),
                            "types": place.get("types", [])[:3],
                            "rating": place.get("rating", 0),
                            "maps_url": place.get("googleMapsUri", ""),
                        })
                else:
                    print(f"[Places] API error {resp.status_code}: {resp.text[:200]}")
                    
            except Exception as e:
                print(f"[Places] Request failed: {e}")
    
    # Deduplicate by name
    seen = set()
    unique = []
    for r in all_results:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)
    
    return unique[:max_results]


def _get_search_queries(business_type: str) -> list[str]:
    """Get relevant search queries based on business type."""
    queries = {
        "tiffin_delivery": [
            "offices and IT companies",
            "co-working spaces and business parks",
        ],
        "home_baker": [
            "event venues and party halls",
            "offices and corporate parks",
        ],
        "cloud_kitchen": [
            "offices and tech parks",
            "residential societies and apartments",
        ],
        "tutor": [
            "schools and coaching centers",
            "residential societies",
        ],
        "salon": [
            "residential complexes and apartments",
            "shopping malls and markets",
        ],
        "tailor": [
            "wedding venues and event halls",
            "markets and shopping centers",
        ],
        "kirana": [
            "residential societies and apartments",
            "offices nearby",
        ],
    }
    return queries.get(business_type, [
        "offices and businesses",
        "residential areas and societies",
    ])
