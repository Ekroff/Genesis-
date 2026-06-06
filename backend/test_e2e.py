"""End-to-end test: Launch the full GENESIS pipeline."""

import httpx
import asyncio
import json
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


async def main():
    payload = {
        "business_name": "Sharma Ji Tiffin Centre",
        "business_type": "tiffin_delivery",
        "phone": "9876543210",
        "address": "Sector 15, Noida, UP",
        "upi_id": "sharmaji@paytm",
        "language": "hi",
        "menu": [
            {"item": "Thali", "price": 80},
            {"item": "Paratha", "price": 40},
            {"item": "Chole Bhature", "price": 60},
        ],
    }

    # First test health
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("[HEALTH] Checking backend...")
        try:
            h = await client.get("http://localhost:8000/health")
            print(f"[HEALTH] {h.json()}")
        except Exception as e:
            print(f"[HEALTH] FAILED: {e}")
            return

        print("\n[LAUNCH] Sending request to /api/launch ...")
        try:
            resp = await client.post("http://localhost:8000/api/launch", json=payload)
            data = resp.json()
            print(f"\n[OK] Response ({resp.status_code}):")
            print(json.dumps(data, indent=2))
            print(f"\nSession ID: {data.get('session_id', 'N/A')}")
            print(f"Status: {data.get('status', 'N/A')}")
            print("\nPipeline is running in the background.")
            print("Watch the backend terminal for agent progress logs.")
        except httpx.ReadTimeout:
            print("[ERROR] Request timed out (30s). Supabase may be slow.")
            print("Check backend terminal for errors.")
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
