"""Test the full /api/launch endpoint — end-to-end"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import httpx
import json

BASE = "http://localhost:8000"

# Simulate what TruGen would send after collecting data
payload = {
    "business_name": "Ramesh Tiffin Service",
    "business_type": "tiffin_delivery",
    "menu": [
        {"item": "Dal Chawal", "price": 80},
        {"item": "Rajma Chawal", "price": 90},
        {"item": "Paneer Thali", "price": 120},
        {"item": "Special Thali", "price": 150},
    ],
    "address": "Shop 12, Adarsh Colony, Bhopal MP 462001",
    "phone": "9876543210",
    "language": "hi",
    "upi_id": "ramesh@paytm",
}

print("=== Testing /api/launch ===")
print(f"Payload: {json.dumps(payload, indent=2)}")

r = httpx.post(f"{BASE}/api/launch", json=payload, timeout=30)
print(f"\nStatus: {r.status_code}")
print(f"Response: {r.text}")

if r.status_code == 200:
    data = r.json()
    session_id = data.get("session_id")
    print(f"\nSession ID: {session_id}")
    print("Agents are now running in background!")
    print(f"\nCheck dashboard: http://localhost:3000/dashboard?session={session_id}")
else:
    print(f"Error: {r.text[:500]}")
