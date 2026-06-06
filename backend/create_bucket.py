"""Create Supabase Storage bucket for GENESIS assets."""
import sys
sys.path.insert(0, ".")
from services.supabase_client import supabase

if not supabase:
    print("[ERROR] No Supabase connection")
    exit(1)

# Create bucket
try:
    result = supabase.storage.create_bucket(
        "genesis-assets",
        options={
            "public": True,
            "file_size_limit": 10485760,  # 10MB
            "allowed_mime_types": [
                "text/html",
                "image/png",
                "image/jpeg",
                "image/svg+xml",
                "application/pdf",
            ],
        },
    )
    print(f"[OK] Created bucket 'genesis-assets': {result}")
except Exception as e:
    if "already exists" in str(e).lower() or "Duplicate" in str(e):
        print("[OK] Bucket 'genesis-assets' already exists")
    else:
        print(f"[ERROR] {e}")
        # Try listing existing buckets
        try:
            buckets = supabase.storage.list_buckets()
            print(f"[INFO] Existing buckets: {[b.name for b in buckets]}")
        except Exception as e2:
            print(f"[ERROR] Cannot list buckets: {e2}")
