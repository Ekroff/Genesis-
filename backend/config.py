import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY", "")
TRUGEN_API_KEY = os.getenv("TRUGEN_API_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
KIE_API_KEY = os.getenv("KIE_API_KEY", "")
